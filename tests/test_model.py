from pathlib import Path
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from insider_risk.categorize import campaigns, categorize, suggest_routing  # noqa: E402
from insider_risk.controls import (  # noqa: E402
    best_portfolio, cheapest_within_appetite, efficient_frontier, evaluate_all_portfolios,
)
from insider_risk.data import (  # noqa: E402
    BUSINESS_UNITS, load_control_effects, load_controls, load_reports, load_scenarios,
)
from insider_risk.quantify import (  # noqa: E402
    Assumptions, apply_controls, build_inputs, exceedance_probability, expected_annual_loss,
    frequency_posterior, lognormal_from_interval, simulate, summarize, Z90,
)


@pytest.fixture(scope="module")
def model():
    scenarios = load_scenarios()
    cat = categorize(load_reports(), scenarios)
    return {"cat": cat, "scenarios": scenarios, "controls": load_controls(), "effects": load_control_effects()}


def test_intake_log_has_marie_reports(model):
    assert len(model["cat"]) == 10
    assert set(model["cat"].scenario_id) <= {"S1", "S2", "S3", "S4", "P0"}


def test_bribery_reports_are_one_campaign(model):
    cat = model["cat"].set_index("report_id")
    ids = ["IR-2026-0001", "IR-2026-0002", "IR-2026-0008"]
    assert cat.loc[ids, "campaign_id"].nunique() == 1
    camp = campaigns(model["cat"])
    assert camp.event_weight.max() == 1.0          # IR-0008 has a confirmed external party
    assert "P0" not in set(camp.scenario_id)        # precursors are not loss events


def test_posterior_equals_prior_without_data(model):
    empty = model["cat"].copy()
    empty["is_loss_event"] = False
    fp = frequency_posterior(empty, model["scenarios"], Assumptions(prior_weight_years=1.0))
    t = (empty.report_date.max() - empty.report_date.min()).days / 365.25
    assert fp.posterior_rate.sum() == pytest.approx(6.3 / (1 + t + 1 / 365.25), rel=1e-6)


def test_posterior_lies_between_prior_and_observed(model):
    fp = frequency_posterior(model["cat"], model["scenarios"], Assumptions())
    lo = np.minimum(fp.prior_rate, fp.observed_rate)
    hi = np.maximum(fp.prior_rate, fp.observed_rate)
    assert ((fp.posterior_rate >= lo - 1e-9) & (fp.posterior_rate <= hi + 1e-9)).all()


def test_business_units_partition_company_total(model):
    a = Assumptions()
    company = expected_annual_loss(build_inputs(model["cat"], model["scenarios"], a))
    units = sum(expected_annual_loss(build_inputs(model["cat"], model["scenarios"], a, "unit", u))
                for u in BUSINESS_UNITS)
    assert units == pytest.approx(company, rel=1e-9)


def test_lognormal_interval_round_trip():
    mu, sigma = lognormal_from_interval(1e5, 4e6)
    assert np.exp(mu - Z90 * sigma) == pytest.approx(1e5)
    assert np.exp(mu + Z90 * sigma) == pytest.approx(4e6)


def test_monte_carlo_mean_matches_closed_form(model):
    inputs = build_inputs(model["cat"], model["scenarios"], Assumptions())
    sim = simulate(inputs, 200_000, seed=7)
    assert sim.total.mean() == pytest.approx(expected_annual_loss(inputs), rel=0.08)
    assert np.all(sim.total >= 0)
    s = summarize(sim.total)
    assert s["median"] <= s["p90"] <= s["p95"] <= s["p99"] <= s["max"]


def test_controls_reduce_loss_and_stack_safely(model):
    inputs = build_inputs(model["cat"], model["scenarios"], Assumptions())
    base = expected_annual_loss(inputs)
    all_ids = list(model["controls"].control_id)
    everything = apply_controls(inputs, model["effects"], all_ids, effectiveness=5.0)
    assert 0 < expected_annual_loss(everything) < base
    assert (everything.freq_factor > 0).all() and (everything.slef >= 0).all()


def test_optimizer_and_tail_screen(model):
    inputs = build_inputs(model["cat"], model["scenarios"], Assumptions())
    p = evaluate_all_portfolios(inputs, model["controls"], model["effects"])
    assert len(p) == 2 ** len(model["controls"])
    assert p.residual_ale.iloc[0] == pytest.approx(expected_annual_loss(inputs))
    best = best_portfolio(p)
    assert best.net_benefit >= p.net_benefit.max() - 1e-6
    frontier = efficient_frontier(p)
    assert frontier.residual_ale.is_monotonic_decreasing
    pick = cheapest_within_appetite(p, 0.05)
    assert pick is not None and pick.p_exceed <= 0.05
    sim = simulate(apply_controls(inputs, model["effects"], best.controls), 100_000, seed=3)
    assert abs(exceedance_probability(sim.total, 100e6) - best.p_exceed) < 0.01


def test_routing_rules():
    assert suggest_routing("S3", "Employee", "Finance and treasury", "Company", "No") == \
        ["Insider risk team", "Security", "IT", "Legal", "Finance"]
    hr = suggest_routing("S2", "Employee", "Human resources", "Employee", "No")
    assert "HR" in hr and "Legal" in hr
    assert suggest_routing("P0", "Employee", "Sales and marketing", None, "No") == ["Insider risk team", "HR"]


@pytest.mark.parametrize("dept", ["Company-wide", "Response team · Legal", "Business unit · Engineering"])
def test_dashboard_runs_for_department(dept):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=180).run()
    at.sidebar.selectbox[0].select(dept).run()
    assert not at.exception, [e.value for e in at.exception]
    assert at.metric[0].label == "Expected loss / yr"

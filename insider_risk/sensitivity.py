"""One-at-a-time sensitivity (tornado) and recommendation-stability analysis."""
from __future__ import annotations

import pandas as pd

from .controls import best_portfolio, evaluate_all_portfolios
from .quantify import Assumptions, apply_controls, build_inputs, expected_annual_loss

# (label, field, low value, high value, why this range)
SENSITIVITY_RANGES = [
    ("Industry prior frequency", "prior_rate", 3.15, 13.8,
     "Half of Ponemon's 6.3 malicious incidents/yr up to Ponemon's 13.8 all-type incidents/yr (B14, B10)"),
    ("Weight on industry prior (years)", "prior_weight_years", 0.25, 4.0,
     "Trust internal reports more (0.25) or the benchmark more (4)"),
    ("Report credibility weights", "credibility_scale", 0.5, 1.5,
     "Halve or raise (capped at 1) the evidence-based credibility of each report"),
    ("Primary loss magnitude", "primary_multiplier", 0.5, 2.0,
     "Scales every primary-loss 90% interval"),
    ("Escalation probability (SLEF)", "slef_multiplier", 0.33, 2.67,
     "S1 escalation from 1% to 8%, other scenarios scaled the same way"),
    ("Secondary loss magnitude (SLM)", "slm_multiplier", 0.5, 1.5,
     "Scales the Coinbase 8-K $180M-$400M range and the other SLM intervals"),
    ("Control effectiveness", "control_effectiveness", 0.5, 1.25,
     "Controls deliver half, or 125%, of the assumed reductions"),
    ("Control cost", "cost_multiplier", 0.5, 1.5,
     "Vendor quotes come in at half or 150% of team estimates"),
]


def _metric(categorized, scenarios, controls, effects, a: Assumptions, selected, lens, name, metric):
    inputs = build_inputs(categorized, scenarios, a, lens, name)
    base = expected_annual_loss(inputs)
    if metric == "baseline":
        return base
    residual = expected_annual_loss(apply_controls(inputs, effects, selected, a.control_effectiveness))
    if metric == "residual":
        return residual
    cost = controls.loc[controls.control_id.isin(selected), "annual_cost"].sum() * a.cost_multiplier
    return base - residual - cost


def tornado(categorized, scenarios, controls, effects, a: Assumptions, selected: list[str],
            lens: str = "company", name: str | None = None, metric: str = "baseline") -> pd.DataFrame:
    """metric: 'baseline' (inherent ALE), 'residual' (ALE after controls) or 'net' (net benefit)."""
    center = _metric(categorized, scenarios, controls, effects, a, selected, lens, name, metric)
    rows = []
    for label, field, lo, hi, why in SENSITIVITY_RANGES:
        low = _metric(categorized, scenarios, controls, effects, a.with_(**{field: lo}), selected, lens, name, metric)
        high = _metric(categorized, scenarios, controls, effects, a.with_(**{field: hi}), selected, lens, name, metric)
        rows.append({"parameter": label, "low_input": lo, "high_input": hi, "at_low": low,
                     "at_high": high, "swing": abs(high - low), "center": center, "range_basis": why})
    return pd.DataFrame(rows).sort_values("swing", ascending=True)


def recommendation_stability(categorized, scenarios, controls, effects, a: Assumptions) -> pd.DataFrame:
    """Does the net-benefit-maximizing portfolio change at the ends of each range?"""
    def best(assume):
        inputs = build_inputs(categorized, scenarios, assume)
        p = evaluate_all_portfolios(inputs, controls, effects, assume.control_effectiveness,
                                    assume.cost_multiplier)
        return best_portfolio(p)

    reference = best(a)
    rows = [{"case": "Base assumptions", "best_portfolio": reference.portfolio,
             "net_benefit": reference.net_benefit, "same_as_base": True}]
    for label, field, lo, hi, _ in SENSITIVITY_RANGES:
        for tag, val in (("low", lo), ("high", hi)):
            b = best(a.with_(**{field: val}))
            rows.append({"case": f"{label} = {val:g} ({tag})", "best_portfolio": b.portfolio,
                         "net_benefit": b.net_benefit, "same_as_base": b.portfolio == reference.portfolio})
    return pd.DataFrame(rows)

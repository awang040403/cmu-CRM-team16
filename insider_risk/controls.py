"""Control evaluation: marginal value, return on security investment, and portfolio optimization."""
from __future__ import annotations

import itertools
from math import erfc

import numpy as np
import pandas as pd

from .quantify import apply_controls, expected_annual_loss, expected_loss_by_scenario

LEVERS = ["frequency", "primary", "slef", "slm"]


def _log_effect_tensor(inputs: pd.DataFrame, controls: pd.DataFrame, effects: pd.DataFrame,
                       effectiveness: float) -> np.ndarray:
    """log(1 - r) for every (control, scenario, lever)."""
    cids = list(controls.control_id)
    sids = list(inputs.scenario_id)
    t = np.zeros((len(cids), len(sids), len(LEVERS)))
    for _, e in effects.iterrows():
        if e.control_id not in cids or e.scenario_id not in sids:
            continue
        r = min(0.95, max(0.0, e.reduction * effectiveness))
        t[cids.index(e.control_id), sids.index(e.scenario_id), LEVERS.index(e.lever)] += np.log(1 - r)
    return t


def _normal_sf(z: np.ndarray) -> np.ndarray:
    return 0.5 * np.vectorize(erfc)(z / np.sqrt(2.0))


def evaluate_all_portfolios(inputs: pd.DataFrame, controls: pd.DataFrame, effects: pd.DataFrame,
                            effectiveness: float = 1.0, cost_multiplier: float = 1.0,
                            threshold: float = 100e6) -> pd.DataFrame:
    """Closed-form expected loss, cost and tail probability for every subset of controls (2^n).

    p_exceed approximates P(annual loss >= threshold) by the chance of at least one escalated
    event whose secondary loss alone exceeds the threshold. With lambda ~ Gamma(alpha, beta),
    P(no such event) = (beta / (beta + c))^alpha exactly (Gamma moment-generating function).
    """
    n = len(controls)
    masks = np.array(list(itertools.product([0, 1], repeat=n)), dtype=float)
    t = _log_effect_tensor(inputs, controls, effects, effectiveness)
    summed = np.einsum("mc,csl->msl", masks, t)

    base_rate = (inputs.alpha / inputs.beta * inputs.share * inputs.freq_factor).to_numpy()
    mu_p, sd_p = inputs.mu_p.to_numpy(), inputs.sigma_p.to_numpy()
    slef, mu_s, sd_s = inputs.slef.to_numpy(), inputs.mu_s.to_numpy(), inputs.sigma_s.to_numpy()

    rate = base_rate * np.exp(summed[:, :, 0])
    prim = np.exp(mu_p + summed[:, :, 1] + 0.5 * sd_p ** 2)
    sec = slef * np.exp(summed[:, :, 2]) * np.exp(mu_s + summed[:, :, 3] + 0.5 * sd_s ** 2)
    ale = (rate * (prim + sec)).sum(axis=1)

    alpha, beta = inputs.alpha.to_numpy(), inputs.beta.to_numpy()
    scale = (inputs.share * inputs.freq_factor).to_numpy() * np.exp(summed[:, :, 0])
    tail_sev = _normal_sf((np.log(threshold) - (mu_s + summed[:, :, 3])) / sd_s)
    c = scale * slef * np.exp(summed[:, :, 2]) * tail_sev
    p_exceed = 1.0 - np.prod((beta / (beta + c)) ** alpha, axis=1)

    costs = controls.annual_cost.to_numpy() * cost_multiplier
    cost = masks @ costs
    ids = np.array(controls.control_id)
    labels = [", ".join(ids[m.astype(bool)]) or "None (baseline)" for m in masks]
    df = pd.DataFrame({"portfolio": labels, "n_controls": masks.sum(axis=1).astype(int),
                       "annual_cost": cost, "residual_ale": ale, "p_exceed": p_exceed})
    base = float(ale[0])
    df["loss_avoided"] = base - df.residual_ale
    df["net_benefit"] = df.loss_avoided - df.annual_cost
    df["rosi"] = np.where(df.annual_cost > 0, df.net_benefit / df.annual_cost, np.nan)
    df["controls"] = [list(ids[m.astype(bool)]) for m in masks]
    return df


def efficient_frontier(portfolios: pd.DataFrame) -> pd.DataFrame:
    """Portfolios for which no cheaper portfolio has lower residual expected loss."""
    ordered = portfolios.sort_values(["annual_cost", "residual_ale"])
    best = np.inf
    keep = []
    for idx, row in ordered.iterrows():
        if row.residual_ale < best - 1e-6:
            keep.append(idx)
            best = row.residual_ale
    return ordered.loc[keep]


def best_portfolio(portfolios: pd.DataFrame, budget: float | None = None) -> pd.Series:
    pool = portfolios if budget is None else portfolios[portfolios.annual_cost <= budget]
    return pool.loc[pool.net_benefit.idxmax()]


def cheapest_within_appetite(portfolios: pd.DataFrame, max_probability: float) -> pd.Series | None:
    """Lowest-cost portfolio whose tail probability meets the board's risk appetite."""
    ok = portfolios[portfolios.p_exceed <= max_probability]
    if ok.empty:
        return None
    return ok.sort_values(["annual_cost", "residual_ale"]).iloc[0]


def control_value_table(inputs: pd.DataFrame, controls: pd.DataFrame, effects: pd.DataFrame,
                        selected: list[str], effectiveness: float = 1.0,
                        cost_multiplier: float = 1.0) -> pd.DataFrame:
    """Standalone and marginal (given the current selection) loss avoided for each control."""
    base = expected_annual_loss(inputs)
    current = expected_annual_loss(apply_controls(inputs, effects, selected, effectiveness))
    rows = []
    for _, c in controls.iterrows():
        alone = base - expected_annual_loss(apply_controls(inputs, effects, [c.control_id], effectiveness))
        if c.control_id in selected:
            others = [x for x in selected if x != c.control_id]
            marginal = expected_annual_loss(apply_controls(inputs, effects, others, effectiveness)) - current
        else:
            marginal = current - expected_annual_loss(
                apply_controls(inputs, effects, selected + [c.control_id], effectiveness))
        cost = c.annual_cost * cost_multiplier
        rows.append({
            "control_id": c.control_id,
            "control": c.control,
            "selected": c.control_id in selected,
            "annual_cost": cost,
            "standalone_loss_avoided": alone,
            "standalone_pct": alone / base if base else 0.0,
            "marginal_loss_avoided": marginal,
            "marginal_net_benefit": marginal - cost,
            "standalone_rosi": (alone - cost) / cost if cost else np.nan,
            "benchmark_pct": c.benchmark_pct,
        })
    return pd.DataFrame(rows)


def department_recommendations(inputs: pd.DataFrame, controls: pd.DataFrame, effects: pd.DataFrame,
                               effectiveness: float = 1.0, top: int = 3) -> pd.DataFrame:
    """Controls that remove the most expected loss from the selected department's view."""
    base = expected_annual_loss(inputs)
    rows = []
    for _, c in controls.iterrows():
        avoided = base - expected_annual_loss(apply_controls(inputs, effects, [c.control_id], effectiveness))
        rows.append({**c.to_dict(), "loss_avoided": avoided})
    return pd.DataFrame(rows).sort_values("loss_avoided", ascending=False).head(top)


def scenario_reduction(inputs: pd.DataFrame, effects: pd.DataFrame, selected: list[str],
                       effectiveness: float = 1.0) -> pd.DataFrame:
    before = expected_loss_by_scenario(inputs)[["scenario_id", "scenario", "expected_annual_loss"]]
    after = expected_loss_by_scenario(apply_controls(inputs, effects, selected, effectiveness))
    before = before.rename(columns={"expected_annual_loss": "inherent"})
    before["residual"] = after.expected_annual_loss.to_numpy()
    before["reduction_pct"] = np.where(before.inherent > 0, 1 - before.residual / before.inherent, 0.0)
    return before

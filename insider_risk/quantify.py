"""Part 3 - Quantify: FAIR loss-event frequency x loss magnitude, simulated with Monte Carlo.

Frequency (LEF, estimated directly as FAIR allows when TEF/vulnerability data are thin)
    lambda_s ~ Gamma(alpha0 * pi_s + k_s,  w + t)
      alpha0 = industry prior rate (Ponemon 2026: 6.3 malicious incidents/org/yr) x prior weight w
      pi_s   = prior share of scenario s (uniform)
      k_s    = credibility-weighted campaigns observed in the intake log
      t      = observation window in years
    Annual event count N_s ~ Poisson(lambda_s x department share x control factor)
    (Gamma-Poisson = negative binomial, so parameter uncertainty widens the tail.)

Magnitude (per event)
    Primary loss   ~ Lognormal fitted to a 90% interval
    Secondary loss ~ Bernoulli(SLEF) x Lognormal(SLM 90% interval)

Department views use Poisson thinning: a business unit's process is the company process
thinned by that unit's share, so business-unit views add up to the company-wide view.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
import pandas as pd

from .categorize import campaigns, observation_years
from .data import BUSINESS_UNITS, RESPONSE_TEAMS, split_multi

Z90 = 1.6448536269514722


@dataclass(frozen=True)
class Assumptions:
    prior_rate: float = 6.3            # B14, malicious insider incidents per org per year
    prior_weight_years: float = 1.0    # how many years of internal data the prior is "worth"
    smoothing: float = 0.5             # pseudo-count for department shares
    credibility_scale: float = 1.0     # scales report credibility weights (capped at 1)
    primary_multiplier: float = 1.0
    slef_multiplier: float = 1.0
    slm_multiplier: float = 1.0
    control_effectiveness: float = 1.0
    cost_multiplier: float = 1.0

    def with_(self, **kwargs) -> "Assumptions":
        return replace(self, **kwargs)


def lognormal_from_interval(lo: float, hi: float) -> tuple[float, float]:
    """(mu, sigma) of a lognormal whose 5th and 95th percentiles are lo and hi."""
    lo, hi = max(lo, 1.0), max(hi, 1.0)
    return (np.log(lo) + np.log(hi)) / 2.0, (np.log(hi) - np.log(lo)) / (2.0 * Z90)


def lognormal_mean(mu: float, sigma: float) -> float:
    return float(np.exp(mu + 0.5 * sigma ** 2))


# --------------------------------------------------------------------------- frequency

def frequency_posterior(categorized: pd.DataFrame, scenarios: pd.DataFrame,
                        a: Assumptions = Assumptions()) -> pd.DataFrame:
    camp = campaigns(categorized)
    camp["event_weight"] = (camp.event_weight * a.credibility_scale).clip(upper=1.0)
    t = observation_years(categorized)
    w = a.prior_weight_years
    n_scen = len(scenarios)
    rows = []
    for sid in scenarios.scenario_id:
        k = float(camp.loc[camp.scenario_id == sid, "event_weight"].sum())
        prior_alpha = a.prior_rate * w / n_scen
        post_alpha = prior_alpha + k
        post_beta = w + t
        draws = np.random.default_rng(0).gamma(post_alpha, 1 / post_beta, 20000)
        rows.append({
            "scenario_id": sid,
            "effective_events": k,
            "campaigns": int((camp.scenario_id == sid).sum()),
            "prior_rate": prior_alpha / w,
            "observed_rate": k / t,
            "post_alpha": post_alpha,
            "post_beta": post_beta,
            "posterior_rate": post_alpha / post_beta,
            "rate_p05": float(np.quantile(draws, 0.05)),
            "rate_p95": float(np.quantile(draws, 0.95)),
            "credibility_Z": t / (t + w),
        })
    return pd.DataFrame(rows)


def department_shares(categorized: pd.DataFrame, scenarios: pd.DataFrame, lens: str,
                      name: str | None, a: Assumptions = Assumptions()) -> pd.Series:
    """Share of each scenario's loss-event rate attributable to the selected department."""
    ids = list(scenarios.scenario_id)
    if lens == "company":
        return pd.Series(1.0, index=ids)
    loss = categorized[categorized.is_loss_event].copy()
    loss["w"] = (loss.credibility * a.credibility_scale).clip(upper=1.0)
    g = a.smoothing
    shares = {}
    if lens == "unit":
        d = len(BUSINESS_UNITS)
        for sid in ids:
            sub = loss[loss.scenario_id == sid]
            k_s = sub.w.sum()
            k_ds = sub.loc[sub.subject_team == name, "w"].sum()
            shares[sid] = (k_ds + g / d) / (k_s + g)
    else:
        routed = loss.route_to.apply(lambda v: name in split_multi(v))
        q = (loss.w * routed).sum() / loss.w.sum() if loss.w.sum() else 1 / len(RESPONSE_TEAMS)
        for sid in ids:
            m = loss.scenario_id == sid
            k_s = loss.loc[m, "w"].sum()
            k_ts = loss.loc[m & routed, "w"].sum()
            shares[sid] = (k_ts + g * q) / (k_s + g)
    return pd.Series(shares)


# --------------------------------------------------------------------------- model inputs

def build_inputs(categorized: pd.DataFrame, scenarios: pd.DataFrame, a: Assumptions,
                 lens: str = "company", name: str | None = None) -> pd.DataFrame:
    """One row per scenario holding every parameter the simulator needs (before controls)."""
    freq = frequency_posterior(categorized, scenarios, a).set_index("scenario_id")
    share = department_shares(categorized, scenarios, lens, name, a)
    rows = []
    for _, s in scenarios.iterrows():
        mu_p, sd_p = lognormal_from_interval(s.primary_lo * a.primary_multiplier,
                                             s.primary_hi * a.primary_multiplier)
        mu_s, sd_s = lognormal_from_interval(s.slm_lo * a.slm_multiplier, s.slm_hi * a.slm_multiplier)
        rows.append({
            "scenario_id": s.scenario_id,
            "scenario": s.scenario,
            "alpha": freq.loc[s.scenario_id, "post_alpha"],
            "beta": freq.loc[s.scenario_id, "post_beta"],
            "share": float(share[s.scenario_id]),
            "freq_factor": 1.0,
            "mu_p": mu_p, "sigma_p": sd_p,
            "slef": min(1.0, s.slef * a.slef_multiplier),
            "mu_s": mu_s, "sigma_s": sd_s,
        })
    return pd.DataFrame(rows)


def apply_controls(inputs: pd.DataFrame, effects: pd.DataFrame, selected: list[str],
                   effectiveness: float = 1.0) -> pd.DataFrame:
    """Controls stack multiplicatively per lever, so overlapping controls never exceed 100%."""
    out = inputs.copy()
    if not selected:
        return out
    eff = effects[effects.control_id.isin(selected)]
    for _, e in eff.iterrows():
        r = min(0.95, max(0.0, e.reduction * effectiveness))
        m = out.scenario_id == e.scenario_id
        if e.lever == "frequency":
            out.loc[m, "freq_factor"] *= (1 - r)
        elif e.lever == "primary":
            out.loc[m, "mu_p"] += np.log(1 - r)
        elif e.lever == "slef":
            out.loc[m, "slef"] *= (1 - r)
        elif e.lever == "slm":
            out.loc[m, "mu_s"] += np.log(1 - r)
    return out


# --------------------------------------------------------------------------- analytics

def expected_loss_by_scenario(inputs: pd.DataFrame) -> pd.DataFrame:
    """Closed-form expected annual loss: E[lambda] x (E[primary] + SLEF x E[SLM])."""
    out = inputs[["scenario_id", "scenario"]].copy()
    rate = inputs.alpha / inputs.beta * inputs.share * inputs.freq_factor
    prim = np.exp(inputs.mu_p + 0.5 * inputs.sigma_p ** 2)
    sec = inputs.slef * np.exp(inputs.mu_s + 0.5 * inputs.sigma_s ** 2)
    out["events_per_year"] = rate
    out["primary_per_event"] = prim
    out["secondary_per_event"] = sec
    out["loss_per_event"] = prim + sec
    out["expected_annual_loss"] = rate * (prim + sec)
    out["expected_primary"] = rate * prim
    out["expected_secondary"] = rate * sec
    return out


def expected_annual_loss(inputs: pd.DataFrame) -> float:
    return float(expected_loss_by_scenario(inputs).expected_annual_loss.sum())


# --------------------------------------------------------------------------- Monte Carlo

@dataclass
class SimulationResult:
    total: np.ndarray                 # (n,) annual loss
    by_scenario: pd.DataFrame         # (n, S) annual loss per scenario
    primary: np.ndarray               # (n,) primary component
    secondary: np.ndarray             # (n,) secondary component
    events: np.ndarray                # (n,) event count


def simulate(inputs: pd.DataFrame, n_trials: int = 10_000, seed: int = 14817) -> SimulationResult:
    if n_trials < 1000:
        raise ValueError("Use at least 1,000 trials.")
    rng = np.random.default_rng(seed)
    total_p = np.zeros(n_trials)
    total_s = np.zeros(n_trials)
    events = np.zeros(n_trials, dtype=int)
    per_scen = {}
    for _, r in inputs.iterrows():
        lam = rng.gamma(r.alpha, 1.0 / r.beta, n_trials) * r.share * r.freq_factor
        counts = rng.poisson(lam)
        n_ev = int(counts.sum())
        trial = np.repeat(np.arange(n_trials), counts)
        prim = rng.lognormal(r.mu_p, r.sigma_p, n_ev)
        escalate = rng.random(n_ev) < r.slef
        sec = np.where(escalate, rng.lognormal(r.mu_s, r.sigma_s, n_ev), 0.0)
        p = np.bincount(trial, weights=prim, minlength=n_trials)
        s = np.bincount(trial, weights=sec, minlength=n_trials)
        total_p += p
        total_s += s
        events += counts
        per_scen[r.scenario] = p + s
    return SimulationResult(total_p + total_s, pd.DataFrame(per_scen), total_p, total_s, events)


def summarize(losses: np.ndarray) -> dict:
    x = np.asarray(losses, dtype=float)
    p95 = float(np.quantile(x, 0.95))
    tail = x[x >= p95]
    return {
        "mean": float(x.mean()),
        "median": float(np.median(x)),
        "p10": float(np.quantile(x, 0.10)),
        "p90": float(np.quantile(x, 0.90)),
        "p95": p95,
        "p99": float(np.quantile(x, 0.99)),
        "tvar95": float(tail.mean()) if len(tail) else p95,
        "max": float(x.max()),
    }


def exceedance_probability(losses: np.ndarray, threshold: float) -> float:
    return float(np.mean(np.asarray(losses) >= threshold))


def exceedance_curve(losses: np.ndarray, n_points: int = 200) -> pd.DataFrame:
    x = np.asarray(losses)
    lo = max(np.quantile(x, 0.01), 1e4)
    hi = max(x.max(), lo * 10)
    grid = np.geomspace(lo, hi, n_points)
    xs = np.sort(x)
    prob = 1.0 - np.searchsorted(xs, grid, side="left") / len(xs)
    return pd.DataFrame({"loss": grid, "probability": prob})


def calibration_check(inputs: pd.DataFrame, benchmarks: pd.DataFrame) -> pd.DataFrame:
    """Compare model-implied quantities with the cited Ponemon / IBM benchmarks."""
    from .data import benchmark_value
    el = expected_loss_by_scenario(inputs)
    rate = el.events_per_year.sum()
    mean_primary = (el.expected_primary.sum() / rate) if rate else 0.0
    rows = [
        ("Malicious loss events per year", rate, benchmark_value(benchmarks, "B14"),
         "Ponemon 2026 malicious incidents/org (B14)",
         "Above benchmark because internal reports are updating the prior upward."),
        ("Mean primary loss per event", mean_primary, benchmark_value(benchmarks, "B11"),
         "Ponemon 2026 average incident cost, all types (B11)",
         "Malicious events at a crypto exchange should exceed the all-type average (negligent incidents are cheaper)."),
        ("Expected annual loss", el.expected_annual_loss.sum(), benchmark_value(benchmarks, "B01"),
         "Ponemon 2026 average annual insider cost, all types (B01)",
         "Gap is the secondary-loss tail: Coinbase actually lost $345M in 2025 (B19)."),
        ("Expected annual primary loss only", el.expected_primary.sum(), benchmark_value(benchmarks, "B12"),
         "IBM average annual malicious-insider cost (B12)",
         "Primary-only loss is the closest like-for-like comparison."),
    ]
    return pd.DataFrame(rows, columns=["quantity", "model", "benchmark", "benchmark_source", "interpretation"])

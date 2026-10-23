"""
Illustrative compound-Poisson / lognormal Monte Carlo model for the insider-threat project.

Important:
- The parameters in data/risk_register.csv are illustrative assumptions, not observed bank data.
- Frequency is the mean number of loss events per year (Poisson assumption).
- Severity is lognormal with the supplied median and log-space sigma.
- Control packages reduce frequency and severity according to scenario-specific assumptions.
- Validate distributions, dependencies, and calibration against credible evidence before using for real decisions.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

PACKAGE_COSTS = {
    "Baseline": 0.0,
    "Package A — Essential access controls": 1_200_000.0,
    "Package B — Enhanced monitoring & data protection": 3_800_000.0,
    "Package C — High-assurance privileged controls": 6_500_000.0,
}
PACKAGE_LETTERS = {
    "Baseline": None,
    "Package A — Essential access controls": "A",
    "Package B — Enhanced monitoring & data protection": "B",
    "Package C — High-assurance privileged controls": "C",
}
PACKAGE_DESCRIPTIONS = {
    "Baseline": "Existing environment; no incremental control investment modeled.",
    "Package A — Essential access controls": "Least privilege, MFA for sensitive access, periodic access reviews, timely offboarding, and separation of duties.",
    "Package B — Enhanced monitoring & data protection": "Package A plus DLP, UEBA, centralized logging, alert triage, and data-handling guardrails.",
    "Package C — High-assurance privileged controls": "Package B plus PAM, just-in-time privileged access, independent high-risk approvals, immutable logs, and tested response playbooks.",
}

def _package_column(letter: str | None, suffix: str) -> str | None:
    if letter is None:
        return None
    if suffix == "freq":
        return f"control_{letter}_frequency_reduction"
    return f"severity_reduction_{letter}"

def simulate_portfolio(
    risk_df: pd.DataFrame,
    package: str = "Baseline",
    n_trials: int = 50_000,
    seed: int = 20261021,
    frequency_multiplier: float = 1.0,
    severity_multiplier: float = 1.0,
    control_effectiveness_multiplier: float = 1.0,
) -> tuple[np.ndarray, pd.DataFrame]:
    """Return annual loss samples (excluding program cost) and scenario-level parameter summary."""
    if n_trials < 1000:
        raise ValueError("Use at least 1,000 trials for a stable classroom demonstration.")
    if package not in PACKAGE_LETTERS:
        raise ValueError(f"Unknown package: {package}")
    if min(frequency_multiplier, severity_multiplier, control_effectiveness_multiplier) < 0:
        raise ValueError("Multipliers must be non-negative.")
    rng = np.random.default_rng(seed)
    letter = PACKAGE_LETTERS[package]
    total_loss = np.zeros(n_trials, dtype=float)
    summary = []

    for _, row in risk_df.iterrows():
        base_rate = float(row["inherent_frequency_per_year"]) * frequency_multiplier
        base_median = float(row["median_loss_usd"]) * severity_multiplier
        if letter is None:
            freq_reduction = 0.0
            sev_reduction = 0.0
        else:
            freq_reduction = min(0.95, max(0.0, float(row[_package_column(letter, "freq")]) * control_effectiveness_multiplier))
            sev_reduction = min(0.95, max(0.0, float(row[_package_column(letter, "sev")]) * control_effectiveness_multiplier))
        residual_rate = base_rate * (1.0 - freq_reduction)
        residual_median = base_median * (1.0 - sev_reduction)
        counts = rng.poisson(residual_rate, size=n_trials)
        max_count = int(counts.max()) if len(counts) else 0
        scenario_loss = np.zeros(n_trials, dtype=float)
        if max_count > 0 and residual_median > 0:
            # Each event has an independent lognormal severity. The sum gives annual scenario loss.
            draws = rng.lognormal(
                mean=np.log(residual_median),
                sigma=float(row["log_sigma"]),
                size=(n_trials, max_count),
            )
            active = np.arange(max_count)[None, :] < counts[:, None]
            scenario_loss = (draws * active).sum(axis=1)
        total_loss += scenario_loss
        summary.append({
            "scenario_id": row["scenario_id"],
            "scenario": row["scenario"],
            "base_frequency": base_rate,
            "residual_frequency": residual_rate,
            "frequency_reduction_pct": 100.0 * freq_reduction,
            "base_median_severity_usd": base_median,
            "residual_median_severity_usd": residual_median,
            "severity_reduction_pct": 100.0 * sev_reduction,
            "simulated_mean_annual_loss_usd": float(scenario_loss.mean()),
        })
    return total_loss, pd.DataFrame(summary)

def summarize(losses: np.ndarray, program_cost: float = 0.0) -> dict:
    losses = np.asarray(losses, dtype=float)
    return {
        "mean_loss": float(np.mean(losses)),
        "median_loss": float(np.median(losses)),
        "p90_loss": float(np.quantile(losses, 0.90)),
        "p95_loss": float(np.quantile(losses, 0.95)),
        "p99_loss": float(np.quantile(losses, 0.99)),
        "prob_gt_1m": float(np.mean(losses > 1_000_000)),
        "prob_gt_5m": float(np.mean(losses > 5_000_000)),
        "prob_gt_10m": float(np.mean(losses > 10_000_000)),
        "program_cost": float(program_cost),
        "mean_total_cost": float(np.mean(losses) + program_cost),
    }

def compare_packages(risk_df: pd.DataFrame, n_trials: int = 50_000, seed: int = 20261021,
                     frequency_multiplier: float = 1.0, severity_multiplier: float = 1.0,
                     control_effectiveness_multiplier: float = 1.0) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    packages = list(PACKAGE_COSTS.keys())
    losses_by_package = {}
    rows = []
    for i, package in enumerate(packages):
        losses, _ = simulate_portfolio(
            risk_df, package, n_trials=n_trials, seed=seed + i,
            frequency_multiplier=frequency_multiplier,
            severity_multiplier=severity_multiplier,
            control_effectiveness_multiplier=control_effectiveness_multiplier,
        )
        losses_by_package[package] = losses
        stats = summarize(losses, PACKAGE_COSTS[package])
        rows.append({"package": package, **stats})
    df = pd.DataFrame(rows)
    baseline_mean = float(df.loc[df["package"] == "Baseline", "mean_loss"].iloc[0])
    df["mean_loss_avoided_vs_baseline"] = baseline_mean - df["mean_loss"]
    df["net_annual_benefit_proxy"] = df["mean_loss_avoided_vs_baseline"] - df["program_cost"]
    df["gross_loss_reduction_pct"] = np.where(baseline_mean > 0, 100 * df["mean_loss_avoided_vs_baseline"] / baseline_mean, 0.0)
    return df, losses_by_package

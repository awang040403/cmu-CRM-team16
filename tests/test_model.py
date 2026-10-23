from pathlib import Path
import sys
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from risk_model import simulate_portfolio, summarize, PACKAGE_COSTS

def test_simulation_shape_and_nonnegative():
    risks = pd.read_csv(ROOT / "data" / "risk_register.csv")
    losses, summary = simulate_portfolio(risks, "Baseline", n_trials=1000, seed=42)
    assert len(losses) == 1000
    assert np.all(losses >= 0)
    assert len(summary) == len(risks)

def test_control_package_reduces_assumed_frequency():
    risks = pd.read_csv(ROOT / "data" / "risk_register.csv")
    _, baseline = simulate_portfolio(risks, "Baseline", n_trials=1000, seed=42)
    _, package_c = simulate_portfolio(risks, list(PACKAGE_COSTS.keys())[3], n_trials=1000, seed=42)
    assert (package_c["residual_frequency"] <= baseline["residual_frequency"]).all()

def test_summary_percentiles_ordered():
    s = summarize(np.array([0, 1, 2, 3, 10], dtype=float))
    assert s["median_loss"] <= s["p90_loss"] <= s["p95_loss"] <= s["p99_loss"]

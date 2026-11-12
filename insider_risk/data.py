"""Loaders for the intake log, cited benchmarks, scenario parameters and control catalog."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data"

RESPONSE_TEAMS = ["Security", "IT", "Legal", "HR", "Finance", "Insider risk team"]
BUSINESS_UNITS = [
    "Customer support",
    "Engineering",
    "Finance and treasury",
    "Human resources",
    "Operations",
    "Sales and marketing",
    "Compliance and risk",
]
COMPANY_WIDE = "Company-wide"


def split_multi(value) -> list[str]:
    """Web-form multi-select answers are stored as '; '-separated strings."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    return [part.strip() for part in str(value).split(";") if part.strip()]


def load_reports(path: Path | None = None) -> pd.DataFrame:
    df = pd.read_csv(path or DATA / "insider_reports.csv")
    for col in ("report_date", "first_noticed"):
        df[col] = pd.to_datetime(df[col])
    return df


def load_benchmarks() -> pd.DataFrame:
    return pd.read_csv(DATA / "benchmarks.csv")


def benchmark_value(benchmarks: pd.DataFrame, benchmark_id: str) -> float:
    return float(benchmarks.loc[benchmarks.benchmark_id == benchmark_id, "value"].iloc[0])


def load_scenarios() -> pd.DataFrame:
    return pd.read_csv(DATA / "scenarios.csv")


def load_controls() -> pd.DataFrame:
    return pd.read_csv(DATA / "controls.csv")


def load_control_effects() -> pd.DataFrame:
    return pd.read_csv(DATA / "control_effects.csv")


def department_options() -> list[str]:
    """Labels for the single department drop-down: company, response teams, then business units."""
    return (
        [COMPANY_WIDE]
        + [f"Response team · {t}" for t in RESPONSE_TEAMS]
        + [f"Business unit · {u}" for u in BUSINESS_UNITS]
    )


def parse_department(label: str) -> tuple[str, str | None]:
    """Return (lens, name) where lens is 'company', 'team' or 'unit'."""
    if label == COMPANY_WIDE:
        return "company", None
    lens, name = label.split(" · ", 1)
    return ("team" if lens == "Response team" else "unit"), name

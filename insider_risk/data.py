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


# Synthetic workbook columns A–M only (no USD loss fields are loaded into the web app)
SYNTHETIC_AM_COLS = [
    "incident_id", "incident_date", "incident_type", "business_line", "insider_role",
    "work_arrangement", "records_exposed", "days_to_detect", "detection_method",
    "days_to_contain", "prior_warning_signs", "motivation", "primary_impact_category",
]


def load_reports(path: Path | None = None) -> pd.DataFrame:
    """Load the incident log that drives Part 2–4.

    Prefer the synthetic history (columns A–M only). Fall back to Marie's intake
    sample if the synthetic CSV has not been imported yet.
    """
    csv_path = path or DATA / "insider_reports.csv"
    df = pd.read_csv(csv_path)
    for col in ("report_date", "first_noticed"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    # Drop any USD / magnitude columns if a wider export was used by mistake
    usd = [c for c in df.columns if str(c).endswith("_usd") or str(c) == "total_loss_usd"]
    if usd:
        df = df.drop(columns=usd)
    return df


def load_synthetic_am(path: Path | None = None) -> pd.DataFrame:
    """Raw A–M synthetic fields for Methodology / transparency displays."""
    csv_path = path or DATA / "synthetic_incidents_am.csv"
    if not csv_path.exists():
        return pd.DataFrame(columns=SYNTHETIC_AM_COLS)
    df = pd.read_csv(csv_path)
    keep = [c for c in SYNTHETIC_AM_COLS if c in df.columns]
    return df[keep]


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

"""Convert Marie's raw research workbooks into the CSV files the model reads.

Usage:  python scripts/import_marie_data.py

Inputs  (data/raw/):
  insider_reports_sample.xlsx      - sample submissions from the "General" insider-report web form
  insider_threat_statistics.xlsx   - cited benchmark statistics + FAIR category mapping

Outputs (data/):
  insider_reports.csv              - one row per report, ISO dates, original form vocabulary
  benchmarks_raw.csv               - Marie's statistics sheet, unmodified apart from header cleanup
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data"


def import_reports() -> pd.DataFrame:
    # Row 1 of the sheet is a research note; the header is on row 2.
    df = pd.read_excel(RAW / "insider_reports_sample.xlsx", header=1)
    df = df.dropna(subset=["report_id"])
    for col in ("report_date", "first_noticed"):
        df[col] = pd.to_datetime(df[col]).dt.date
    df.to_csv(OUT / "insider_reports.csv", index=False)
    return df


def import_benchmarks() -> pd.DataFrame:
    df = pd.read_excel(RAW / "insider_threat_statistics.xlsx", sheet_name=0, header=1)
    df = df.dropna(how="all")
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df.to_csv(OUT / "benchmarks_raw.csv", index=False)
    return df


if __name__ == "__main__":
    reports = import_reports()
    stats = import_benchmarks()
    print(f"Wrote {len(reports)} reports and {len(stats)} benchmark statistics.")

"""Import Dheya's synthetic incident log into the dashboard's report schema.

Only columns A–M from synthetic_insider_incidents.xlsx are used (no USD loss columns):
  A incident_id
  B incident_date
  C incident_type
  D business_line
  E insider_role
  F work_arrangement
  G records_exposed
  H days_to_detect
  I detection_method
  J days_to_contain
  K prior_warning_signs
  L motivation
  M primary_impact_category

Usage:  python scripts/import_synthetic.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
SRC = PROJECT / "synthetic_insider_incidents.xlsx"
RAW_OUT = ROOT / "data" / "raw" / "synthetic_insider_incidents.xlsx"
CSV_OUT = ROOT / "data" / "insider_reports.csv"
SYNTH_CSV = ROOT / "data" / "synthetic_incidents_am.csv"

# Columns A–M only (exclude regulatory_usd … total_loss_usd)
COLS_A_TO_M = [
    "incident_id",
    "incident_date",
    "incident_type",
    "business_line",
    "insider_role",
    "work_arrangement",
    "records_exposed",
    "days_to_detect",
    "days_to_contain",
    "detection_method",
    "prior_warning_signs",
    "motivation",
    "primary_impact_category",
]

# Coinbase dashboard business units ← synthetic banking lines
BUSINESS_LINE_TO_UNIT = {
    "Retail Banking": "Customer support",
    "Commercial Banking": "Sales and marketing",
    "Payments": "Operations",
    "Wealth Management": "Finance and treasury",
    "Capital Markets": "Engineering",
}

ROLE_TO_SUBJECT = {
    "Vendor/Contractor Staff": "Outsourced vendor staff (BPO, call center)",
    "Customer Support": "Employee",
    "Operations": "Employee",
    "IT/Admin": "Employee",
    "Branch/Teller": "Employee",
}

ROLE_TO_TEAM_OVERRIDE = {
    "Customer Support": "Customer support",
    "Operations": "Operations",
    "IT/Admin": "Engineering",
    "Branch/Teller": "Customer support",
    "Vendor/Contractor Staff": None,  # keep business-line unit
}

WORK_TO_LOCATION = {
    "Remote": "Remote",
    "On-site": "Company office",
    "Hybrid": "Hybrid / mixed",
}

DETECTION_TO_EVIDENCE = {
    "Monitoring alert": "Ticket or system log",
    "Audit/review": "Ticket or system log",
    "Whistleblower report": "Email or chat message",
    "Customer complaint": "Another witness",
    "External tip/extortion demand": "Another witness",
}

IMPACT_TO_FORM = {
    "Customer": "Customer notification; Scam reimbursement; Reputation",
    "Response": "Response and investigation",
    "Regulatory": "Regulatory and legal",
    "Forensic": "Response and investigation",
    "Media": "Reputation",
    "Cost of Capital": "Financial reporting (SOX)",
}


def map_scenario(row: pd.Series) -> str:
    """Map A–M fields onto the four modeled FAIR loss scenarios (+ precursors unused here)."""
    itype = str(row.incident_type)
    role = str(row.insider_role)
    motiv = str(row.motivation)
    impact = str(row.primary_impact_category)

    if itype == "Third-Party" or role == "Vendor/Contractor Staff":
        return "Bribed or colluding data exfiltration"
    if itype == "Employee Device/ID Theft":
        return "Credential or access sharing"
    if role == "IT/Admin" or (itype == "Internal Employee" and motiv == "Sensitive personal information"):
        return "Privileged access abuse"
    if motiv == "Business disruption" or impact in ("Cost of Capital", "Forensic"):
        if itype == "Internal Employee":
            return "Fraud or record manipulation"
    if itype == "Compromised Employee":
        if motiv in ("Ransom", "Sensitive personal information"):
            return "Bribed or colluding data exfiltration"
        return "Credential or access sharing"
    if itype == "Internal Employee":
        if motiv in ("Grudge", "Hacktivism", "Terrorism"):
            return "Fraud or record manipulation"
        return "Privileged access abuse"
    return "Bribed or colluding data exfiltration"


def records_bucket(n: int) -> str:
    if n < 100:
        return "10 to 100"
    if n < 1000:
        return "100 to 1,000"
    return "Over 1,000"


def subject_access(role: str) -> str:
    if role == "IT/Admin":
        return "Admin or privileged system access"
    if role in ("Customer Support", "Branch/Teller", "Vendor/Contractor Staff"):
        return "Customer records and support tools"
    return "Standard tools only"


def route_for(scenario: str, subject_type: str, unit: str, impact: str) -> str:
    teams = ["Insider risk team", "Security", "IT"]
    if "Regulatory" in impact or scenario.startswith("Bribed") or "Customer" in impact:
        teams.append("Legal")
    if subject_type.startswith("Employee") and unit == "Human resources":
        teams.append("HR")
    if scenario.startswith("Fraud") or unit == "Finance and treasury":
        teams.append("Finance")
    if "Vendor" in subject_type or "Outsourced" in subject_type:
        teams.append("Legal")
    return "; ".join(dict.fromkeys(teams))


def convert(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in df.iterrows():
        unit = BUSINESS_LINE_TO_UNIT.get(str(r.business_line), "Operations")
        role = str(r.insider_role)
        override = ROLE_TO_TEAM_OVERRIDE.get(role)
        if override:
            unit = override
        subject_type = ROLE_TO_SUBJECT.get(role, "Employee")
        scenario = map_scenario(r)
        impact = IMPACT_TO_FORM.get(str(r.primary_impact_category), "Response and investigation")
        evidence = DETECTION_TO_EVIDENCE.get(str(r.detection_method), "Nothing yet")
        days_detect = int(r.days_to_detect)
        incident_date = pd.to_datetime(r.incident_date)
        first_noticed = incident_date - pd.Timedelta(days=days_detect)
        records = int(r.records_exposed)
        external = "Confirmed" if str(r.detection_method) == "External tip/extortion demand" else (
            "Suspected" if str(r.incident_type) == "Third-Party" else "No"
        )
        urgency = (
            "Data or money is leaving now" if days_detect == 0
            else ("Needs review this week" if days_detect <= 14 else "Not urgent")
        )
        rows.append({
            "report_id": str(r.incident_id),
            "report_date": incident_date.date(),
            "form": "synthetic-history",
            "reporter_team": "",
            "reporter_relationship": "Synthetic historical record",
            "anonymous": "No",
            "subject_type": subject_type,
            "subject_team": unit,
            "subject_access": subject_access(role),
            "subject_location": WORK_TO_LOCATION.get(str(r.work_arrangement), "Company office"),
            "activities": _activities(scenario, role),
            "data_owner": "Customer" if str(r.primary_impact_category) == "Customer" else "Company",
            "customer_data": "Names and contact details; Balances or transaction history" if records else "",
            "employee_data": "",
            "company_data": "",
            "records_affected": records_bucket(records),
            "records_exposed": records,
            "exfil_method": "Unknown / synthetic",
            "external_party_involved": external,
            "first_noticed": first_noticed.date(),
            "frequency": "Once",
            "still_happening": "No",
            "found_out_by": str(r.detection_method),
            "evidence": evidence,
            "urgency": urgency,
            "note": (
                f"Synthetic · {r.incident_type} · {r.business_line} · {role} · "
                f"motivation={r.motivation} · impact={r.primary_impact_category} · "
                f"detect={days_detect}d contain={int(r.days_to_contain)}d · "
                f"warnings={int(r.prior_warning_signs)}"
            ),
            "scenario_name": scenario,
            "impact_categories": impact,
            "route_to": route_for(scenario, subject_type, unit, impact),
            # Keep A–M originals for Methodology / transparency tabs
            "incident_type": str(r.incident_type),
            "business_line": str(r.business_line),
            "insider_role": role,
            "work_arrangement": str(r.work_arrangement),
            "days_to_detect": days_detect,
            "days_to_contain": int(r.days_to_contain),
            "detection_method": str(r.detection_method),
            "prior_warning_signs": int(r.prior_warning_signs),
            "motivation": str(r.motivation),
            "primary_impact_category": str(r.primary_impact_category),
        })
    return pd.DataFrame(rows)


def _activities(scenario: str, role: str) -> str:
    if scenario.startswith("Bribed"):
        return "Viewed or searched data they don't need for their job; Copied, photographed, downloaded or sent data out"
    if scenario.startswith("Privileged"):
        return "Asked for or used access beyond their role; Viewed or searched data they don't need for their job"
    if scenario.startswith("Fraud"):
        return "Moved funds or changed wallet, withdrawal or limit settings; Changed, deleted or falsified data or records"
    if scenario.startswith("Credential"):
        return "Shared, borrowed or asked for someone's login"
    return "Tried to get around a security control"


def main() -> None:
    raw = pd.read_excel(SRC)
    # Enforce A–M only regardless of sheet extras
    keep = [c for c in COLS_A_TO_M if c in raw.columns]
    # detection_method may appear after days_to_contain in source; reorder to A–M logical set
    am = raw[[
        "incident_id", "incident_date", "incident_type", "business_line", "insider_role",
        "work_arrangement", "records_exposed", "days_to_detect", "detection_method",
        "days_to_contain", "prior_warning_signs", "motivation", "primary_impact_category",
    ]].copy()
    assert list(am.columns) == [
        "incident_id", "incident_date", "incident_type", "business_line", "insider_role",
        "work_arrangement", "records_exposed", "days_to_detect", "detection_method",
        "days_to_contain", "prior_warning_signs", "motivation", "primary_impact_category",
    ]
    # Reject any USD columns leaking in
    usd_cols = [c for c in raw.columns if c.endswith("_usd")]
    assert not any(c in am.columns for c in usd_cols)

    RAW_OUT.parent.mkdir(parents=True, exist_ok=True)
    am.to_excel(RAW_OUT, index=False, sheet_name="synthetic_insider_incidents")
    am.to_csv(SYNTH_CSV, index=False)

    reports = convert(am)
    reports.to_csv(CSV_OUT, index=False)
    print(f"Wrote A–M only ({len(am.columns)} cols, {len(am)} rows) → {RAW_OUT.name}, {SYNTH_CSV.name}")
    print(f"Wrote {len(reports)} mapped reports → {CSV_OUT.name}")
    print("Scenario mix:")
    print(reports.scenario_name.value_counts().to_string())
    print("Business-unit mix:")
    print(reports.subject_team.value_counts().to_string())


if __name__ == "__main__":
    main()

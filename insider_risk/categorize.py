"""Part 2 - Categorize: turn raw web-form reports into model-ready loss events.

Each report receives the four labels from the team's design (adapted from Pollmeier et al., 2023):
  A. Incident type      - which modeled loss scenario the report belongs to
  B. Impact qualifier   - security property hit (CIA) and a severity tier
  C. Impact category    - FAIR forms of loss, split into primary vs secondary
  D. Quant metrics      - credibility weight, records exposed, detection lag

Related reports are then linked into campaigns so one bribery ring reported three times
counts as one loss event in the frequency estimate, not three.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data import split_multi

PRECURSOR_ID = "P0"
PRECURSOR_NAME = "Precursor signals only (no loss event yet)"

# Probability that a report reflects a genuine malicious event, by strongest evidence attached.
# Analyst-set weights; documented in docs/part3_quantification.md and tested in sensitivity.
EVIDENCE_WEIGHT = {
    "Ticket or system log": 0.9,
    "Screenshot or photo": 0.8,
    "Another witness": 0.7,
    "Email or chat message": 0.6,
    "Nothing yet": 0.3,
}
CONFIRMED_EXTERNAL_WEIGHT = 1.0

ACTIVITY_CIA = {
    "Viewed or searched data they don't need for their job": "Confidentiality",
    "Copied, photographed, downloaded or sent data out": "Confidentiality",
    "Mentioned an offer of money or favors for data or access": "Confidentiality",
    "Asked for or used access beyond their role": "Confidentiality",
    "Shared, borrowed or asked for someone's login": "Integrity",
    "Tried to get around a security control": "Integrity",
    "Moved funds or changed wallet, withdrawal or limit settings": "Integrity",
    "Changed, deleted or falsified data or records": "Integrity",
    "Threatened the company or coworkers": "Availability",
}

URGENCY_TIER = {
    "Data or money is leaving now": "Critical",
    "Someone may be hurt": "Critical",
    "Needs review this week": "High",
    "Not urgent": "Low",
}

# Web-form impact category -> (FAIR loss type, FAIR form of loss)
IMPACT_TO_FAIR = {
    "Response and investigation": ("Primary", "Response"),
    "Direct fund loss": ("Primary", "Replacement"),
    "Customer notification": ("Secondary", "Response"),
    "Employee notification": ("Secondary", "Response"),
    "Regulatory and legal": ("Secondary", "Fines & judgments"),
    "Privacy and legal": ("Secondary", "Fines & judgments"),
    "Financial reporting (SOX)": ("Secondary", "Fines & judgments"),
    "Scam reimbursement": ("Secondary", "Fines & judgments"),
    "Reputation": ("Secondary", "Reputation"),
    "IP and competitive loss": ("Secondary", "Competitive advantage"),
}

# Geometric midpoints of the form's record-count buckets; "Over 1,000" uses an analyst assumption.
RECORDS_ESTIMATE = {"10 to 100": 32, "100 to 1,000": 316, "Over 1,000": 3000}


def credibility(evidence, external_party) -> float:
    if str(external_party).strip() == "Confirmed":
        return CONFIRMED_EXTERNAL_WEIGHT
    weights = [EVIDENCE_WEIGHT.get(item, 0.5) for item in split_multi(evidence)]
    return max(weights) if weights else 0.3


def _fair_forms(impacts) -> tuple[str, str]:
    primary, secondary = [], []
    for item in split_multi(impacts):
        kind, form = IMPACT_TO_FAIR.get(item, ("Secondary", "Other"))
        (primary if kind == "Primary" else secondary).append(form)
    dedupe = lambda xs: "; ".join(dict.fromkeys(xs))
    return dedupe(primary), dedupe(secondary)


def categorize(reports: pd.DataFrame, scenarios: pd.DataFrame) -> pd.DataFrame:
    name_to_id = dict(zip(scenarios.form_scenario_name, scenarios.scenario_id))
    name_to_intent = dict(zip(scenarios.form_scenario_name, scenarios.intent))
    out = reports.copy()
    out["scenario_id"] = out.scenario_name.map(name_to_id).fillna(PRECURSOR_ID)
    out["intent"] = out.scenario_name.map(name_to_intent).fillna("Precursor")
    out["is_loss_event"] = out.scenario_id != PRECURSOR_ID

    cia = []
    for acts in out.activities:
        props = [ACTIVITY_CIA.get(a, "Integrity") for a in split_multi(acts)]
        cia.append("; ".join(dict.fromkeys(props)) or "Unspecified")
    out["cia"] = cia
    out["severity_tier"] = out.urgency.map(URGENCY_TIER).fillna("High")

    forms = out.impact_categories.apply(_fair_forms)
    out["primary_loss_forms"] = [f[0] for f in forms]
    out["secondary_loss_forms"] = [f[1] for f in forms]

    out["credibility"] = [credibility(e, x) for e, x in zip(out.evidence, out.external_party_involved)]
    out["records_est"] = out.records_affected.map(RECORDS_ESTIMATE).fillna(0).astype(int)
    out["detection_lag_days"] = (out.report_date - out.first_noticed).dt.days
    return link_campaigns(out)


def link_campaigns(df: pd.DataFrame, window_days: int = 90) -> pd.DataFrame:
    """Reports with the same scenario, business unit and insider type within `window_days`
    of each other are treated as one campaign (one FAIR loss event)."""
    df = df.sort_values("report_date").copy()
    campaign = pd.Series(index=df.index, dtype=object)
    counter = 0
    for _, grp in df.groupby(["scenario_id", "subject_team", "subject_type"], dropna=False, sort=False):
        last_date = None
        for idx, row in grp.iterrows():
            if last_date is None or (row.report_date - last_date).days > window_days:
                counter += 1
            campaign[idx] = f"CMP-{counter:02d}"
            last_date = row.report_date
    df["campaign_id"] = campaign
    df["campaign_size"] = df.groupby("campaign_id").report_id.transform("count")
    return df.sort_values("report_id")


def campaigns(categorized: pd.DataFrame) -> pd.DataFrame:
    """One row per campaign: the unit counted as a loss event in the frequency model."""
    loss = categorized[categorized.is_loss_event]
    return (
        loss.groupby("campaign_id")
        .agg(
            scenario_id=("scenario_id", "first"),
            subject_team=("subject_team", "first"),
            reports=("report_id", lambda s: ", ".join(s)),
            n_reports=("report_id", "count"),
            first_report=("report_date", "min"),
            last_report=("report_date", "max"),
            event_weight=("credibility", "max"),
        )
        .reset_index()
    )


def suggest_routing(scenario_id: str, subject_type: str, subject_team: str,
                    data_owner: str | None, external_party: str) -> list[str]:
    """Rule-based routing so a new report reaches the right response teams automatically."""
    teams = ["Insider risk team"]
    if scenario_id != PRECURSOR_ID:
        teams += ["Security", "IT"]
    if data_owner in ("Customer", "Employee") or external_party in ("Suspected", "Confirmed") \
            or scenario_id in ("S1", "S3"):
        teams.append("Legal")
    if subject_type == "Employee" and (subject_team == "Human resources" or scenario_id == PRECURSOR_ID):
        teams.append("HR")
    if data_owner == "Employee":
        teams.append("HR")
    if scenario_id == "S3" or subject_team == "Finance and treasury":
        teams.append("Finance")
    return list(dict.fromkeys(teams))


def observation_years(categorized: pd.DataFrame) -> float:
    span = (categorized.report_date.max() - categorized.report_date.min()).days + 1
    return max(span, 1) / 365.25


def leading_indicators(categorized: pd.DataFrame) -> dict:
    loss = categorized[categorized.is_loss_event]
    return {
        "precursors": int((~categorized.is_loss_event).sum()),
        "anonymous_share": float((categorized.anonymous == "Yes").mean()),
        "vendor_share": float(categorized.subject_type.str.contains("vendor", case=False, na=False).mean()),
        "median_detection_lag": float(np.median(loss.detection_lag_days)) if len(loss) else float("nan"),
        "ongoing": int((categorized.still_happening == "Yes").sum()),
    }

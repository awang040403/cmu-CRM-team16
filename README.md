# Insider Risk Lab — CMU 14-817 Scenario 2

An interactive Streamlit prototype plus reproducible Python Monte Carlo model for the group project scenario: insider threats at a multinational financial institution.

## Important integrity note
All numeric starting values in `data/risk_register.csv` are illustrative assumptions. They are not actual bank data, empirically measured incident rates, or sourced loss estimates. Clearly label them in the presentation and report. Replace them with credible, cited evidence or a documented expert-elicitation process where available.

## Run locally
Python 3.10+ recommended.

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
streamlit run app.py
```

Streamlit will print a local URL, usually `http://localhost:8501`.

## Project contents
- `app.py`: interactive dashboard with six tabs, sensitivity sliders, Monte Carlo distribution, exceedance curve, control package comparison, risk register, framework mapping, and roadmap.
- `risk_model.py`: reproducible compound-Poisson / lognormal simulation and portfolio comparison.
- `data/risk_register.csv`: five distinct insider-risk scenarios and transparent model assumptions.
- `report_draft.md`: report narrative draft and methodological explanation.
- `presentation_outline.md`: 16-slide presentation outline and speaker allocation suggestions.
- `model_card.md`: model purpose, assumptions, limitations, and validation checklist.
- `tests/test_model.py`: basic model sanity tests.

## Model structure
For each scenario, annual event count is modeled as Poisson with mean lambda. Each event's loss severity is modeled as lognormal, parameterized by a median and log-space sigma. Annual scenario losses are summed across events and scenarios. The control packages reduce assumed event frequency and median severity by scenario-specific percentages. Program costs are compared with modeled mean loss avoided in a simplified annual proxy.

This is not a complete FAIR implementation by itself. It is a classroom Monte Carlo structure that should be aligned with the exact FAIR Standard v3.0 terms and decomposition used in the course. Do not label the Poisson/lognormal assumptions as required by FAIR; they are modeling choices that need justification and sensitivity analysis.

## Before submission
1. Compare against the actual assignment rubric and project guidance.
2. Confirm all frameworks used were covered in class or cite them as supplementary.
3. Add citations to course lecture slides, FAIR Standard v3.0, NIST SP 800-37 Rev. 2, OWASP threat modeling guidance, and any MITRE ATT&CK technique pages you actually use.
4. Add evidence for parameter choices; otherwise label as expert-elicited or illustrative assumptions.
5. Have a teammate independently inspect the code, calculations, and chart interpretations.
6. Export the final app screenshots or provide a reliable hosted URL if your instructor permits it.

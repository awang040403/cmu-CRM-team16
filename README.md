# Centralized Insider-Threat Reporting and Quantification: Coinbase

CMU 14-817 Cyber Risk Modeling · Team 16 (Dheya Reddy Doddipalli, Marie McCauley, Amy Wang) · Scenario 2

A working implementation of the four-step pipeline from our Milestone 1 deck:

```
1. Report       ->  2. Categorize        ->  3. Quantify              ->  4. Dashboard
dept web forms      malicious + A/B/C/D      FAIR + 10,000-run MC         dept & company views,
(Marie's sample)    + campaign linking       Bayesian frequency           costs, controls, NIST + regulation
```

## Run it

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py               # opens http://localhost:8501
```

Other commands:

```bash
python scripts/import_marie_data.py   # rebuild data/insider_reports.csv from Marie's raw workbooks
python scripts/export_results.py      # regenerate results/summary.md and CSVs quoted in the report
pytest -q                             # 13 tests: model math, partitions, optimizer, and the dashboard itself
```

## Headline results (base case, 10,000 trials, seed 14817)

| | Inherent | With recommended controls |
|---|---|---|
| Expected annual loss | $40.3M | $8.2M |
| 1-in-20 year (P95) | $249M | $25M |
| P(annual loss ≥ $100M) | 8.1% | 2.3% |

- Recommended portfolio: C1, C2, C4, C5, C6, C8, C9. It costs $7.6M/yr, has a net benefit of $25.0M/yr, and a return on security investment of 329%.
- Bribed BPO exfiltration is 57% of expected loss and 92% of the worst-5% years; Customer support carries $22.6M.
- No mitigation mix gets the chance of a $100M+ year below about 2%. Meeting a 1% appetite needs risk transfer (insurance).
- Back-test: conditional on escalation, Coinbase's actual FY2025 loss ($345.2M) sits at the 85th percentile of the modeled range.

## Repository map

| Path | What it is |
|---|---|
| `app.py` | Part 4: Streamlit dashboard with the department drop-down and six tabs |
| `insider_risk/categorize.py` | Part 2: ABCD labels, credibility weights, campaign linking, auto-routing |
| `insider_risk/quantify.py` | Part 3: Gamma-Poisson frequency, lognormal primary/secondary loss, Monte Carlo, calibration |
| `insider_risk/controls.py` | Control effects, 1,024-portfolio optimizer, efficient frontier, risk-appetite screen |
| `insider_risk/sensitivity.py` | Tornado and recommendation-stability analysis |
| `data/raw/` | Marie's original workbooks (intake sample and cited statistics) |
| `data/insider_reports.csv` | Intake log converted from Marie's sample |
| `data/benchmarks.csv` | Cited statistics with IDs B01–B22 and how each is used |
| `data/scenarios.csv` | Loss-magnitude 90% intervals, SLEF, SLM, and the basis for each |
| `data/controls.csv`, `data/control_effects.csv` | Control catalog (NIST 800-53, CSF 2.0, regulation, cost) and per-scenario effects |
| `docs/part3_quantification.md` | Part 3 write-up for the report |
| `docs/part4_dashboard_design.md` | Part 4 write-up and live-demo script |
| `results/` | Reproducible outputs quoted in the report and slides |
| `model_card.md` | Intended use, assumptions, limitations, validation status |

## Integrity note

Frequencies blend a cited industry benchmark (Ponemon/DTEX 2026) with ten sample reports. Loss ranges are anchored on Ponemon and on Coinbase's SEC filings. Escalation probabilities, report credibility weights, control effects and control costs are team estimates. They are labeled as such in `data/*.csv` and in the app, and they are stress-tested on the Sensitivity tab. This is a proof of concept, not a validated actuarial model.

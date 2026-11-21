# Centralized Insider-Threat Reporting and Quantification: Coinbase

CMU 14-817 Cyber Risk Modeling · Team 16 (Dheya Reddy Doddipalli, Marie McCauley, Amy Wang) · Scenario 2

A working implementation of the four-step pipeline from our Milestone 1 deck:

```
1. Report              ->  2. Categorize        ->  3. Quantify              ->  4. Dashboard
synthetic history          malicious + A/B/C/D      FAIR + 10,000-run MC         dept & company views,
(columns A–M only)         + campaign linking       Bayesian frequency           costs, controls, NIST + regulation
```

## Run it

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/import_synthetic.py # load A–M only from ../synthetic_insider_incidents.xlsx
streamlit run app.py               # opens http://localhost:8501
```

Other commands:

```bash
python scripts/export_results.py      # regenerate results/summary.md and CSVs quoted in the report
pytest -q                             # model math, partitions, optimizer, A–M-only loading
python scripts/capture_screenshots.py # after streamlit is running
python scripts/build_guide_docx.py
python scripts/build_amy_writeup_and_demo.py
```

## Data policy (important)

The website uses **only columns A–M** from `synthetic_insider_incidents.xlsx`
(incident attributes). USD loss columns N–T are **not** loaded. FAIR magnitudes
stay anchored on cited Ponemon / Coinbase SEC benchmarks.

## Headline results (base case, 10,000 trials, seed 14817)

| | Inherent | With recommended controls |
|---|---|---|
| Expected annual loss | $96.8M | $11.0M |
| 1-in-20 year (P95) | $381M | $38.5M |
| P(annual loss ≥ $100M) | 22.0% | 3.3% |

- 500 A–M incidents → 93 linked campaigns over ~5 years.
- Recommended portfolio: C1, C2, C3, C4, C5, C6, C8, C9. Cost $10.6M/yr; net benefit $73.9M/yr; ROSI 697%.
- Bribed / colluding exfiltration ~$77M inherent; Customer support ~$45M; Operations ~$26M.
- Back-test: Coinbase FY2025 $345.2M sits on the modeled exceedance curve.

## Repository map

| Path | What it is |
|---|---|
| `app.py` | Part 4: Streamlit dashboard with the department drop-down and six tabs |
| `insider_risk/categorize.py` | Part 2: ABCD labels, credibility weights, campaign linking, auto-routing |
| `insider_risk/quantify.py` | Part 3: Gamma-Poisson frequency, lognormal primary/secondary loss, Monte Carlo |
| `insider_risk/controls.py` | Control effects, 1,024-portfolio optimizer, efficient frontier |
| `insider_risk/sensitivity.py` | Tornado and recommendation-stability analysis |
| `insider_risk/data.py` | Loaders; enforces A–M only (drops `*_usd`) |
| `data/synthetic_incidents_am.csv` | A–M fields only |
| `data/insider_reports.csv` | Mapped report schema used by the model |
| `data/benchmarks.csv` | Cited statistics B01–B22 |
| `docs/part3_quantification.md` / `part4_dashboard_design.md` | Technical write-ups |
| `results/` | Reproducible outputs quoted in the report and slides |

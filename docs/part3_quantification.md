# Part 3: Quantify (FAIR + Monte Carlo)

Team 16 · CMU 14-817 · Coinbase malicious-insider scenario

All numbers below come from `python scripts/export_results.py` (10,000 trials, seed 14817, base assumptions). Re-run it after changing any input; `results/summary.md` is regenerated automatically.

## 3.1 What Part 3 has to answer

Part 2 turns each synthetic incident (workbook columns **A–M only**) into labeled loss events. Part 3 turns those events into money: how often malicious-insider loss events happen (FAIR **Loss Event Frequency**), how much each one costs (FAIR **Loss Magnitude**), and what that implies for an annual loss distribution, before and after controls.

Two class methodologies are applied, not just named:

| Methodology | Where it is applied |
|---|---|
| **FAIR** (Open FAIR / FAIR Standard v3.0) | LEF × LM decomposition; primary vs. secondary loss; SLEF/SLM; controls act on specific FAIR factors |
| **Monte Carlo simulation with probability distributions** | 10,000 simulated years; Gamma-Poisson frequency, lognormal magnitudes; loss exceedance curve, P95/P99, TVaR |
| NIST SP 800-53 Rev. 5 / NIST CSF 2.0 (supporting) | Every control carries an 800-53 ID and a CSF function |

## 3.2 Data sources

**Dheya’s synthetic incident history** (`synthetic_insider_incidents.xlsx` → `data/synthetic_incidents_am.csv`): **500 rows, columns A–M only**.

| Col | Field | Used for |
|---|---|---|
| A–B | incident_id, incident_date | Identity + observation window (~5 years) |
| C–F | incident_type, business_line, insider_role, work_arrangement | Scenario mapping, business-unit views, subject type/location |
| G–K | records_exposed, days_to_detect, detection_method, days_to_contain, prior_warning_signs | Quant metrics + leading indicators |
| L–M | motivation, primary_impact_category | Intent / FAIR impact-form mapping (Pollmeier-style classes) |

**Explicitly not loaded into the website:** `regulatory_usd`, `customer_usd`, `media_usd`, `response_usd`, `cost_of_capital_usd`, `forensic_usd`, `total_loss_usd`. Dollar magnitude stays externally cited so the model is not circular with its own synthetic dollars.

**Marie’s benchmark statistics** (`data/raw/insider_threat_statistics.xlsx` → `data/benchmarks.csv`, IDs B01–B22). Key uses: B14 frequency prior (6.3/yr); B03/B11/B15 primary-loss anchors; B18 Coinbase 8-K $180M–$400M secondary magnitude; B19/B20 customer-scale calibration; B05–B09 / B16–B17 control-effect ceilings.

## 3.3 From A–M rows to loss events (Part 2)

1. **Scenario mapping (A).** `incident_type` + `insider_role` + `motivation` map to S1–S4 (bribed exfiltration, privileged abuse, fraud/manipulation, credential sharing).
2. **Credibility weight (D).** `detection_method` maps to evidence strength (monitoring/audit → 0.9; tip/complaint → 0.7; whistleblower → 0.6; confirmed external tip → 1.0).
3. **Campaign linking.** Same scenario, business unit and insider type within 90 days = one loss event. **500 rows → 93 campaigns.**

## 3.4 Loss Event Frequency

\[
\lambda_s \sim \text{Gamma}\big(\alpha_0 \pi_s + k_s,\; w + t\big), \qquad \alpha_0 = 6.3\,w
\]

With ~5 years of history, credibility factor \(Z = t/(t+w) \approx 0.83\): internal synthetic history dominates the prior, but the Ponemon anchor still regularizes sparse scenario cells.

| Scenario | Weighted events | Prior / yr | Observed / yr | Posterior / yr |
|---|---|---|---|---|
| S1 Bribed exfiltration | 42.2 | 1.57 | 8.55 | 7.37 |
| S2 Privileged abuse | 15.9 | 1.57 | 3.22 | 2.94 |
| S3 Fraud / manipulation | 14.7 | 1.57 | 2.98 | 2.74 |
| S4 Credential sharing | 13.0 | 1.57 | 2.63 | 2.46 |

## 3.5 Loss Magnitude

Primary and secondary loss ranges remain the calibrated 90% lognormal intervals in `scenarios.csv` (Ponemon + Coinbase SEC). Secondary loss follows FAIR: with probability SLEF a primary event triggers secondary stakeholders; SLM for S1 is anchored on Coinbase’s 8-K $180M–$400M band.

## 3.6 Results (company-wide, base case)

| Statistic | Inherent | With recommended controls |
|---|---|---|
| Expected annual loss | **$96.8M** | **$11.0M** |
| Median year | $32.7M | $3.5M |
| P95 (1-in-20 year) | $380.7M | $38.5M |
| P99 (1-in-100 year) | $618.7M | $196.9M |
| P(annual loss ≥ $100M) | 22.0% | 3.3% |
| P(annual loss ≥ $180M) | 20.2% | 1.5% |

Recommended portfolio: **C1, C2, C3, C4, C5, C6, C8, C9** · annual cost **$10.6M** · net benefit **$73.9M** · ROSI **697%**.

Department concentration: Customer support **~$45M**, Operations **~$26M** of inherent expected loss.

## 3.7 Code entry points

- `insider_risk/categorize.py` — A/B/C/D labels, campaign linking
- `insider_risk/quantify.py` — frequency posterior, FAIR magnitude, Monte Carlo
- `insider_risk/controls.py` / `sensitivity.py` — ROI, frontier, tornado, stability
- `scripts/import_synthetic.py` — A–M import
- `scripts/export_results.py` — regenerates `results/summary.md`

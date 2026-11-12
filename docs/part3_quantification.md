# Part 3: Quantify (FAIR + Monte Carlo)

Team 16 · CMU 14-817 · Coinbase malicious-insider scenario

All numbers below come from `python scripts/export_results.py` (10,000 trials, seed 14817, base assumptions). Re-run it after changing any input; `results/summary.md` is regenerated automatically.

## 3.1 What Part 3 has to answer

Part 2 turns each web-form report into labeled loss events. Part 3 turns those events into money: how often malicious-insider loss events happen (FAIR **Loss Event Frequency**), how much each one costs (FAIR **Loss Magnitude**), and what that implies for an annual loss distribution, before and after controls.

Two class methodologies are applied, not just named:

| Methodology | Where it is applied |
|---|---|
| **FAIR** (Open FAIR / FAIR Standard v3.0) | LEF × LM decomposition; primary vs. secondary loss; SLEF/SLM; controls act on specific FAIR factors (frequency, primary magnitude, SLEF, SLM) |
| **Monte Carlo simulation with probability distributions** | 10,000 simulated years; Gamma-Poisson frequency, lognormal magnitudes; loss exceedance curve, P95/P99, TVaR |
| NIST SP 800-53 Rev. 5 / NIST CSF 2.0 (supporting) | Every control carries an 800-53 ID and a CSF function, so the quantified recommendation maps straight into a control baseline |

## 3.2 Data sources

**Marie's intake sample** (`data/raw/insider_reports_sample.xlsx`): 10 reports from the "General" web form, 3 Sep to 4 Nov 2026 (63 days). Fields include insider type, business unit, access level, activities, records affected, evidence, urgency, incident type, impact categories, and routing.

**Marie's benchmark statistics** (`data/raw/insider_threat_statistics.xlsx`, curated into `data/benchmarks.csv` with IDs B01–B22). Only statistics with a citable primary source were kept. The model uses:

| ID | Statistic | Value | Used for |
|---|---|---|---|
| B14 | Malicious insider incidents per org per year (Ponemon/DTEX 2026) | 6.3 | Frequency prior |
| B10 | All-type insider events per org per year | 13.8 | Upper end of the prior sensitivity range |
| B11 | Average cost per insider incident | $747,107 | Calibration check |
| B03 | Average credential-theft incident cost | $779,707 | S4 primary loss calibration |
| B15 | Containment cost per incident | $247,587 | Lower bound of primary-loss ranges |
| B05–B09 | Annual savings from insider-risk program, PAM, UBA, training, SIEM | $8.2M, $6.1M, $5.1M, $4.8M, $4.6M | Control-effectiveness ceilings (÷ B01 $19.5M) |
| B16/B17 | Annual cost when incidents are contained in < 30 days vs > 30 days | $14.2M vs $21.9M | Containment-speed effect (35%) for C2 |
| B18 | Coinbase 8-K estimated cost of the 2025 breach | $180M–$400M | Secondary-loss magnitude for S1 |
| B19 | Coinbase FY2025 incident-related expense | $345.2M | Back-test |
| B20 | Customers affected | 69,461 | ≈ $4,970 all-in cost per affected customer |

## 3.3 From reports to loss events (Part 2 output used here)

1. **Scenario mapping (A).** Incident types map to four modeled scenarios: S1 bribed/colluding exfiltration, S2 privileged access abuse, S3 fraud/record manipulation, S4 credential/access sharing. "Precursor signals only" reports (IR-0004, IR-0009) are tracked as leading indicators, not loss events.
2. **Credibility weight (D).** A report is not a confirmed incident. Each gets a probability of being a real malicious event from its strongest evidence: system log 0.9, screenshot 0.8, witness 0.7, chat message 0.6, nothing yet 0.3. A confirmed external party sets it to 1.0.
3. **Campaign linking.** Reports with the same scenario, business unit and insider type within 90 days are one loss event. IR-0001, IR-0002 and IR-0008 (offshore BPO agents photographing customer screens, seven weeks apart) collapse into one campaign. Without this step, one bribery ring would be counted three times.

The result is 6 loss campaigns with a total weight of 5.2 events in 63 days.

## 3.4 Loss Event Frequency: Bayesian update of an industry benchmark

Ten reports are too few to estimate a rate on their own, and a benchmark alone ignores what Coinbase is actually seeing. A Gamma-Poisson (conjugate) model blends the two:

\[
\lambda_s \sim \text{Gamma}\big(\alpha_0 \pi_s + k_s,\; w + t\big), \qquad \alpha_0 = 6.3\,w
\]

- \(w\) = prior weight in years (base 1.0): the Ponemon benchmark counts as one year of data.
- \(\pi_s = 1/4\): no prior reason to favor a scenario.
- \(k_s\) = credibility-weighted campaigns; \(t\) = 63 days = 0.172 years.
- Credibility factor \(Z = t/(t+w) = 0.15\): the internal data moves the estimate 15% of the way from the benchmark toward the observed rate. Z rises automatically as reports accumulate.

| Scenario | Weighted events | Prior / yr | Observed / yr | Posterior / yr |
|---|---|---|---|---|
| S1 Bribed exfiltration | 1.0 | 1.57 | 5.80 | 2.20 |
| S2 Privileged abuse | 2.7 | 1.57 | 15.65 | 3.65 |
| S3 Fraud / manipulation | 0.9 | 1.57 | 5.22 | 2.11 |
| S4 Credential sharing | 0.6 | 1.57 | 3.48 | 1.86 |
| **Total** | 5.2 | 6.30 | 30.1 | **9.81** |

In each simulated year, \(\lambda_s\) is drawn from its posterior before the Poisson event count. This makes the count negative-binomial and carries parameter uncertainty into the tail instead of hiding it.

**Department views (Poisson thinning).** A business unit's rate is \(\lambda_s \times\) its smoothed share of scenario-s reports (pseudo-count 0.5 spread across seven units). A thinned Poisson process is still Poisson, so the seven business-unit views add up exactly to the company view (unit-tested). Response-team views use the share of reports routed to that team. They overlap by design, because one report is routed to several teams.

## 3.5 Loss Magnitude: primary and secondary loss

Each range is a calibrated 90% interval (5th–95th percentile) fitted to a lognormal:

\[
\mu = \tfrac{1}{2}(\ln L + \ln H), \qquad \sigma = \frac{\ln H - \ln L}{2 \times 1.645}
\]

| Scenario | Primary loss 90% CI | Anchor | SLEF | SLM 90% CI |
|---|---|---|---|---|
| S1 Bribed exfiltration | $0.4M–$6.0M | B15 containment; 1,000 records × $4,970 (B19/B20) | 3% | $180M–$400M (B18) |
| S2 Privileged abuse | $0.25M–$3.0M | B15 up to ~4× B11 | 2% | $15M–$150M |
| S3 Fraud / manipulation | $0.3M–$8.0M | Direct fund loss + forensics (IR-0006) | 3% | $5M–$60M |
| S4 Credential sharing | $0.1M–$2.5M | Mean ≈ $0.8M matches B03 | 1% | $5M–$50M |

Secondary loss follows FAIR: with probability SLEF a primary event triggers secondary stakeholders (extortion, scammed customers, regulators, auditors), and the secondary magnitude is drawn from the SLM distribution. Web-form impact categories are mapped onto FAIR forms of loss in Part 2. For example, "Scam reimbursement" and "Regulatory and legal" map to secondary Fines & Judgments, and "Direct fund loss" maps to primary Replacement. This mapping avoids double-counting the same cost under two labels.

## 3.6 Results (company-wide, base case)

| Statistic | Inherent | With recommended controls |
|---|---|---|
| Expected annual loss | **$40.3M** | **$8.2M** |
| Median year | $16.1M | $2.4M |
| P10–P90 | $5.8M–$72.5M | $0.5M–$8.1M |
| P95 (1-in-20 year) | $248.5M | $24.9M |
| P99 (1-in-100 year) | $394.3M | $171.5M |
| TVaR 95 (average of worst 5%) | $341.5M | $106.1M |
| P(annual loss ≥ $100M) | 8.1% | 2.3% |
| P(annual loss ≥ $180M) | 6.5% | 0.8% |

By scenario, S1 bribed exfiltration is $23.0M of the $40.3M. It is 57% of the expected loss and 92% of the loss in the worst-5% years. Customer support carries $22.6M of exposure. The dashboard shows this concentration immediately when the department drop-down is set to that business unit.

The distribution has two humps: ordinary years driven by primary losses, and rare escalation years dominated by secondary loss. That is why the mean ($40.3M) is far above the median ($16.1M), and why reporting only a single expected value would mislead the board.

## 3.7 Validation

**Calibration against benchmarks** (Methodology tab):

| Quantity | Model | Benchmark | Reading |
|---|---|---|---|
| Malicious loss events / yr | 9.8 | 6.3 (B14) | Internal reports push the rate above the industry average |
| Mean primary loss / event | $1.6M | $0.75M (B11, all types) | Malicious events at a crypto exchange should exceed the all-type average |
| Expected annual loss | $40.3M | $19.5M (B01) | Gap is the escalation tail |
| Expected primary loss only | $15.9M | $4.9M (B12) | Like-for-like comparison; Coinbase is a high-value target |

**Back-test against the real 2025 breach.** The model gives a 6.5% annual chance of a loss of $180M or more (about 1 year in 15) under current controls. Conditional on an escalation, the actual $345.2M falls at the 85th percentile of the modeled secondary-loss range. The model reproduces the size of the event that actually happened without being fitted to it.

**Analytic cross-checks.** The Monte Carlo mean matches the closed-form expected loss \(\sum_s E[\lambda_s](E[PL_s] + SLEF_s\,E[SLM_s])\). The closed-form tail screen used by the optimizer, \(1-\prod_s (\beta_s/(\beta_s+c_s))^{\alpha_s}\) (the Gamma moment-generating function), stays within one percentage point of the simulation. Both checks are in `tests/test_model.py`.

## 3.8 Controls, ROI and risk appetite

Ten controls (nine mitigations and one transfer) each act on named FAIR factors for named scenarios (`data/control_effects.csv`). Reductions on the same factor combine multiplicatively, \(\prod(1-r_i)\), so overlapping controls never exceed 100% and are not double-counted. Each control's modeled standalone reduction is kept at or below its Ponemon benchmark. For example, PAM is modeled at 16% of expected loss against a 31% benchmark, because Ponemon's figures are cross-sectional associations, not causal effects.

All 1,024 portfolios are evaluated:

- **Maximize net benefit:** C1, C2, C4, C5, C6, C8, C9 cost $7.6M/yr, avoid $32.6M/yr, net **$25.0M/yr, ROSI 329%**.
- **Cheapest portfolio within risk appetite** (P(≥$100M)): ≤ 5% costs $0.9M (C4, C9); ≤ 2% costs $5.4M (C1, C3, C4, C9); ≤ 1% costs $12.7M and requires the insurance tower (C10).
- **Finding:** no mix of mitigation controls gets the chance of a $100M+ year below about 2%. The last slice of tail risk has to be transferred or formally accepted. This is a board decision, not a technology decision.

## 3.9 Sensitivity and robustness

Tornado (inherent expected loss, base $40.3M):

1. Escalation probability (SLEF, 1%–8%): $23.9M to $81.2M
2. Industry prior frequency (3.15 to 13.8 per year): $28.8M to $67.6M
3. Weight on the prior (0.25 to 4 years): $30.7M to $64.1M
4. Secondary loss magnitude (±50%): $28.1M to $52.5M

SLEF is both the most influential input and the least evidenced, so it has the highest value of information. Tracking how often insider events escalate to extortion or regulator action is the single most useful data the dashboard can collect.

**Recommendation stability** (re-optimizing at both ends of all eight ranges, 17 cases):

- C1, C4, C5, C6, C8 and C9 are optimal in every case. These are no-regret investments.
- C2 (UEBA) and C3 (BPO floors) swing with the assumptions. Pilot them before committing.
- C7 (immutable logs/SIEM) and C10 (insurance) are never expected-value-optimal. C7 is still required by PCI DSS Req. 10 and SOX ITGC evidence; C10 is justified only by risk appetite.
- Net benefit stays positive in every case (minimum $12.4M/yr).

## 3.10 Limitations

- Ten sample reports; the Gamma prior keeps estimates anchored until more data arrives.
- Credibility weights, SLEF and control effects are analyst judgments. All three are stress-tested.
- Scenarios are simulated independently, so one compromised vendor team that triggers several scenarios at once could make the tail fatter.
- The secondary-loss anchor is a single event (Coinbase 2025).
- Insurance is modeled as a proportional cut in secondary loss rather than a retention/limit layer.

## References

- FAIR Institute (2025). *Factor Analysis of Information Risk (FAIR) Standard v3.0*.
- FAIR Institute (2025). *Analyst's Guide to Cyber Risk Data Sources* (used in Marie's FAIR category mapping).
- Pollmeier, S., Bongiovanni, I., & Slapničar, S. (2023). Designing a financial quantification model for cyber risk: A case study in a bank. *Safety Science, 159*, 106022.
- Ponemon Institute & DTEX Systems (2026). *Cost of Insider Risks Global Report* (statistics B01–B17 as cited in `data/benchmarks.csv`).
- Coinbase Global, Inc. Form 8-K (14 May 2025); Form 10-K FY2025.
- NIST SP 800-53 Rev. 5; NIST Cybersecurity Framework 2.0.

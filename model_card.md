# Model card: Insider Risk Dashboard (Coinbase, malicious insiders)

## Intended use
Decision support for an insider-risk program: prioritize scenarios and departments, compare control portfolios, and check residual risk against a board-set appetite. Built as the proof of concept for Team 16's CMU 14-817 project.

## Not intended for
- Predicting or labeling individual employees or vendors as malicious.
- Regulatory capital, audit opinions, or legal conclusions.
- Replacing control testing, incident response, or expert review.

## Inputs
| Input | Source | Status |
|---|---|---|
| Intake reports | Marie's 10-report sample from the "General" web form | Sample data |
| Frequency prior (6.3 malicious incidents/yr) | Ponemon/DTEX 2026 (B14) | Cited |
| Primary-loss 90% intervals | Ponemon (B03, B11, B15); Coinbase 10-K + Maine AG (B19/B20) | Cited anchors, team-set ranges |
| Secondary-loss magnitude (S1) | Coinbase 8-K, $180M–$400M (B18) | Cited |
| Escalation probability (SLEF) | Team estimate, tested 1%–8% | Assumption |
| Report credibility weights | Analyst judgment by evidence type | Assumption |
| Control effects | Team estimates capped at Ponemon benchmarks (B05–B09, B16/B17) | Assumption with benchmark ceiling |
| Control costs | Team estimates | Assumption |

## Model
- Loss Event Frequency: per-scenario Gamma posterior (Ponemon prior + credibility-weighted, campaign-deduplicated reports), Poisson annual counts.
- Loss Magnitude: lognormal primary loss; Bernoulli(SLEF) × lognormal secondary loss.
- Department views: Poisson thinning by smoothed report shares (business units add up to the company total; response teams overlap).
- Controls: multiplicative reductions on frequency, primary magnitude, SLEF or SLM per scenario.
- Outputs: 10,000-trial annual loss distribution, exceedance curve, P95/P99/TVaR, closed-form expected loss, portfolio optimizer, tornado, stability analysis.

## Validation performed
- [x] Monte Carlo mean matches closed-form expected loss (unit test, within 8% at 200k trials).
- [x] Business-unit views add up exactly to company-wide (unit test).
- [x] Closed-form tail screen within 1 percentage point of simulation (unit test).
- [x] Calibration check vs. Ponemon/IBM benchmarks (Methodology tab).
- [x] Back-test: FY2025 actual loss at the 85th percentile of the modeled escalation range.
- [x] One-at-a-time sensitivity on 8 inputs; recommendation stability across 17 stress cases.
- [ ] Re-estimate credibility weights from investigated case outcomes once available.
- [ ] Replace control costs with vendor quotes.
- [ ] Add dependence between scenarios (common vendor compromise).

## Known limitations
Small sample (10 reports, 63 days); single-event anchor for secondary loss; independence between scenarios; insurance modeled proportionally rather than as a retention/limit layer.

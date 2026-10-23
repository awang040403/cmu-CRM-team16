# Model card — Insider Risk Lab

## Intended use
Classroom demonstration of quantitative cyber-risk reasoning, uncertainty, and control-package comparison for the insider-threat scenario.

## Not intended for
- Estimating a real bank's actual risk without validated inputs.
- Regulatory certification, audit assurance, legal conclusions, or operational authorization.
- Predicting a specific insider or labeling an employee as malicious.
- Replacing control testing, threat modeling, incident response, or expert review.

## Inputs
- Assumed annual event frequency by scenario.
- Assumed median loss severity and lognormal sigma.
- Assumed control reductions to event frequency and severity.
- Assumed annual program costs.
- Sensitivity multipliers chosen by the user.

## Model
Annual counts are independent Poisson random variables by scenario. Event losses are independent lognormal draws. Total annual loss is the sum of event losses across the scenario set. Control packages adjust assumed frequency and median severity. Monte Carlo repetitions estimate the output distribution.

## Key assumptions
- The initial event-rate and severity parameters are illustrative.
- Annual rates are stationary.
- Events and scenarios are independent.
- The selected distributions are reasonable starting points.
- Control effectiveness is represented as a reduction percentage and does not include adversarial adaptation.
- Cost comparison is a simplified annual proxy.

## Limitations
- No correlation or common-cause modeling.
- No explicit insurance/recovery, discounting, multi-year implementation cost, or all indirect impacts.
- No automatic legal penalty calculation.
- Output quality depends on input quality and model structure.
- Monte Carlo sample size does not remove epistemic uncertainty.

## Validation checklist
- [ ] Source and owner recorded for each material input.
- [ ] Low/central/high ranges or distributions reviewed with subject-matter experts.
- [ ] Alternative distributions tested where plausible.
- [ ] Scenario dependencies and common-cause failures assessed.
- [ ] Control effectiveness grounded in evidence or documented elicitation.
- [ ] Output checked against historical incidents / near misses where available.
- [ ] Independent peer review completed.
- [ ] Random seed, code version, date, and model settings recorded.
- [ ] Interpretation avoids treating illustrative results as empirical facts.

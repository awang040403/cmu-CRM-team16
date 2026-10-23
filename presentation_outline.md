# Presentation outline — 16 slides
## Scenario 2: Insider Threat in a Multinational Financial Institution

**Target:** 12–15 minutes, adjusted to course rules. Every group member should speak and be able to explain the model and assumptions.

1. **Title and consulting question**
   - Who we are; Scenario 2; decision question: which control investments reduce insider risk to an acceptable level?
   - Speaker: opening / project lead.

2. **Executive recommendation**
   - Layered strategy: access governance first, then monitoring/data protection, then high-assurance privileged controls for critical workflows.
   - Explicit caveat: numerical inputs are illustrative until validated.

3. **Bank context and scope**
   - 50,000+ employees; employees and contractors; customer PII, transaction systems, trading algorithms, SWIFT-related workflows.
   - Define what is in/out of scope.

4. **Assets and trust boundaries**
   - Show a simple diagram: identity/privileged access → business systems/data → payment approvals → logging/SOC.
   - Mark trust boundaries, high-value data flows, and independent approval points.

5. **Threat modeling method**
   - OWASP-style steps; how assets, actors, paths, gaps, and mitigations were identified.
   - Explain that STRIDE categorizes threats rather than calculating risk.

6. **Five prioritized scenarios**
   - Data exfiltration; privileged transaction manipulation; negligent disclosure; collusion; log tampering.
   - Define the loss event boundary for each.

7. **STRIDE and attack-path mapping**
   - Map each scenario to relevant categories; show one worked path.
   - Include MITRE ATT&CK mappings only when specific technique IDs are verified against evidence.

8. **Framework integration**
   - FAIR for quantitative loss analysis; probability distributions and Monte Carlo for uncertainty; NIST SP 800-37 Rev. 2 for governance.
   - Show workflow and explain each framework's distinct job.

9. **Inputs, evidence, and assumptions**
   - Frequency, median severity, log-space sigma, control effectiveness, package cost.
   - Clearly separate sourced facts, expert estimates, and illustrative assumptions.

10. **Monte Carlo model**
    - Explain annual event counts + per-event severity + aggregation.
    - State number of trials and random seed; show limitations and independence assumptions.

11. **Risk distribution and tail exposure**
    - Show histogram, P95/P99, exceedance curve, and threshold probabilities from a saved run.
    - Do not invent values: export actual values from the app and record settings.

12. **Control packages**
    - A: essential access controls.
    - B: A + DLP/UEBA/centralized monitoring.
    - C: B + PAM, just-in-time privilege, independent approval, immutable logs.
    - Explain scenario-specific effectiveness assumptions.

13. **Cost-risk comparison**
    - Gross modeled loss reduction vs annual program cost; net benefit proxy.
    - Discuss why a simplified mean-based metric can miss tail risk and mandatory obligations.

14. **Compliance, governance, and residual risk**
    - Conditional SOX/PCI DSS/GDPR scope; avoid assuming automatic maximum penalties.
    - Risk appetite, risk acceptance owner, expiry, evidence, monitoring.

15. **90-day roadmap and KPIs**
    - 0–30 discover; 31–60 reduce access exposure; 61–90 pilot detection/evidence; 90+ validate and optimize.
    - KPIs: revocation SLA, approval compliance, log coverage, alert precision, detection/containment time.

16. **Decision request and limitations**
    - Ask leadership to approve a pilot, owners, evidence collection, model validation, and risk appetite thresholds.
    - State what would change the recommendation; invite questions.

## Suggested speaker allocation for a four-person group
- **Person 1 — Risk/consulting lead:** slides 1–4 and final synthesis.
- **Person 2 — Threat modeling lead:** slides 5–7.
- **Person 3 — Quantitative modeling lead:** slides 8–11 and live dashboard demonstration.
- **Person 4 — Controls/compliance lead:** slides 12–16.
Adjust to equalize speaking time and follow instructor rules. Every speaker should understand the overall project, not just their slides.

## Demo sequence (2–3 minutes)
1. Start with the baseline package and fixed random seed.
2. Show annual loss histogram and P95 / exceedance probabilities.
3. Select Package B or C and compare the gross loss distribution.
4. Increase the severity multiplier and show whether package ranking changes.
5. Explain that outputs move because assumptions changed; the slider is not evidence that the bank's actual risk changed.

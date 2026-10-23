# Insider Threat Risk Assessment and Quantitative Treatment Plan
## Scenario 2 — Multinational Financial Institution
### CMU 14-817 Cyber Risk Modeling — Draft for team completion

> **Evidence statement:** This is a project draft and model prototype. The numerical parameters are illustrative assumptions created to demonstrate risk modeling; they are not empirical incident rates or actual losses at a bank. Replace or validate them with credible evidence, course-provided data, or a documented expert-elicitation method before presenting numerical conclusions as evidence.

## 1. Executive summary

A multinational financial institution with more than 50,000 employees depends on trusted access to customer personally identifiable information (PII), transaction and payment workflows, trading algorithms, and SWIFT-related operations. Insider risk includes both malicious actions and unintentional mistakes by employees and contractors. The risk is not limited to a single malicious person: overbroad access, concentrated privileges, weak separation of duties, incomplete monitoring, and insufficiently protected audit evidence can combine to make an event more likely or increase its impact.

This assessment evaluates five distinct loss-event scenarios: (1) malicious customer-data exfiltration, (2) privileged transaction or payment manipulation, (3) negligent disclosure, (4) employee-contractor collusion, and (5) log tampering or evidence destruction. OWASP-style threat modeling structures the attack paths; STRIDE labels the relevant threat types; FAIR provides the quantitative risk-analysis framing; probability distributions and Monte Carlo simulation represent uncertainty; and NIST SP 800-37 Rev. 2 provides a governance lifecycle for implementing, assessing, authorizing, and continuously monitoring treatment.

The accompanying Insider Risk Lab lets decision-makers adjust event-frequency, loss-severity, and control-effectiveness assumptions; compare three incremental control packages; inspect the annual loss distribution; and examine exceedance probabilities and residual-risk indicators. It is intended to make assumptions visible, not to imply precision unsupported by evidence.

The recommended decision is to begin with a risk-based control baseline—least privilege, strong authentication, lifecycle access management, and separation of duties—then prioritize DLP/UEBA and centralized tamper-resistant logging for high-risk data flows, and apply privileged access management (PAM), just-in-time access, independent approvals, and tested incident response to the most consequential workflows. Final package selection should depend on validated risk inputs, regulatory scope, risk appetite, implementation feasibility, and tail-loss tolerance—not solely on a single expected-loss estimate.

## 2. Scope, context, and assumptions

### 2.1 Scope
In scope:
- Customer PII and sensitive customer records.
- Transaction and payment-processing workflows, including SWIFT-related processes.
- Trading algorithms and associated privileged or deployment access.
- Identity, privileged access, data movement, logging, and investigation evidence.
- Employees, contractors, privileged administrators, and possible collusion with external actors.

Out of scope unless the team obtains evidence and expands the model:
- General external cyberattacks unrelated to insider action.
- Full enterprise-wide operational risk.
- Precise legal penalty estimates without jurisdictional and factual analysis.
- Actual bank loss estimates or claims about the frequency of real insider incidents.

### 2.2 Assumptions register
| Assumption | Why it is used | Validation needed |
|---|---|---|
| Five scenario families are sufficient for a first-pass model | Keeps the analysis decision-focused and avoids a sprawling register | Confirm with asset owners and threat modeling review |
| Annual scenario counts can initially be approximated with Poisson distributions | Transparent baseline for rare event counts | Test whether rate stability and independence are plausible; use alternative distributions if not |
| Event severity is right-skewed and positive; lognormal is a starting distribution | Large losses can be much greater than typical losses | Fit or elicit severity ranges from credible evidence; test alternative distributions |
| Scenarios are independent in the initial model | Keeps first prototype understandable | Assess shared causes and dependencies; add correlated scenarios if warranted |
| Control reductions are scenario-specific percentages | Enables transparent package comparison | Estimate from control tests, evidence, vendor-neutral research, and expert elicitation |
| Package costs are annualized placeholders | Makes cost trade-offs visible | Replace with internal implementation, licensing, staffing, training, and operating-cost estimates |
| All model values are illustrative until validated | Prevents false precision | Maintain source, owner, date, confidence, and range for each parameter |

## 3. Business assets and security objectives

| Asset | Confidentiality | Integrity | Availability / resilience | Key insider concern |
|---|---|---|---|---|
| Customer PII | Prevent unauthorized disclosure | Preserve accuracy and lawful handling | Maintain service continuity | Bulk access, exfiltration, negligent sharing |
| Transaction and payment systems | Restrict sensitive transaction details | Prevent unauthorized transaction changes | Prevent disruption of critical payment operations | Privileged manipulation, collusion, concealment |
| SWIFT-related workflows | Restrict access to sensitive payment information | Protect payment-message integrity and authorization | Maintain reliable payment processing | Misuse of credentials, approval bypass, evidence loss |
| Trading algorithms and model artifacts | Protect proprietary strategy | Prevent unauthorized code/model changes | Maintain reliable execution and deployment | Algorithm tampering, theft, unauthorized release |
| Identity and privileged-access systems | Protect authentication secrets and role data | Preserve role and entitlement integrity | Ensure secure, reliable access | Privilege escalation, stale accounts, misuse of administrative capability |
| Audit logs and monitoring evidence | Restrict access to sensitive evidence | Preserve integrity and traceability | Ensure investigation and compliance readiness | Log deletion, alteration, monitoring disablement |

## 4. Threat modeling

The threat model follows a structured process: define the system boundary and sensitive assets; identify actors and trust boundaries; map plausible attack paths; categorize threat types; assess current control gaps; and select mitigations. STRIDE is used as a taxonomy, not as a quantitative probability model. MITRE ATT&CK may be added as a threat-informed mapping where a specific technique is supported by evidence; do not assign ATT&CK IDs by guesswork.

### 4.1 Scenario S1 — Malicious customer-data exfiltration
- **Actor:** Employee or contractor with legitimate access.
- **Loss event:** Sensitive customer data is copied to an unauthorized destination and the institution incurs response, investigation, remediation, legal, customer-support, or other applicable costs.
- **Attack path:** Overbroad access → bulk query/export → transfer to a personal or external destination → delayed detection or containment.
- **STRIDE:** Information disclosure; potentially elevation of privilege.
- **Control gaps to test:** Excessive entitlements; unmonitored bulk access; DLP coverage gaps; inadequate egress controls; limited alert triage.
- **Treatment:** Least privilege, data minimization, DLP, UEBA, secure sharing defaults, centralized logs, tested incident response.
- **Key indicators:** Sensitive-data export alerts investigated within SLA; privileged access review completion; time to contain confirmed exfiltration.

### 4.2 Scenario S2 — Privileged transaction or SWIFT-related manipulation
- **Actor:** Privileged administrator or operations insider.
- **Loss event:** Unauthorized payment or transaction change is executed, or a high-risk instruction is released without required independent authorization.
- **Attack path:** Privileged session → transaction/beneficiary modification → approval bypass or misuse → release → delayed reconciliation.
- **STRIDE:** Tampering, repudiation, elevation of privilege.
- **Control gaps to test:** Concentrated permissions; shared accounts; weak separation between change and approval; insufficient independent reconciliation; mutable logs.
- **Treatment:** PAM, just-in-time privilege, dual authorization, separation of duties, immutable audit trails, independent reconciliation, tested payment recovery.
- **Key indicators:** High-risk payment changes with independent approval; privileged-session coverage; unauthorized change detection time.

### 4.3 Scenario S3 — Negligent disclosure or mishandling
- **Actor:** Employee or contractor acting unintentionally.
- **Loss event:** Sensitive data is sent to an incorrect recipient or placed in an unsafe sharing location.
- **Attack path:** Routine workflow → misaddressed message or unsafe sharing → external exposure → response and remediation.
- **STRIDE:** Information disclosure.
- **Control gaps to test:** Unsafe defaults; inadequate recipient confirmation; inconsistent DLP coverage; confusing handling procedures.
- **Treatment:** DLP tuned to business workflows, safe sharing defaults, recipient confirmation, targeted training, simple reporting and response.
- **Key indicators:** Confirmed misdelivery rate; repeat policy violations; false-positive rate for DLP alerts.

### 4.4 Scenario S4 — Employee-contractor collusion
- **Actor:** Employee and contractor or external accomplice.
- **Loss event:** Multiple parties coordinate to bypass controls, expose data, or manipulate a transaction.
- **Attack path:** Split knowledge/access across actors → coordinated activity → bypass of single-person controls → delayed detection.
- **STRIDE:** Depending on the path, spoofing, tampering, information disclosure, or elevation of privilege.
- **Control gaps to test:** Incompatible roles; weak contractor lifecycle controls; single-person approvals; monitoring that fails to correlate across identities.
- **Treatment:** Separation of duties, independent approval, contractor access expiration, cross-account analytics, conflict-of-interest review, protected whistleblower/speak-up channels.
- **Key indicators:** Unresolved incompatible-role conflicts; contractor accounts past end date; high-risk approvals without independent evidence.

### 4.5 Scenario S5 — Log tampering or evidence destruction
- **Actor:** Privileged insider seeking to conceal activity.
- **Loss event:** Logs or records needed to detect, investigate, or demonstrate control operation are disabled, altered, or deleted.
- **Attack path:** Privileged access → logging/retention change → evidence gap → delayed detection or impaired investigation.
- **STRIDE:** Tampering, repudiation, and potentially denial of service.
- **Control gaps to test:** System administrators can alter their own audit evidence; logging changes are not separately alerted; retention is not independently verified.
- **Treatment:** Immutable centralized logging, separate log-admin roles, alerts on logging changes, protected retention, independent evidence review, tested incident response.
- **Key indicators:** Critical systems with tamper-resistant log coverage; log pipeline availability; time to detect logging changes.

## 5. Methodology and framework integration

### 5.1 OWASP-style threat modeling and STRIDE
Threat modeling supplies the system and attack-path structure. STRIDE categorizes threats that may affect system properties. It does not itself produce a calibrated annual dollar-loss estimate. The output is a threat register with assets, actors, events, paths, existing controls, control gaps, and mitigations.

### 5.2 FAIR framing
FAIR is the quantitative risk framework. Use the exact terminology and decomposition from the course-assigned FAIR Standard v3.0. At a high level, the analysis concerns the frequency of loss events and the magnitude of loss when events occur. The Python prototype approximates annual event frequency and event severity using transparent probability distributions; this is a simplified quantitative implementation and must not be claimed to be a complete or certified FAIR implementation.

For each scenario, record:
- Parameter name and definition.
- Low / most-likely / high estimate or distribution parameters.
- Evidence source or elicitation rationale.
- Confidence and uncertainty.
- Owner responsible for validation.
- Date last reviewed.

### 5.3 Probability and Monte Carlo
The prototype runs repeated trials. For each trial and scenario, it samples a number of events for one year, samples a loss severity for each event, and sums those losses across scenarios. Repeating this process produces a distribution rather than a single point estimate.

Baseline assumptions:
- Annual event count: Poisson with mean \(\lambda\), a modeling choice that should be tested.
- Per-event loss severity: lognormal, parameterized by the median and log-space sigma.
- Annual portfolio loss: sum of event losses across the five scenario families.
- Control package: reduces assumed event frequency and median severity using scenario-specific effectiveness assumptions.
- Initial dependence assumption: scenarios and event severities are independent. This is a simplification and may understate tail risk if a common insider, identity compromise, or control failure can trigger multiple losses.

Outputs:
- Mean and median annual loss.
- 90th, 95th, and 99th percentile annual loss.
- Probability annual loss exceeds chosen thresholds.
- Scenario-level simulated contribution.
- Gross loss reduction and a simplified net annual benefit proxy after annual program cost.

Do not report values from the prototype as empirical facts. Re-run the code, record the seed and settings, and include the output date. Use sensitivity analysis to show how conclusions change under lower/higher frequencies, severity, and control effectiveness.

### 5.4 NIST SP 800-37 Rev. 2 governance lifecycle
Use the RMF as the management lifecycle, not as a dollar-loss calculator:
1. **Prepare:** define context, roles, assets, risk assumptions, and decision authority.
2. **Categorize:** classify information systems and information types according to applicable policy.
3. **Select:** choose controls based on risk, requirements, and constraints.
4. **Implement:** deploy controls with accountable owners.
5. **Assess:** independently test whether controls work as intended.
6. **Authorize:** make explicit, documented risk acceptance decisions.
7. **Monitor:** continuously review controls, indicators, incidents, and changing assumptions.

If the team adds NIST SP 800-30, make clear it is supplementary unless confirmed as covered in class; the provided course outline specifically lists SP 800-37 Rev. 2.

## 6. Quantitative model and interpretation

### 6.1 Input parameter table
The starter CSV includes five scenario rows with illustrative annual frequencies, median severities, log-space sigma values, control-effectiveness assumptions, and owners. These values were selected to demonstrate a working analysis and are not supported by empirical bank-specific data. Replace them with sourced ranges or document expert elicitation.

### 6.2 Why use distributions?
A point estimate can hide uncertainty. A single annual frequency of 0.25 could represent a rare event with a wide plausible range; a single loss amount can hide a long tail. Monte Carlo simulation allows decision-makers to ask not only “What is the mean?” but also “How often could losses exceed a threshold?” and “Does the preferred control package change if assumptions worsen?”

### 6.3 How to read the dashboard
- **Mean annual loss:** average across simulated years; sensitive to both event frequency and severe tail events.
- **Median:** midpoint of the modeled annual-loss distribution; may be below the mean for right-skewed losses.
- **P95:** 95% of simulated annual outcomes are at or below this level under the model assumptions; 5% are above.
- **Exceedance probability:** estimated fraction of simulated years where loss is greater than a selected threshold.
- **Gross loss avoided:** baseline mean loss minus package mean loss.
- **Net annual benefit proxy:** gross mean loss avoided minus assumed annual program cost. This is a screening metric only, not a complete return-on-investment estimate.

### 6.4 Limitations and model risk
The model does not automatically account for:
- Correlated scenarios or common-cause failures.
- Recovery, insurance, or recoveries from counterparties.
- Reputational effects unless explicitly modeled.
- Legal/regulatory penalties without applicable facts and careful treatment of overlap.
- Multi-year implementation cost, discount rates, staffing, and operational friction.
- Changes in adversary behavior after controls are introduced.
- Calibration uncertainty or imperfect detection.
- Non-stationary event rates and changing business scale.

Use sensitivity analysis and independent review. More simulation iterations reduce Monte Carlo sampling noise but do not correct bad inputs or a wrong model structure.

## 7. Control packages and risk treatment

### Package A — Essential access controls
- Least privilege and role-based access review.
- Strong authentication for sensitive and privileged access.
- Timely joiner/mover/leaver and contractor offboarding.
- Separation of duties for high-risk operations.
- Basic logging and escalation process.

### Package B — Enhanced monitoring and data protection
Package A plus:
- DLP for high-risk data flows.
- UEBA to flag anomalous access and behavior, with human review.
- Centralized logging and alert triage.
- Secure sharing defaults and data-handling guardrails.
- Metrics for alert precision, response times, and control coverage.

### Package C — High-assurance privileged controls
Package B plus:
- PAM and just-in-time privilege elevation.
- Independent approvals for high-risk transaction changes.
- Tamper-resistant audit logs and separate log administration.
- More rigorous cross-identity/collusion monitoring.
- Tested response playbooks and recovery/tabletop exercises.

Do not assume the most expensive package is automatically optimal. The bank should evaluate risk reduction, cost, implementation feasibility, operational impact, regulatory obligations, and appetite for tail risk. Certain mandatory controls may be required regardless of a simplified expected-loss calculation.

### Risk treatment decisions
For each risk, record:
- Inherent risk: before the relevant controls.
- Current residual risk: after verified controls already operating.
- Target residual risk: expected after proposed treatment, supported by evidence.
- Treatment: reduce, avoid, transfer/share, or accept where permitted.
- Accountable risk owner and executive approval.
- Deadline, funding, compensating controls, and evidence of completion.
- Exception expiry and review date.

## 8. Compliance and governance considerations

- **SOX:** discuss internal controls over financial reporting only where the relevant entity, reporting process, and obligations are in scope. Link privileged changes, transaction evidence, and access reviews to the control objective where applicable.
- **PCI DSS:** apply to the cardholder-data environment and systems/processes in scope. It is a security standard with contractual/payment-brand consequences, not a general federal statute.
- **GDPR:** evaluate material and territorial scope, controller/processor roles, data categories, breach facts, notification requirements, and applicable supervisory authority. Do not assume every incident triggers the maximum penalty.
- **Privacy and employment:** employee monitoring, UEBA, and whistleblower programs should be proportionate, transparent where required, access-restricted, and reviewed by privacy/legal/HR specialists.
- **Whistleblower/speak-up channels:** protect confidentiality to the extent possible, prohibit retaliation, provide safe escalation, and ensure allegations are investigated fairly. A report or behavioral alert is a lead for review—not proof of misconduct.

Avoid double counting. For example, the same response effort should not be added as separate “incident response,” “investigation,” and “remediation” costs unless those categories represent distinct resources.

## 9. Implementation roadmap

| Phase | Priority actions | Accountable roles | Evidence / KPI |
|---|---|---|---|
| Days 0–30 | Inventory sensitive assets and privileged roles; validate current controls and access paths; identify stale accounts and incompatible duties | CISO, IAM, business owners, Internal Audit | Inventory completeness; stale-account count; access review coverage |
| Days 31–60 | Reduce excess access; strengthen authentication; enforce independent approvals for high-risk payment changes; improve contractor offboarding | IAM, Payments Operations, Procurement | Revocation SLA; dual-approval compliance; unresolved role conflicts |
| Days 61–90 | Pilot DLP/UEBA in high-risk workflows; centralize and protect logs; tune alerts; test response and evidence preservation | SOC, Data Protection, IT Operations | Alert precision; time to detect/contain; immutable-log coverage |
| Day 90 onward | Conduct tabletop exercises; validate control performance; refresh model inputs; review risk acceptance and exceptions quarterly | Operational Risk, Risk Committee, Internal Audit | Residual risk; P95/P99 trend; overdue remediation; test results |

## 10. Key risk indicators and validation plan

| KRI / KPI | Definition | Owner | Review |
|---|---|---|---|
| Privileged access review completion | Percentage of in-scope privileged entitlements reviewed by due date | IAM | Monthly |
| Time to revoke access | Elapsed time between a valid termination/role-change trigger and access removal | HR + IAM | Monthly |
| Independent approval compliance | Share of defined high-risk transaction changes with required independent approval | Payments Operations | Monthly |
| Tamper-resistant log coverage | Share of critical systems whose logs are centralized and protected from local alteration | SOC / IT Operations | Monthly |
| DLP alert precision | Confirmed actionable alerts divided by reviewed alerts, using an agreed label definition | Data Protection | Monthly |
| Time to detect / contain | Median and high-percentile elapsed time from event start/alert to detection/containment | SOC | Monthly / after incident |
| Unresolved incompatible-role conflicts | Number and age of access conflicts beyond remediation SLA | IAM + business owners | Monthly |
| Model input coverage | Share of material inputs with source, owner, date, and confidence documented | Operational Risk | Quarterly |
| Residual loss distribution | Simulated mean/P95/P99 and threshold exceedance under approved assumptions | Operational Risk | Quarterly and after major changes |

### Validation activities
1. Walk through each scenario with system and business owners.
2. Test representative control paths in a safe environment.
3. Compare modeled event and loss assumptions with incident, near-miss, audit, and control-test evidence where available.
4. Independently review distribution choices, truncation/aggregation, and dependence assumptions.
5. Re-run sensitivity analysis and record whether package rankings change.
6. Conduct a tabletop for a data exfiltration event and a privileged payment-manipulation event.
7. Document decisions, limitations, dissenting views, and model version.

## 11. Conclusion

Insider risk is a combined access, process, monitoring, and governance problem. The institution should not rely on employee training alone or assume that monitoring by itself prevents loss. A layered strategy should restrict unnecessary access, separate high-risk duties, detect anomalous activity, preserve independent evidence, and rehearse response. The interactive model makes uncertainty and trade-offs visible, while the risk register and roadmap translate analysis into ownership and measurable action.

The final management decision should be made only after the team validates input assumptions, confirms regulatory applicability, tests proposed controls, and compares the residual loss distribution against approved risk appetite. The model is a decision-support aid—not a substitute for evidence, expert judgment, legal advice, or independent control assessment.

## References to complete from course materials
- FAIR Institute. *FAIR Standard v3.0* (course-assigned version, January 2025). Cite the exact edition and relevant sections used.
- NIST. *SP 800-37 Rev. 2: Risk Management Framework for Information Systems and Organizations*.
- OWASP. Threat Modeling guidance and Threat Modeling Cheat Sheet (exact pages/versions used).
- MITRE. ATT&CK knowledge base (only specific technique pages actually mapped).
- Course textbook: *Confronting Cyber Risk*, chapters assigned in Weeks 1–6.
- Course CRM lecture slides (cite lecture number and slide number where required).
- Any course-provided dataset or case study used to calibrate an input.
- Any external evidence used for incident frequency, loss severity, control efficacy, cost, or regulatory interpretation.

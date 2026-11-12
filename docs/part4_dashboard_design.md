# Part 4: Dashboard interface design

Team 16 · CMU 14-817 · Run with `streamlit run app.py`

## 4.1 Design goal

Each stakeholder should answer their own question in under a minute from one screen, without reading the model. The proof-of-concept mock-up in our Milestone 1 deck (scope list on the left; expected loss, P10–P90 range, report count, loss by scenario, and NIST + regulation controls on the right) is kept as the landing view. Everything else is one click deeper.

| User | Question | Where they get it |
|---|---|---|
| Board / audit committee | "Are we within risk appetite? What is the 1-in-20 year?" | Dashboard → risk appetite check; Monte Carlo → exceedance curve |
| CISO / insider-risk lead | "Which controls, in what order, for how much?" | Controls & ROI → objective selector and efficient frontier |
| Department head (e.g., Customer support) | "How much of this is mine, and what should I fix first?" | Department drop-down → KPIs, scenario bars, top controls |
| Response team (HR, IT, Legal, Security, Finance) | "What is in my queue and how exposed is it?" | Drop-down → response-team view; Report intake tab |
| Analyst / auditor | "Where does each number come from? What if it is wrong?" | Methodology & sources; Sensitivity |

## 4.2 The department drop-down

A single **Department view** drop-down at the top of the sidebar re-scopes every KPI, chart, recommendation and table. It offers three kinds of view, because "department" means two different things in an insider program:

1. **Company-wide.** Total exposure, return on security investment, and the back-test against the 2025 breach.
2. **Response team** (Security, IT, Legal, HR, Finance, Insider risk team). These are the teams reports are routed to (the departmental forms in Part 1). The view shows the exposure each team must handle. Views overlap because one report can go to several teams; the interface says so.
3. **Business unit** (Customer support, Engineering, Finance and treasury, Human resources, Operations, Sales and marketing, Compliance and risk). This is where the insider works. Business-unit views partition the company: they add up exactly to the company-wide total (Poisson thinning), so no exposure is double-counted when budgets are allocated.

Switching to **Business unit · Customer support** shows $22.6M of the $40.3M company exposure, $19.5M of it bribed exfiltration. BPO personnel security (PS-7) and ticket-scoped access (AC-6) top its control list. PS-7 carries an "outside optimal portfolio" pill: it is this unit's best single fix, but company-wide, AC-6 plus fraud friction already remove most of the same loss more cheaply. The pill makes that disagreement visible instead of hiding it. **Response team · HR** shows $3.6M, mostly privileged access abuse (the payroll export in IR-0007), and its list leads with AC-6 and PAM (AC-2/AC-6(5)). Units with no reports yet (e.g., Compliance and risk) still show a small, smoothed share instead of a misleading zero.

## 4.3 Screen layout

**Sidebar (always visible):** department drop-down; control multiselect with *Recommended* and *Clear* buttons; collapsible model assumptions (prior, credibility, loss multipliers, control effectiveness and cost, trial count, seed); collapsible risk appetite (loss threshold, maximum acceptable probability).

**KPI strip (always visible):** expected loss / yr · P10–P90 range · reports this quarter (with change vs. last quarter) · residual loss / yr after the selected controls · ROSI (company view) or loss avoided (department view, because control costs are company-wide).

**Tabs:**

| Tab | Content | Design choice |
|---|---|---|
| Dashboard | Inherent vs. residual loss by scenario; top controls for this view with NIST 800-53 ID, CSF function, regulation and a deployed / optimal / outside-optimal status; risk appetite pass/fail; business-unit × scenario heat map; response-team exposure bars; downloadable executive brief | Mirrors the Milestone 1 mock-up; status pills explain why a high-ranked control may still be left out |
| Monte Carlo | Log-scale loss histogram (inherent vs. residual); loss exceedance curve with the board-appetite marker and Coinbase 2025 reference lines; tail statistics (mean to TVaR 95); scenario share of average vs. worst-5% years; back-test | Log scales, because the losses span four orders of magnitude; tail shown next to the mean |
| Controls & ROI | Three objectives (max net benefit, cheapest within appetite, best within budget); cost vs. residual-loss scatter of all 1,024 portfolios with efficient frontier and break-even line; control catalog with standalone, benchmark and marginal value; *Deploy this portfolio* button | Makes the trade-off visible instead of presenting one answer |
| Sensitivity | Tornado for inherent loss, residual loss or net benefit; "what would change our answer" callout; recommendation stability across 17 stress cases (core / swing / never-optimal controls) | Turns uncertainty into a decision rule |
| Report intake (Parts 1–2) | Leading indicators (precursors, days to report vs. Ponemon's 67-day containment, vendor share, ongoing); new-report form with automatic routing; ABCD-categorized table; linked campaigns; CSV export | Closes the loop: a submitted report updates the Bayesian frequency and every chart immediately |
| Methodology & sources | Pipeline and FAIR-ontology diagrams; Bayesian update table with credibility factor; calibration check vs. Ponemon/IBM; scenario parameters with their basis; cited benchmark table with links; limitations | Every number is traceable to a benchmark ID or a labeled team estimate |

## 4.4 NIST and regulatory mapping

Every control carries a NIST SP 800-53 Rev. 5 control ID, a NIST CSF 2.0 function, the regulations it supports, and the Milestone 1 gap it closes. The control catalog shows all four.

| ID | Control | 800-53 | CSF 2.0 | Regulation | Gap closed |
|---|---|---|---|---|---|
| C1 | Ticket-scoped access, field masking, logged reveal | AC-6, AC-3 | Protect | GDPR Art. 25/32, PCI DSS 7, NYDFS 500.7 | Data scope |
| C2 | UEBA with automatic access suspension | SI-4, AU-6, IR-4 | Detect / Respond | PCI DSS 10, NYDFS 500.14 | Containment speed |
| C3 | BPO personnel security, device-free floors | PS-7, PS-3, SA-9 | Govern (GV.SC) | GDPR Art. 28, NYDFS 500.11 | Vendor oversight, screen capture, bribe economics |
| C4 | Vendor-inclusive whistleblower channel + bribe bounty | PM-12, AT-2(2) | Govern | SOX §301/§806 | Vendor reporting |
| C5 | PAM with just-in-time admin | AC-2, AC-6(5), IA-2(1) | Protect | SOX ITGC, PCI DSS 7/8 | Shared admin credentials |
| C6 | Separation of duties, dual approval for limits | AC-5, CM-3 | Protect | SOX §404 | Limit changes outside change control |
| C7 | Immutable audit logs + SIEM | AU-9, AU-6, AU-12 | Detect | PCI DSS 10, SOX §404 | Edited reconciliation notes; stale assurance |
| C8 | Fraud friction on exposed accounts | IR-4, SI-4 | Respond | NYDFS 500.16 | Fraud friction |
| C9 | Centralized reporting and quantification dashboard | PM-12, PM-16, RA-3 | Govern / Identify | SOX §404, SEC 8-K Item 1.05 | No linked view of related reports |
| C10 | Cyber and crime insurance tower (transfer) | PM-9 | Govern (GV.RM) | SEC Reg. S-K Item 106 | Residual tail |

## 4.5 Suggested live demo (about 3 minutes)

1. **Company-wide.** "$40.3M expected, but the 1-in-20 year is $249M, and Coinbase's real $345M sits on our curve." Point to the exceedance curve.
2. **Drop-down → Business unit · Customer support.** "$22.6M of it lives here, almost all bribed exfiltration. Locking down BPO floors is this unit's best single fix, yet it falls outside the company-optimal portfolio. Here's why."
3. **Clear the controls → Recommended.** Watch residual loss fall to about $8M and ROSI reach about 330%.
4. **Controls & ROI → Cheapest within appetite, set to 1%.** "No mitigation mix gets there; only insurance does. That is a board decision."
5. **Report intake → submit a confirmed bribed-exfiltration report from an Operations contractor.** It is routed automatically to Security, IT and Legal, opens a new campaign, and company expected loss rises by roughly $8M. Then submit the same thing for Customer support BPO staff. It is linked to the existing bribery campaign, so expected loss does not jump. "The model does not double-count one ring reported twice." The pipeline is live.
6. **Sensitivity.** "If escalation probability is 8% instead of 3%, loss doubles, but the core six controls stay optimal in every stress case."

## 4.6 Accessibility and integrity choices

- A dark theme matching the mock-up; color is never the only signal (pills and icons carry text, and heat-map cells are labeled).
- A banner on every view states that this is a proof of concept and which numbers are cited vs. team estimates.
- Fixed random seed and trial count are shown, so screenshots in the report can be reproduced.
- Response-team totals are explicitly marked as overlapping; business-unit totals are marked as additive.

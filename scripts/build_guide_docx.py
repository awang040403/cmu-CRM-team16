"""Build the Word summary + user guide for Parts 3 and 4.

Usage:  python scripts/build_guide_docx.py
Needs:  pip install python-docx; screenshots from scripts/capture_screenshots.py
Writes: ../Parts 3-4 Summary and Dashboard Guide.docx (next to the project PDFs)
"""
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "docs" / "screenshots"
OUT = ROOT.parent / "Parts 3-4 Summary and Dashboard Guide.docx"
BLUE = RGBColor(0x1F, 0x4E, 0x9A)
GREY = RGBColor(0x59, 0x59, 0x59)

doc = Document()
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(10.5)
for s in doc.sections:
    s.left_margin = s.right_margin = Inches(0.9)
    s.top_margin = s.bottom_margin = Inches(0.8)


def shade(cell, hex_color):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def para(text, bold_lead=None, size=None, color=None, italic=False, space_after=6):
    p = doc.add_paragraph()
    if bold_lead:
        r = p.add_run(bold_lead)
        r.bold = True
    r = p.add_run(text)
    r.italic = italic
    if size:
        r.font.size = Pt(size)
    if color:
        r.font.color.rgb = color
    p.paragraph_format.space_after = Pt(space_after)
    return p


def bullets(items, style_name="List Bullet"):
    for item in items:
        p = doc.add_paragraph(style=style_name)
        if isinstance(item, tuple):
            p.add_run(item[0]).bold = True
            p.add_run(item[1])
        else:
            p.add_run(item)
        p.paragraph_format.space_after = Pt(2)


def table(header, rows, widths=None, font=9.5):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(h)
        r.bold = True
        r.font.size = Pt(font)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        shade(c, "1F4E9A")
    for k, row in enumerate(rows):
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(v))
            r.font.size = Pt(font)
            if k % 2:
                shade(cells[i], "EEF3FB")
    for row in t.rows:
        for c in row.cells:
            c.paragraphs[0].paragraph_format.space_after = Pt(1)
    if widths:
        t.autofit = False
        layout = OxmlElement("w:tblLayout")
        layout.set(qn("w:type"), "fixed")
        t._tbl.tblPr.append(layout)
        for i, w in enumerate(widths):
            t.columns[i].width = Inches(w)
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Inches(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def figure(name, caption, width=6.6):
    doc.add_picture(str(SHOTS / f"{name}.png"), width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph()
    r = p.add_run(caption)
    r.italic = True
    r.font.size = Pt(9)
    r.font.color.rgb = GREY
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER


def callouts(items):
    """Numbered explanations that match the red numbers on the screenshot."""
    for n, (title, text) in enumerate(items, 1):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(f"({n}) {title}. ")
        r.bold = True
        r.font.color.rgb = RGBColor(0xC0, 0x1E, 0x1E)
        p.add_run(text)


# --------------------------------------------------------------------------- title

t = doc.add_paragraph()
t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run("Parts 3 & 4 Upgrade: Quantification and Dashboard")
r.bold = True
r.font.size = Pt(22)
r.font.color.rgb = BLUE
s = doc.add_paragraph()
s.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = s.add_run("Summary of changes, why they target an outstanding grade, and how to use the website\n"
              "CMU 14-817 Cyber Risk Modeling · Team 16 (Dheya, Marie, Amy) · Coinbase insider-threat scenario")
r.font.size = Pt(11)
r.font.color.rgb = GREY

# --------------------------------------------------------------------------- 1

doc.add_heading("1. At a glance", level=1)
para("We rebuilt Part 3 (Quantify) and Part 4 (Dashboard) of our pipeline. The earlier prototype modeled a "
     "generic bank with made-up numbers. The new version runs on Marie's intake reports and cited statistics, "
     "models Coinbase specifically, and lets anyone pick a department from a drop-down and see that "
     "department's risk, recommended controls and compliance mapping.")
table(["Result (base case, 10,000 simulated years)", "Today", "With recommended controls"], [
    ["Expected annual loss", "$40.3M", "$8.2M"],
    ["Typical bad year (1-in-20, P95)", "$249M", "$25M"],
    ["Chance of a $100M+ year", "8.1%", "2.3%"],
    ["Recommended controls", "–", "C1, C2, C4, C5, C6, C8, C9"],
    ["Annual cost / net benefit / ROSI", "–", "$7.6M / $25.0M / 329%"],
], widths=[3.2, 1.4, 2.0])

# --------------------------------------------------------------------------- 2

doc.add_heading("2. What changed", level=1)
doc.add_heading("2.1 Before vs. after", level=2)
table(["Area", "Before", "After"], [
    ["Data", "Five illustrative bank scenarios typed into a CSV; no real sources",
     "Marie's 10 web-form reports + 22 cited benchmarks (Ponemon/DTEX 2026, IBM, Coinbase 8-K/10-K), each with an ID"],
    ["Company", "Unnamed multinational bank", "Coinbase, with the 2025 bribed-support-agent breach as the anchor event"],
    ["Part 2 link", "None", "Each report gets the A/B/C/D labels from our deck; duplicate reports of one bribery ring are linked into one campaign"],
    ["Frequency", "Fixed guesses per scenario",
     "Bayesian update: Ponemon's 6.3 incidents/yr prior + credibility-weighted reports (credibility factor shown)"],
    ["Loss size", "One lognormal per scenario",
     "FAIR primary loss + secondary loss (escalation probability × Coinbase-scale $180M–$400M)"],
    ["Simulation", "Monte Carlo of illustrative numbers",
     "10,000-run Monte Carlo with parameter uncertainty, exceedance curve, P95/P99/TVaR, back-test"],
    ["Departments", "No department view",
     "Single drop-down: Company-wide, 6 response teams, 7 business units; every number re-scopes"],
    ["Controls", "Three generic packages A/B/C",
     "10 named controls tied to the gaps in our deck, each with NIST 800-53 ID, CSF 2.0 function, regulation and cost"],
    ["Decision support", "Net-benefit bar chart",
     "All 1,024 control combinations, efficient frontier, cheapest portfolio within board risk appetite, budget mode"],
    ["Uncertainty", "Three sliders",
     "Tornado chart + recommendation-stability test across 17 stress cases"],
    ["Live demo", "None", "Report-intake form: submit a report, it is routed and categorized, and all numbers update"],
    ["Quality", "3 basic tests", "13 tests (math, partitions, optimizer, and the dashboard itself), reproducible results export"],
], widths=[1.1, 2.2, 3.4], font=9)

doc.add_heading("2.2 Files", level=2)
para("Everything is in the insider_threat_project folder.", space_after=3)
table(["File", "Purpose"], [
    ["app.py", "The dashboard website (Part 4)"],
    ["insider_risk/categorize.py", "Part 2: A/B/C/D labels, credibility weights, campaign linking, auto-routing"],
    ["insider_risk/quantify.py", "Part 3: Bayesian frequency, FAIR loss magnitude, Monte Carlo, calibration"],
    ["insider_risk/controls.py, sensitivity.py", "Control ROI, portfolio optimizer, tornado, robustness"],
    ["data/raw/", "Marie's original Excel files (unchanged)"],
    ["data/benchmarks.csv, scenarios.csv, controls.csv", "Every input with its source or labeled as a team estimate"],
    ["docs/part3_quantification.md", "Part 3 write-up ready for the report"],
    ["docs/part4_dashboard_design.md", "Part 4 write-up and demo script"],
    ["results/summary.md", "Every number quoted in this document, regenerated by scripts/export_results.py"],
    ["Removed: risk_model.py, data/risk_register.csv", "Old generic-bank model (still in git history)"],
], widths=[2.6, 4.1], font=9)

# --------------------------------------------------------------------------- 3

doc.add_heading("3. Why this targets an outstanding (A) grade", level=1)
para("The guidance says simply covering the listed items earns a B; an A needs creativity, innovation and "
     "complex problem solving, plus at least two class methodologies applied in depth. Here is how each "
     "expectation is met:")
table(["What the professor looks for", "Typical B-level project", "Our project"], [
    ["≥ 2 class methodologies, applied", "Names FAIR and NIST on a slide",
     "FAIR decomposition drives the math; Monte Carlo with probability distributions; NIST 800-53 + CSF 2.0 map every control; Bayesian credibility blends data"],
    ["Quantify likelihood and impact", "ALE = ARO × SLE with guessed numbers",
     "Frequencies from cited benchmark + our own reports; losses anchored on Ponemon and Coinbase SEC filings"],
    ["Use real evidence", "Generic statistics",
     "Marie's intake sample and 22 cited statistics, each traceable by ID in the app"],
    ["Model uncertainty", "Single point estimate",
     "Full loss distribution, 1-in-20/1-in-100 years, tornado, and a test of whether the recommendation changes"],
    ["Validate the model", "Not done",
     "Back-tested on the real 2025 breach: $345M sits at the 85th percentile of our escalation range; calibration vs. Ponemon/IBM"],
    ["Residual risk + ROI", "Before/after for one package",
     "Residual loss for any portfolio; ROSI; efficient frontier; insurance (risk transfer) vs. mitigation"],
    ["Heat map / simulation", "Static heat map",
     "Live department × scenario heat map and response-team workload view"],
    ["Compliance (SOX, PCI DSS, GDPR)", "List of laws",
     "Each control mapped to the specific article/requirement it supports (e.g., PCI DSS Req. 10, GDPR Art. 32, SOX §404)"],
    ["Creativity / innovation", "Slides only",
     "Working product: live intake → categorize → quantify → dashboard; campaign linking stops double-counting"],
    ["Consistency", "Numbers differ between slides and report",
     "One source of truth: results/summary.md regenerates every quoted figure"],
], widths=[1.6, 1.6, 3.5], font=9)

doc.add_heading("Findings that make the presentation stand out", level=2)
bullets([
    ("Concentration: ", "bribed vendor data theft is 57% of expected loss and 92% of the loss in the worst years; "
                        "Customer support carries $22.6M of the $40.3M."),
    ("Mean vs. tail: ", "the median year costs $16M but the 1-in-20 year costs $249M. Reporting only an average would mislead the board."),
    ("Risk transfer is a board decision: ", "no mix of security controls gets the chance of a $100M+ year below about 2%; "
                                           "reaching 1% needs the insurance tower."),
    ("No-regret controls: ", "C1, C4, C5, C6, C8 and C9 stay optimal in all 17 stress cases; C2 and C3 depend on "
                             "assumptions, so pilot them first."),
    ("Compliance vs. ROI: ", "immutable logging (C7) never pays for itself on expected value but is required by PCI DSS "
                             "Req. 10, a good example of when regulation overrides ROI."),
    ("Value of information: ", "escalation probability is the most influential and least-known input, so the "
                               "dashboard's most valuable data to collect is how often incidents escalate."),
])

# --------------------------------------------------------------------------- 4

doc.add_heading("4. How to open the website", level=1)
bullets([
    "Open Terminal and go to the project folder: cd \"Desktop/14817 group project/insider_threat_project\"",
    "First time only: python3 -m venv .venv  then  source .venv/bin/activate  then  pip install -r requirements.txt",
    "Every time: source .venv/bin/activate  then  streamlit run app.py",
    "Your browser opens http://localhost:8501. Leave the Terminal window open while you use it; press Ctrl+C to stop.",
    "Optional: pytest -q runs the 13 checks; python scripts/export_results.py refreshes results/summary.md.",
], style_name="List Number")
para("Tip: numbers in this guide use the default settings (10,000 trials, seed 14817, recommended controls). "
     "If a slider has been moved, refresh the browser page to get back to the defaults.", italic=True, color=GREY)

# --------------------------------------------------------------------------- 5

doc.add_heading("5. Website walkthrough", level=1)
para("Red numbers on each screenshot match the numbered explanations below it.")

doc.add_heading("5.1 Landing view (Dashboard tab)", level=2)
figure("01_overview", "Figure 1. Company-wide landing view")
callouts([
    ("Department view drop-down", "Choose Company-wide, a response team, or a business unit. Every number on every tab "
                                  "re-calculates for that department."),
    ("Controls to deploy", "The controls currently switched on. Recommended loads the best portfolio; Clear removes all "
                           "controls so you can see today's (inherent) risk."),
    ("Model assumptions and Risk appetite", "Expand to change the benchmark, loss sizes, control effectiveness and costs, "
                                            "or to set the board's tolerance (default: at most 5% chance of a $100M+ year)."),
    ("KPI strip", "Expected loss per year, the range covering 80% of years (P10–P90), reports this quarter, residual loss "
                  "after the selected controls, and ROSI (return on security investment)."),
    ("Tabs", "Six views: Dashboard, Monte Carlo, Controls & ROI, Sensitivity, Report intake, Methodology & sources."),
    ("Expected loss by scenario", "Grey = today, blue = with the selected controls, for each insider scenario."),
    ("Recommended controls for this view", "Ranked by how much loss each removes here, with its NIST 800-53 ID, CSF function and "
                                           "regulation. Pills show deployed, in optimal portfolio, or outside optimal portfolio."),
])

doc.add_heading("5.2 Choosing a department", level=2)
figure("02_department_dropdown", "Figure 2. The department drop-down", width=4.2)
callouts([
    ("Three kinds of view", "Company-wide; Response teams (Security, IT, Legal, HR, Finance, Insider risk team) = who "
                            "receives the report; Business units (Customer support, Engineering, Finance and treasury, "
                            "Human resources, Operations, Sales and marketing, Compliance and risk) = where the insider works. "
                            "Business units add up exactly to the company total; response teams overlap because one report "
                            "goes to several teams."),
])
figure("04_customer_support_view", "Figure 3. Business unit · Customer support selected")
callouts([
    ("Selected department", "The page title and every chart now refer to Customer support."),
    ("Department KPIs", "$22.4M of the company's ~$40M sits here. Because control costs are company-wide, the last box "
                        "shows loss avoided instead of ROSI."),
    ("Scenario mix", "Almost all of it is bribed data exfiltration ($19.5M)."),
    ("Department's best controls", "BPO personnel security (PS-7) ranks first here but is outside the company-optimal "
                                   "portfolio: ticket-scoped access plus fraud friction already remove most of the same loss more "
                                   "cheaply. The pill makes that trade-off visible."),
])

doc.add_heading("5.3 Risk appetite and where the risk sits", level=2)
figure("03_appetite_heatmap", "Figure 4. Lower half of the Dashboard tab")
callouts([
    ("Risk appetite check", "Chance of a year above the board's threshold, today vs. with controls, and a pass/fail."),
    ("Inherent / Residual switch", "Show the heat map before or after the selected controls."),
    ("Heat map", "Expected loss for every business unit × scenario; the darkest cell is where to act first."),
    ("Response-team exposure", "How much risk lands in each team's queue."),
    ("Executive brief", "Downloads a one-page summary of the current view for the report or an email."),
])

doc.add_heading("5.4 Monte Carlo tab (Part 3 results)", level=2)
figure("05_monte_carlo", "Figure 5. Simulation results")
callouts([
    ("Loss distribution", "10,000 simulated years on a log scale. The right-hand hump is the rare escalation year "
                          "(extortion, mass scams, regulators)."),
    ("Loss exceedance curve", "Chance (y) that a year's loss exceeds x. The red X is the board appetite; the orange "
                              "lines are Coinbase's 8-K estimate and the actual FY2025 loss."),
    ("Tail statistics", "Average, median, 1-in-20 and 1-in-100 years, and TVaR (average of the worst 5% of years)."),
    ("What drives the tail", "Bribed exfiltration is 57% of the average but about 92% of the worst years."),
    ("Back-test", "Compares the model to the real 2025 breach without being fitted to it (company-wide view only)."),
])

doc.add_heading("5.5 Controls & ROI tab", level=2)
figure("06_controls_portfolio", "Figure 6. Choosing a control portfolio")
callouts([
    ("Objective", "Maximize net benefit, find the cheapest portfolio that meets the risk appetite, or the best "
                  "portfolio within a budget (a slider appears)."),
    ("Result", "Cost, net benefit and tail probability of the portfolio the objective picks."),
    ("Deploy this portfolio", "Switches those controls on in the sidebar; every tab updates."),
    ("Frontier chart", "Each dot is one of the 1,024 combinations. Green = within appetite, blue line = best possible "
                       "for each budget, star = currently selected, diamond = objective's pick. Points below the red "
                       "line pay for themselves."),
])
figure("07_control_catalog", "Figure 7. Control catalog and scenario effects")
callouts([
    ("Control catalog", "Cost, loss avoided alone, our modeled % vs. the Ponemon benchmark %, marginal value given the "
                        "other selected controls, plus NIST 800-53, CSF 2.0, regulation and the gap it closes."),
    ("Scenario effect", "How much each scenario's loss falls with the selected controls."),
])

doc.add_heading("5.6 Sensitivity tab", level=2)
figure("08_sensitivity", "Figure 8. Tornado chart")
callouts([
    ("Output to stress-test", "Today's loss, loss after controls, or net benefit of the selected controls."),
    ("Tornado", "Each bar moves one input from the low to the high end of its range; the longest bar matters most."),
    ("What would change our answer", "Names the input with the highest value of better information."),
])
figure("09_robustness", "Figure 9. Is the recommendation robust?")
callouts([
    ("Stability chart", "Share of 17 stress cases in which each control is in the best portfolio."),
    ("Interpretation", "Core = no-regret; swing = pilot first; never optimal = justify only by regulation or appetite."),
])

doc.add_heading("5.7 Report intake tab (Parts 1–2, live)", level=2)
figure("10_intake_form", "Figure 10. Submitting a new report", width=5.6)
callouts([
    ("Starting numbers", "Note the expected loss ($40.3M) before submitting."),
    ("Web form", "Same fields as our department form, plus the analyst's incident type (A) and impact categories (C)."),
    ("Submit report", "The report is categorized, routed and fed into the model immediately (session only; the "
                      "original data files are not changed)."),
])
figure("11_intake_result", "Figure 11. What happens after submitting", width=5.8)
callouts([
    ("Confirmation", "Shows who it was routed to, whether it opened a new campaign or joined an existing one, and how "
                     "company expected loss moved (here $40.3M → $48.4M for a new Operations campaign)."),
    ("Categorized reports", "Every report with the A/B/C/D labels: incident type, CIA property and severity, FAIR loss "
                            "forms, credibility, records, days to report, campaign and routing."),
    ("Linked campaigns", "What the frequency model actually counts. IR-0001, -0002 and -0008 are one bribery ring, so "
                         "it is counted once, not three times."),
])

doc.add_heading("5.8 Methodology & sources tab", level=2)
figure("12_methodology", "Figure 12. How the numbers are produced")
callouts([
    ("Pipeline", "Report → Categorize → Quantify → Dashboard, with new reports feeding back into the estimate."),
    ("FAIR ontology", "Which FAIR factor each input feeds and its source ID (B-numbers refer to data/benchmarks.csv)."),
    ("Bayesian update", "Prior, observed and updated frequency per scenario. The credibility factor (0.15) shows how far "
                        "our own reports move the estimate away from the Ponemon benchmark."),
])
para("Further down this tab: calibration against Ponemon/IBM, every scenario parameter with its basis, the full "
     "cited-statistics table with links, and the limitations list.")

# --------------------------------------------------------------------------- 6

doc.add_heading("6. Three-minute live demo for the presentation", level=1)
bullets([
    ("Company-wide: ", "\"Expected loss is $40M a year, but the 1-in-20 year is $249M, and Coinbase's real $345M "
                       "loss sits on our curve.\" Show the Monte Carlo tab."),
    ("Drop-down → Business unit · Customer support: ", "\"$22M of it is here, almost all bribed exfiltration.\""),
    ("Clear, then Recommended: ", "residual loss falls to about $8M; ROSI is about 330%."),
    ("Controls & ROI → Cheapest within appetite, appetite set to 1%: ", "\"Only insurance gets there; that's a board decision.\""),
    ("Report intake → submit a confirmed Operations contractor exfiltration: ", "expected loss jumps about $8M. Submit the "
     "same for Customer support BPO staff: it links to the existing ring and does not double-count."),
    ("Sensitivity: ", "\"Even at 8% escalation the six core controls stay optimal.\""),
], style_name="List Number")

# --------------------------------------------------------------------------- 7

doc.add_heading("7. Questions the professor may ask, and our answers", level=1)
table(["Question", "Answer"], [
    ["Where do your frequencies come from?",
     "Ponemon/DTEX 2026 (6.3 malicious incidents per org per year) as a prior, updated with our credibility-weighted "
     "reports via a Gamma-Poisson model. The credibility factor (0.15) shows how much our 63 days of data count."],
    ["Ten reports is a tiny sample.",
     "That is why we use a Bayesian prior rather than the raw rate (which would be 30/yr). The estimate moves toward "
     "our data automatically as reports accumulate."],
    ["How do you avoid double counting?",
     "Campaign linking (one ring = one event), FAIR primary vs. secondary loss forms, and multiplicative stacking of "
     "control effects so overlapping controls never exceed 100%."],
    ["Why trust the loss sizes?",
     "Ranges are anchored on Ponemon costs and Coinbase's 8-K/10-K; the model reproduces the real $345M event at the "
     "85th percentile without being fitted to it."],
    ["What is the weakest assumption?",
     "Escalation probability. The tornado shows it is the most influential input, so we tested 1%–8% and showed the "
     "core recommendation does not change."],
    ["Are your control effects realistic?",
     "Each is kept at or below its Ponemon benchmark (e.g., PAM: 16% modeled vs. 31% benchmark), because Ponemon "
     "reports associations, not causal effects."],
    ["Why not deploy everything?",
     "The frontier flattens after about $8M/yr; extra spend buys less than a dollar of loss reduction per dollar."],
], widths=[2.0, 4.7], font=9)

# --------------------------------------------------------------------------- 8

doc.add_heading("8. Before we submit", level=1)
bullets([
    "Confirm the NYDFS 2023 Coinbase penalty ($50M) used as an anchor for privileged-abuse secondary loss.",
    "Escalation probability, report credibility weights, control effects and control costs are team estimates. They "
    "are labeled in the data files and app; say so in the report.",
    "report_draft.md and presentation_outline.md still describe the old generic bank; use docs/part3_quantification.md "
    "and docs/part4_dashboard_design.md for Parts 3 and 4 instead.",
    "Limitations to state: small sample, one anchor event for secondary loss, scenarios simulated independently, "
    "insurance modeled as a proportional reduction.",
    "Quote numbers from results/summary.md so the slides, report and dashboard always match.",
])

doc.save(OUT)
print("Wrote", OUT)

"""Build Amy's Parts 3-4 Summary and Dashboard Guide (Word).

Usage:  python scripts/build_guide_docx.py
Needs:  pip install python-docx; screenshots from scripts/capture_screenshots.py
Writes: ../Amy's Parts 3-4 Summary and Dashboard Guide.docx
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
OUT = ROOT.parent / "Amy's Parts 3-4 Summary and Dashboard Guide.docx"
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
    path = SHOTS / f"{name}.png"
    if not path.exists():
        para(f"[Screenshot placeholder: {name}.png — re-run scripts/capture_screenshots.py]", italic=True, color=GREY)
        return
    doc.add_picture(str(path), width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph()
    r = p.add_run(caption)
    r.italic = True
    r.font.size = Pt(9)
    r.font.color.rgb = GREY
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER


def callouts(items):
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
r = t.add_run("Amy’s Parts 3 & 4: Quantification and Dashboard Guide")
r.bold = True
r.font.size = Pt(20)
r.font.color.rgb = BLUE
s = doc.add_paragraph()
s.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = s.add_run(
    "How the website works, how to read it, and why the design over-fulfills Milestone 1\n"
    "CMU 14-817 Cyber Risk Modeling · Team 16 (Dheya, Marie, Amy) · Coinbase · Scenario 2"
)
r.font.size = Pt(11)
r.font.color.rgb = GREY

# --------------------------------------------------------------------------- 1

doc.add_heading("1. At a glance", level=1)
para(
    "Part 3 (Quantify) and Part 4 (Dashboard) now run on Dheya’s synthetic insider-incident history. "
    "The website loads only columns A–M from synthetic_insider_incidents.xlsx (incident attributes). "
    "USD loss columns N–T are intentionally excluded so synthetic dollars never become fake “ground truth.” "
    "FAIR loss magnitude still comes from cited Ponemon benchmarks and Coinbase SEC filings. "
    "A single department drop-down re-scopes every KPI, chart, and control recommendation."
)
table(["Result (base case, 10,000 simulated years)", "Today (inherent)", "With recommended controls"], [
    ["Expected annual loss", "$96.8M", "$11.0M"],
    ["Typical bad year (1-in-20, P95)", "$381M", "$38.5M"],
    ["Chance of a $100M+ year", "22.0%", "3.3%"],
    ["Recommended controls", "–", "C1, C2, C3, C4, C5, C6, C8, C9"],
    ["Annual cost / net benefit / ROSI", "–", "$10.6M / $73.9M / 697%"],
    ["Data feeding the app", "500 incidents · cols A–M only · 93 linked campaigns · ~5 years", ""],
], widths=[3.2, 1.6, 1.9])

# --------------------------------------------------------------------------- 2

doc.add_heading("2. Data the website uses (and does not use)", level=1)
doc.add_heading("2.1 Columns A–M only", level=2)
para(
    "Per project decision, the web app imports only the first thirteen fields of the synthetic workbook. "
    "Dollar columns are kept out of the product so Part 3 can stay auditable against external sources."
)
table(["Col", "Field", "Role in the model"], [
    ["A", "incident_id", "Primary key / report id"],
    ["B", "incident_date", "Event date → observation window for LEF"],
    ["C", "incident_type", "Insider class → FAIR scenario mapping"],
    ["D", "business_line", "Maps onto Coinbase business-unit views"],
    ["E", "insider_role", "Subject type and access level"],
    ["F", "work_arrangement", "Location (remote / on-site / hybrid)"],
    ["G", "records_exposed", "Exact record count (quant metric D)"],
    ["H", "days_to_detect", "Detection lag (quant metric D)"],
    ["I", "detection_method", "Evidence proxy → credibility weight"],
    ["J", "days_to_contain", "Containment speed (leading indicator)"],
    ["K", "prior_warning_signs", "Warning-sign count (leading indicator)"],
    ["L", "motivation", "Motivation → scenario / intent mapping"],
    ["M", "primary_impact_category", "Pollmeier impact class → FAIR loss forms (C)"],
], widths=[0.6, 2.2, 3.9], font=9)
para(
    "Excluded from the website: regulatory_usd, customer_usd, media_usd, response_usd, "
    "cost_of_capital_usd, forensic_usd, total_loss_usd. Rebuild with: python scripts/import_synthetic.py"
)

doc.add_heading("2.2 Before vs. after this upgrade", level=2)
table(["Area", "Before", "After"], [
    ["Data", "10 illustrative web-form rows",
     "500 synthetic incidents (A–M) + Marie’s 22 cited benchmarks (B01–B22)"],
    ["Company", "Generic / early Coinbase mock",
     "Coinbase Scenario 2, anchored on the 2024–25 bribed-support-agent event"],
    ["Frequency", "Tiny sample + strong prior",
     "Bayesian Gamma-Poisson: Ponemon 6.3/yr prior + 93 credibility-weighted campaigns over ~5 years (Z ≈ 0.83)"],
    ["Loss size", "Lognormal ranges only",
     "FAIR primary + secondary (SLEF × Coinbase-scale $180M–$400M SLM); USD columns not used as inputs"],
    ["Departments", "Drop-down over thin sample",
     "Same drop-down; Customer support ~$45M and Operations ~$26M dominate the $97M company total"],
    ["Controls", "10 NIST-mapped controls",
     "Same catalog; optimal portfolio now C1–C6, C8, C9 (adds BPO personnel security C3)"],
], widths=[1.1, 2.2, 3.4], font=9)

doc.add_heading("2.3 Code files Amy owns / maintains", level=2)
table(["File", "Purpose"], [
    ["app.py", "Streamlit dashboard (Part 4)"],
    ["insider_risk/categorize.py", "Part 2 labels, credibility, campaign linking, routing"],
    ["insider_risk/quantify.py", "Part 3: Bayesian LEF, FAIR LM, Monte Carlo"],
    ["insider_risk/controls.py, sensitivity.py", "ROI, optimizer, tornado, robustness"],
    ["insider_risk/data.py", "Loaders; enforces A–M only (drops *_usd)"],
    ["scripts/import_synthetic.py", "Converts A–M → insider_reports.csv"],
    ["scripts/export_results.py", "Regenerates results/summary.md (source of truth for numbers)"],
    ["data/synthetic_incidents_am.csv", "A–M fields only, as shown in the app"],
    ["docs/part3_quantification.md / part4_dashboard_design.md", "Technical write-ups"],
], widths=[2.8, 3.9], font=9)

# --------------------------------------------------------------------------- 3

doc.add_heading("3. Why this targets an outstanding (A) grade", level=1)
para(
    "Simply naming FAIR and NIST earns a B. An A needs creativity, complex problem solving, and at least two "
    "class methodologies applied in depth — plus clear answers to Milestone 1’s posture questions "
    "(assets, obligations, financial impact, gaps, treatment plan, stakeholder/shareholder value)."
)
table(["What earns the A", "How we over-fulfill it"], [
    ["≥ 2 methodologies, applied (not named)",
     "FAIR LEF×LM decomposition + Monte Carlo distributions + NIST 800-53/CSF mapping on every control + Bayesian update"],
    ["Quantify likelihood and impact with evidence",
     "500 A–M incidents → 93 campaigns; prior from Ponemon B14; magnitudes from B03/B11/B15/B18–B20"],
    ["Uncertainty, not a single ALE",
     "Full loss distribution, P95/P99/TVaR, tornado, 17-case recommendation stability"],
    ["Validate",
     "Back-test: Coinbase FY2025 $345.2M sits on the exceedance curve; calibration vs. Ponemon/IBM"],
    ["Residual risk + ROI + transfer",
     "1,024 portfolios, efficient frontier, appetite modes; insurance only when appetite is strict"],
    ["Department heat map / simulation",
     "Live company / response-team / business-unit views; Customer support concentration is visible"],
    ["Compliance depth",
     "Each control cites 800-53 ID, CSF function, and regulation (PCI DSS, GDPR, SOX, NYDFS, SEC)"],
    ["Working product (innovation)",
     "Live intake → categorize → quantify → dashboard; campaign linking prevents double-counting"],
    ["Milestone 1 executive questions",
     "Dashboard KPIs + executive brief download answer financial impact, control gaps, plan cost, and ROSI for shareholders"],
], widths=[2.2, 4.5], font=9)

doc.add_heading("Findings that make the presentation stand out", level=2)
bullets([
    ("Concentration: ",
     "Bribed / colluding exfiltration is ~$77M of the ~$97M expected loss (~80%). Customer support alone is ~$45M."),
    ("Mean vs. tail: ",
     "Median year ~$33M, but the 1-in-20 year is ~$381M. Reporting only an average would mislead the board."),
    ("Risk transfer is a board decision: ",
     "Mitigation can get P($100M+) to ~3%; reaching ~1–2% needs the insurance tower (C10)."),
    ("No-regret controls: ",
     "Core controls stay optimal across stress cases; swing controls should be piloted first."),
    ("Compliance vs. ROI: ",
     "Immutable logging (C7) may not maximize net benefit but is required by PCI DSS Req. 10."),
    ("Value of information: ",
     "SLEF (escalation probability) dominates the tornado — that is the highest-value data to collect next."),
    ("Data hygiene: ",
     "Excluding synthetic USD columns is a methodological strength: magnitudes stay externally cited."),
])

# --------------------------------------------------------------------------- 4

doc.add_heading("4. How to open the website", level=1)
bullets([
    'Open Terminal and go to: cd "Desktop/CRM final project code/cmu-CRM-team16-main"',
    "First time only: python3 -m venv .venv  then  source .venv/bin/activate  then  pip install -r requirements.txt",
    "Import / refresh A–M data: python scripts/import_synthetic.py",
    "Every time: source .venv/bin/activate  then  streamlit run app.py",
    "Browser opens http://localhost:8501. Leave Terminal open; Ctrl+C stops the server.",
    "Optional: pytest -q ; python scripts/export_results.py",
], style_name="List Number")
para(
    "Tip: numbers in this guide use defaults (10,000 trials, seed 14817, recommended controls). "
    "Refresh the browser if sliders were moved.",
    italic=True, color=GREY,
)

# --------------------------------------------------------------------------- 5

doc.add_heading("5. Website walkthrough (how to read the dashboard)", level=1)
para("Red numbers on each screenshot match the numbered explanations below it.")

doc.add_heading("5.1 Landing view (Dashboard tab)", level=2)
figure("01_overview", "Figure 1. Company-wide landing view")
callouts([
    ("Department view drop-down",
     "Choose Company-wide, a response team, or a business unit. Every number re-calculates."),
    ("Controls to deploy",
     "Recommended loads the best portfolio; Clear shows inherent risk."),
    ("Model assumptions and Risk appetite",
     "Change prior weight, loss multipliers, effectiveness, or the board tolerance (default ≤5% chance of a $100M+ year)."),
    ("KPI strip",
     "Expected loss / yr, P10–P90, reports this quarter, residual loss, ROSI (company view)."),
    ("Tabs",
     "Dashboard, Monte Carlo, Controls & ROI, Sensitivity, Report intake, Methodology & sources."),
    ("Expected loss by scenario",
     "Grey = inherent, blue = with selected controls."),
    ("Recommended controls for this view",
     "Ranked by loss removed here, with NIST / CSF / regulation pills."),
])

doc.add_heading("5.2 Choosing a department", level=2)
figure("02_department_dropdown", "Figure 2. The department drop-down", width=4.2)
callouts([
    ("Three kinds of view",
     "Company-wide; Response teams (who receive the report); Business units (where the insider works). "
     "Business units partition the company total; response teams overlap."),
])
figure("04_customer_support_view", "Figure 3. Business unit · Customer support selected")
callouts([
    ("Selected department", "Title and charts now refer to Customer support."),
    ("Department KPIs",
     "About $45M of the ~$97M company exposure sits here; the last box shows loss avoided instead of ROSI."),
    ("Scenario mix", "Dominated by bribed / colluding data exfiltration."),
    ("Department’s best controls",
     "BPO personnel security (C3 / PS-7) ranks high here; pills show whether it is in the company-optimal set."),
])

doc.add_heading("5.3 Risk appetite and where the risk sits", level=2)
figure("03_appetite_heatmap", "Figure 4. Lower half of the Dashboard tab")
callouts([
    ("Risk appetite check", "Chance of a year above the board threshold, inherent vs residual, pass/fail."),
    ("Inherent / Residual switch", "Heat map before or after selected controls."),
    ("Heat map", "Business unit × scenario expected loss — darkest cell = act first."),
    ("Response-team exposure", "How much risk lands in each team’s queue."),
    ("Executive brief", "One-page Markdown download for the report or an email."),
])

doc.add_heading("5.4 Monte Carlo tab", level=2)
figure("05_monte_carlo", "Figure 5. Simulation results")
callouts([
    ("Loss distribution", "10,000 simulated years on a log scale; right hump = rare escalation years."),
    ("Loss exceedance curve",
     "P(loss ≥ x). Board appetite marker; Coinbase 8-K $180M and FY2025 $345M reference lines."),
    ("Tail statistics", "Mean, median, P95, P99, TVaR 95."),
    ("What drives the tail", "Bribed exfiltration dominates both the mean and the worst years."),
    ("Back-test", "Compares the model to the real 2025 breach without fitting to it."),
])

doc.add_heading("5.5 Controls & ROI tab", level=2)
figure("06_controls_portfolio", "Figure 6. Choosing a control portfolio")
callouts([
    ("Objective", "Max net benefit, cheapest within appetite, or best within a budget."),
    ("Result", "Cost, net benefit, and tail probability of the picked portfolio."),
    ("Deploy this portfolio", "Writes those controls into the sidebar; every tab updates."),
    ("Frontier chart",
     "All 1,024 combinations; green = within appetite; star = current; diamond = objective pick."),
])
figure("07_control_catalog", "Figure 7. Control catalog and scenario effects")
callouts([
    ("Control catalog",
     "Cost, standalone value, modeled % vs Ponemon %, marginal net benefit, NIST, CSF, regulation, gap closed."),
    ("Scenario effect", "How each scenario’s ALE falls with the selected controls."),
])

doc.add_heading("5.6 Sensitivity tab", level=2)
figure("08_sensitivity", "Figure 8. Tornado chart")
callouts([
    ("Output to stress-test", "Inherent loss, residual loss, or net benefit."),
    ("Tornado", "Longest bar = highest value of information."),
    ("What would change our answer", "Usually SLEF / escalation probability."),
])
figure("09_robustness", "Figure 9. Is the recommendation robust?")
callouts([
    ("Stability chart", "Share of 17 stress cases where each control is optimal."),
    ("Interpretation", "Core = no-regret; swing = pilot; never-optimal = justify by regulation/appetite."),
])

doc.add_heading("5.7 Report intake tab — what data is / isn’t available", level=2)
figure("10_intake_form", "Figure 10. Synthetic A–M fields + live form", width=5.6)
callouts([
    ("A–M table", "Shows the thirteen synthetic fields the model uses; USD columns are absent by design."),
    ("Live web form", "Optional: submit a new report in-session; it categorizes, routes, and updates LEF."),
    ("What is available",
     "Incident attributes, detection/containment lags, motivation, impact class, mapped FAIR scenario, campaigns."),
    ("What is not available",
     "Synthetic USD loss columns; confirmed real Coinbase case-level PII; unit-level insurance retentions."),
])
figure("11_intake_result", "Figure 11. Categorized log and campaigns", width=5.8)
callouts([
    ("Categorized reports", "A/B/C/D labels, credibility, records, days to detect, campaign, routing."),
    ("Linked campaigns", "What the frequency model actually counts (93 campaigns from 500 rows)."),
])

doc.add_heading("5.8 Methodology & sources tab", level=2)
figure("12_methodology", "Figure 12. How the numbers are produced")
callouts([
    ("Pipeline", "Synthetic A–M → Categorize → Quantify → Dashboard."),
    ("FAIR ontology", "Which FAIR factor each input feeds; B-IDs point to data/benchmarks.csv."),
    ("Bayesian update", "Prior / observed / posterior rates; credibility factor Z ≈ 0.83 with ~5 years of history."),
])

# --------------------------------------------------------------------------- 6

doc.add_heading("6. Dashboard design choices (why it looks this way)", level=1)
bullets([
    ("One composition per job: ",
     "Landing tab answers “where is the risk and are we within appetite?” Monte Carlo answers “how bad can it get?” "
     "Controls answers “what should we buy?” Sensitivity answers “what if we are wrong?”"),
    ("Department drop-down first: ",
     "Insider programs fail when risk is only company-average. Business-unit thinning makes budget ownership real."),
    ("Pills for control status: ",
     "A control can be best for one unit yet outside the company-optimal portfolio — the UI shows that tension."),
    ("Log scales: ",
     "Losses span four orders of magnitude; linear axes hide the escalation hump."),
    ("A–M transparency: ",
     "Methodology tab lists every synthetic field used and every USD field excluded."),
    ("Reproducibility: ",
     "Fixed seed 14817 and trial count are shown; results/summary.md regenerates every quoted figure."),
])

# --------------------------------------------------------------------------- 7

doc.add_heading("7. Three-to-four-minute live demo script (Amy)", level=1)
bullets([
    ("0:00–0:40 Company-wide: ",
     "“Expected loss is about $97M a year, but the 1-in-20 year is ~$381M. Coinbase’s real $345M sits on our curve.” "
     "Point to Monte Carlo exceedance."),
    ("0:40–1:20 Department: ",
     "Drop-down → Business unit · Customer support. “About $45M of it lives here — mostly bribed exfiltration.”"),
    ("1:20–2:00 Controls: ",
     "Clear, then Recommended. Residual falls to ~$11M; ROSI ~700%. Mention C3 now enters the optimal set."),
    ("2:00–2:40 Appetite / transfer: ",
     "Controls & ROI → cheapest within appetite at 2%. “Insurance appears; that is a board decision.”"),
    ("2:40–3:20 Data available / not: ",
     "Report intake → A–M table. “We use incident attributes only — not the synthetic USD columns.”"),
    ("3:20–3:50 Design why: ",
     "Sensitivity → SLEF bar. “We designed for decisions under uncertainty, not a single ALE.”"),
], style_name="List Number")

# --------------------------------------------------------------------------- 8

doc.add_heading("8. Questions the professor may ask", level=1)
table(["Question", "Answer"], [
    ["Where do frequencies come from?",
     "Ponemon/DTEX 2026 (6.3 malicious/yr) as prior, updated with 93 credibility-weighted campaigns from 500 A–M "
     "incidents (~5 years). Z ≈ 0.83."],
    ["Why exclude the USD columns?",
     "So the model is not circular. Magnitudes stay anchored on cited benchmarks and Coinbase SEC filings."],
    ["How do you avoid double counting?",
     "Campaign linking; FAIR primary vs secondary forms; multiplicative control stacking capped below 100%."],
    ["Why trust the loss sizes?",
     "Ranges from Ponemon + Coinbase 8-K/10-K; the $345M actual sits on the modeled escalation range."],
    ["What is the weakest assumption?",
     "SLEF. Tornado shows it; we test 1%–8% and check recommendation stability."],
    ["Why should shareholders care?",
     "Residual ALE falls by ~$86M for ~$11M spend (ROSI ~700%); tail P($100M+) falls from 22% to 3.3%."],
], widths=[2.0, 4.7], font=9)

# --------------------------------------------------------------------------- 9

doc.add_heading("9. Before we submit", level=1)
bullets([
    "Quote numbers only from results/summary.md after python scripts/export_results.py.",
    "Say clearly: synthetic A–M history; USD columns excluded; SLEF/control effects are labeled team estimates.",
    "Screenshots: streamlit run app.py then python scripts/capture_screenshots.py.",
    "Pair this guide with Amy’s write-up sections (code + how to interpret) and the 3–4 minute demo pack.",
])

doc.save(OUT)
print("Wrote", OUT)

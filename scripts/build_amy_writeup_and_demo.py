"""Build Amy's write-up report sections + 3–4 minute demo pack (Word).

Writes to the project root (next to the Milestone PDF):
  - Amy Write-Up Report - Parts 3-4.docx
  - Amy Dashboard Demo Pack - Slides and Script.docx
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
OUT_DIR = ROOT.parent
BLUE = RGBColor(0x1F, 0x4E, 0x9A)
GREY = RGBColor(0x59, 0x59, 0x59)


def shade(cell, hex_color):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def setup(doc: Document):
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    for s in doc.sections:
        s.left_margin = s.right_margin = Inches(0.9)
        s.top_margin = s.bottom_margin = Inches(0.8)


def title(doc, text, sub):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(20)
    r.font.color.rgb = BLUE
    s = doc.add_paragraph()
    s.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = s.add_run(sub)
    r.font.size = Pt(11)
    r.font.color.rgb = GREY


def para(doc, text, bold_lead=None, italic=False, space_after=6):
    p = doc.add_paragraph()
    if bold_lead:
        r = p.add_run(bold_lead)
        r.bold = True
    r = p.add_run(text)
    r.italic = italic
    p.paragraph_format.space_after = Pt(space_after)
    return p


def bullets(doc, items, numbered=False):
    style = "List Number" if numbered else "List Bullet"
    for item in items:
        p = doc.add_paragraph(style=style)
        if isinstance(item, tuple):
            p.add_run(item[0]).bold = True
            p.add_run(item[1])
        else:
            p.add_run(item)
        p.paragraph_format.space_after = Pt(2)


def table(doc, header, rows, widths=None, font=9.5):
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
    if widths:
        t.autofit = False
        layout = OxmlElement("w:tblLayout")
        layout.set(qn("w:type"), "fixed")
        t._tbl.tblPr.append(layout)
        for i, w in enumerate(widths):
            t.columns[i].width = Inches(w)
            for row in t.rows:
                row.cells[i].width = Inches(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def figure(doc, name, caption, width=6.4):
    path = SHOTS / f"{name}.png"
    if not path.exists():
        para(doc, f"[Missing screenshot: {name}.png]", italic=True)
        return
    doc.add_picture(str(path), width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph()
    r = p.add_run(caption)
    r.italic = True
    r.font.size = Pt(9)
    r.font.color.rgb = GREY
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER


# =============================================================================
# WRITE-UP
# =============================================================================

def build_writeup():
    doc = Document()
    setup(doc)
    title(
        doc,
        "Amy Write-Up Report — Parts 3 & 4",
        "Code, dashboard design, interpretation, and Milestone 1 supplements\n"
        "CMU 14-817 · Team 16 · Coinbase Scenario 2 · Numbers from results/summary.md",
    )

    doc.add_heading("1. Scope of Amy’s write-up sections", level=1)
    para(
        doc,
        "Per the team’s Write-Up Topic Division, Amy covers: (1) explain and provide the code, "
        "and (2) how to read / interpret the dashboard. This document also supplies the extra "
        "Milestone 1 material that an outstanding submission needs beyond a B-level checklist: "
        "dashboard design rationale, how-to-use guidance, why we designed it this way, how the "
        "product answers the Milestone 1 executive questions (assets, obligations, financial "
        "impact, gaps, treatment plan, shareholder value), and annotated screenshots. "
        "Companion guide: “Amy’s Parts 3-4 Summary and Dashboard Guide.docx”.",
    )

    doc.add_heading("2. Explain + provide the code", level=1)
    doc.add_heading("2.1 Pipeline the code implements", level=2)
    para(
        doc,
        "The product is a reproducible Python pipeline: import A–M synthetic incidents → "
        "categorize into FAIR loss events → quantify with Bayesian LEF × FAIR LM via Monte Carlo → "
        "serve an interactive Streamlit dashboard with control ROI and sensitivity.",
    )
    table(doc, ["Module / script", "What it does"], [
        ["scripts/import_synthetic.py",
         "Reads synthetic_insider_incidents.xlsx columns A–M only; maps to insider_reports.csv; "
         "writes data/synthetic_incidents_am.csv. Drops all *_usd columns."],
        ["insider_risk/data.py",
         "Loaders; load_reports() strips any USD columns if present; load_synthetic_am() for transparency."],
        ["insider_risk/categorize.py",
         "Part 2: scenario mapping, CIA/severity, FAIR loss forms, credibility, exact records_exposed, "
         "campaign linking (90-day), routing suggestions."],
        ["insider_risk/quantify.py",
         "Part 3: Gamma-Poisson frequency posterior, lognormal primary/secondary loss, Monte Carlo, "
         "exceedance, calibration helpers."],
        ["insider_risk/controls.py",
         "Control effects on FAIR factors; 1,024 portfolios; efficient frontier; department recommendations."],
        ["insider_risk/sensitivity.py",
         "Tornado analysis and recommendation-stability across stress cases."],
        ["app.py",
         "Part 4 Streamlit UI: department drop-down, six tabs, live intake form, downloads."],
        ["scripts/export_results.py",
         "Single source of truth: regenerates results/summary.md used in slides and this report."],
        ["tests/test_model.py",
         "Unit tests for A–M-only loading, campaign collapse, partition math, optimizer, Monte Carlo."],
    ], widths=[2.4, 4.3], font=9)

    doc.add_heading("2.2 How to run the code", level=2)
    bullets(doc, [
        'cd "Desktop/CRM final project code/cmu-CRM-team16-main"',
        "python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt",
        "python scripts/import_synthetic.py",
        "streamlit run app.py   → http://localhost:8501",
        "pytest -q",
        "python scripts/export_results.py",
    ], numbered=True)

    doc.add_heading("2.3 Design of the quantification code (why this math)", level=2)
    bullets(doc, [
        ("Bayesian LEF, not raw rates: ",
         "Even with 500 rows, scenario cells differ in density. A Gamma-Poisson prior (Ponemon B14 = 6.3/yr) "
         "regularizes sparse cells while letting ~5 years of history dominate (Z ≈ 0.83)."),
        ("Campaign linking: ",
         "500 attribute rows become 93 loss events so one prolonged bribery pattern is not counted dozens of times."),
        ("FAIR primary + secondary: ",
         "Separates response/replacement costs from rare escalation (extortion, mass scams, regulators) "
         "anchored on Coinbase’s 8-K $180M–$400M band."),
        ("A–M only / no synthetic USD: ",
         "Keeps magnitude externally cited. The website never treats fabricated total_loss_usd as truth."),
        ("Monte Carlo with parameter uncertainty: ",
         "Drawing λ from its posterior each trial (negative binomial) widens the tail honestly."),
        ("Department thinning: ",
         "Business-unit views partition company exposure exactly (unit-tested), so budgets can be owned."),
    ])

    doc.add_heading("3. Dashboard design", level=1)
    para(
        doc,
        "The dashboard is the decision surface for Coinbase’s insider-risk posture. It is deliberately "
        "not a dump of tables: each tab answers one stakeholder question in under a minute.",
    )
    figure(doc, "01_overview", "Figure W1. Company-wide Dashboard tab (landing composition).")
    table(doc, ["Stakeholder", "Question", "Where answered"], [
        ["Board / audit", "Are we within appetite? What is the 1-in-20 year?",
         "Dashboard appetite check; Monte Carlo exceedance"],
        ["CISO / insider-risk lead", "Which controls, in what order, for how much?",
         "Controls & ROI + Recommended button"],
        ["Department head", "How much of this is mine?",
         "Department drop-down + heat map"],
        ["Response team", "What lands in my queue?",
         "Response-team view + intake routing"],
        ["Analyst / auditor", "Where does each number come from?",
         "Methodology & sources; A–M field table"],
        ["Shareholder / finance", "Why fund this?",
         "ROSI, net benefit, residual tail reduction, executive brief download"],
    ], widths=[1.5, 2.4, 2.8], font=9)

    doc.add_heading("3.1 Why we designed it this way", level=2)
    bullets(doc, [
        ("Department-first navigation: ",
         "Insider risk is not uniform. Customer support (~$45M) and Operations (~$26M) dominate; "
         "a company-only average would hide the treatment priority."),
        ("Status pills on controls: ",
         "A control can be locally best yet globally suboptimal once overlapping controls are selected. "
         "Pills make that trade-off visible instead of hiding it."),
        ("Log-scale Monte Carlo: ",
         "Losses span ~$0.1M to ~$1B; linear axes erase the escalation hump the board must see."),
        ("Appetite as a first-class control: ",
         "“Cheapest portfolio within appetite” turns cyber into a board risk-tolerance decision, "
         "including when only insurance (C10) closes the gap."),
        ("Transparency tab for A–M: ",
         "We show exactly which synthetic fields are used and which USD fields are excluded — "
         "methodological honesty that over-fulfills “use real / documented evidence.”"),
        ("Live intake loop: ",
         "Even though a full production webform was deferred (Marie’s future work), the PoC form "
         "proves the pipeline is closed-loop: new evidence updates the posterior immediately."),
    ])

    doc.add_heading("4. How to use / how to read the dashboard", level=1)
    para(
        doc,
        "Full annotated walkthrough with red callouts is in the companion Dashboard Guide. "
        "This section is the report-ready interpretation narrative.",
    )

    doc.add_heading("4.1 Reading the KPI strip", level=2)
    figure(doc, "04_customer_support_view", "Figure W2. Department view — interpret KPIs for Customer support.")
    bullets(doc, [
        ("Expected loss / yr: ", "Mean of the simulated annual loss distribution (inherent)."),
        ("P10–P90: ", "Range covering 80% of ordinary years — not the crisis year."),
        ("Reports this qtr: ", "Operational volume for the selected view."),
        ("Residual loss / yr: ", "Mean after sidebar controls; delta shows % reduction."),
        ("ROSI vs loss avoided: ",
         "ROSI only in company-wide view (control costs are company-wide). Department views show loss avoided."),
    ])

    doc.add_heading("4.2 Reading Monte Carlo", level=2)
    figure(doc, "05_monte_carlo", "Figure W3. Loss distribution and exceedance curve.")
    bullets(doc, [
        ("Two humps: ", "Ordinary primary-loss years vs rare secondary-escalation years."),
        ("Exceedance curve: ",
         "Y = probability a year’s loss exceeds X. Board appetite is the red marker; "
         "orange lines mark Coinbase 8-K $180M and FY2025 actual $345M."),
        ("Interpretation for Milestone 1 financial impact: ",
         "Inherent P($100M+) ≈ 22%; with recommended controls ≈ 3.3%. Shareholders should care because "
         "tail years threaten earnings, disclosure (SEC 8-K), and franchise value."),
    ])

    doc.add_heading("4.3 Reading Controls & ROI", level=2)
    figure(doc, "06_controls_portfolio", "Figure W4. Efficient frontier of 1,024 control portfolios.")
    bullets(doc, [
        ("Recommended portfolio: ",
         "C1, C2, C3, C4, C5, C6, C8, C9 · $10.6M/yr · net benefit $73.9M · ROSI 697%."),
        ("Frontier flattening: ",
         "After ~$8–11M/yr, extra spend buys less than a dollar of expected-loss reduction — "
         "the economic case for selective transfer (insurance) rather than buying everything."),
        ("Compliance override: ",
         "C7 (immutable logging) may not maximize net benefit but maps to PCI DSS Req. 10 / SOX ITGC — "
         "regulation can correctly override pure ROI."),
    ])

    doc.add_heading("4.4 Reading Sensitivity", level=2)
    figure(doc, "08_sensitivity", "Figure W5. Tornado — SLEF dominates.")
    para(
        doc,
        "Escalation probability (SLEF) moves inherent expected loss from roughly $50M to $208M in the "
        "tested range. That is the highest value-of-information finding: collect escalation outcomes "
        "from real incidents before refining secondary-loss assumptions.",
    )

    doc.add_heading("4.5 What data is available vs not available", level=2)
    figure(doc, "10_intake_form", "Figure W6. Report intake — A–M fields visible; USD columns absent.")
    table(doc, ["Available in the website", "Not available (by design or data gap)"], [
        ["500 synthetic incidents, columns A–M", "Synthetic USD loss columns N–T"],
        ["Mapped FAIR scenarios S1–S4 + campaigns", "Confirmed real Coinbase case-level PII / ticket IDs"],
        ["Cited benchmarks B01–B22 with URLs", "Bank-sector-only frequency (Ponemon is cross-industry)"],
        ["NIST 800-53 / CSF / regulation per control", "Exact insurance retention/limit schedule"],
        ["Live PoC intake form (session only)", "Production department webform attached to SSO (future work)"],
        ["Department heat map + response-team load", "Full OT device inventory dollar valuations"],
    ], widths=[3.35, 3.35], font=9)

    doc.add_heading("5. Milestone 1 supplements answered by Parts 3–4", level=1)
    para(
        doc,
        "Milestone 1 asks for an executive summary of posture and strategy. Dheya and Marie cover "
        "scenario selection, the 2024–25 incident narrative, and data sources. Amy’s product makes "
        "the following Milestone items concrete and quantitative:",
    )
    table(doc, ["Milestone 1 ask", "How the dashboard / code over-fulfills it"], [
        ["Digital assets & how cyber hits them",
         "Scenarios encode customer records, privileged access, payment/limit integrity, credentials; "
         "heat map shows which business units hold the exposure."],
        ["Services / obligations / legal-regulatory",
         "Secondary loss + Legal/Compliance routing; controls map to GDPR, PCI DSS, SOX, NYDFS, SEC."],
        ["Revenue / financial outlook",
         "Full ALE distribution, P95/P99/TVaR, exceedance vs $100M / $180M / $345M; executive brief download."],
        ["Existing security & gaps",
         "Control catalog lists gap_addressed per control (vendor oversight, shared admin, logging, etc.)."],
        ["Plan, costs, stakeholder & shareholder benefits",
         "Recommended portfolio cost $10.6M, net benefit $73.9M, ROSI 697%; residual P($100M+) 3.3%; "
         "department views show who benefits operationally."],
    ], widths=[2.2, 4.5], font=9)

    doc.add_heading("6. Base-case numbers to quote (do not invent)", level=1)
    para(
        doc,
        "Always re-run python scripts/export_results.py and quote results/summary.md. Current base case:",
    )
    bullets(doc, [
        "500 A–M incidents → 93 campaigns over 1,803 days (~5 years).",
        "Inherent expected annual loss $96.8M; residual $11.0M with recommended controls.",
        "P95 $380.7M → $38.5M; P($100M+) 22.0% → 3.3%.",
        "S1 bribed exfiltration ~$77.2M inherent; Customer support ~$45.3M; Operations ~$25.7M.",
        "Recommended: C1, C2, C3, C4, C5, C6, C8, C9 · $10.6M · net benefit $73.9M · ROSI 697%.",
    ])

    doc.add_heading("7. Cross-references", level=1)
    bullets(doc, [
        "Amy’s Parts 3-4 Summary and Dashboard Guide.docx — annotated screenshots + how-to.",
        "Amy Dashboard Demo Pack — Slides and Script.docx — 3–4 minute presentation.",
        "docs/part3_quantification.md — technical Part 3.",
        "docs/part4_dashboard_design.md — technical Part 4.",
        "Marie: data sources, FAIR mapping, limitations, future webform, references.",
        "Dheya: Coinbase / Scenario 2 rationale, 2024 insider impact, synthetic field keep/drop decisions.",
    ])

    out = OUT_DIR / "Amy Write-Up Report - Parts 3-4.docx"
    doc.save(out)
    print("Wrote", out)


# =============================================================================
# DEMO PACK
# =============================================================================

def build_demo():
    doc = Document()
    setup(doc)
    title(
        doc,
        "Amy Dashboard Demo Pack (3–4 minutes)",
        "Slide bullet points + screenshots + spoken script\n"
        "CMU 14-817 · Team 16 · Aim: outstanding (A) — decisions, not just charts",
    )

    doc.add_heading("Timing map (≈ 3:45)", level=1)
    table(doc, ["Clock", "Beat", "Slide / screen"], [
        ["0:00–0:40", "Company risk + tail vs Coinbase actual", "Slide 1 + Monte Carlo"],
        ["0:40–1:20", "Department concentration", "Slide 2 + Customer support view"],
        ["1:20–2:00", "Controls, cost, ROSI", "Slide 3 + Recommended portfolio"],
        ["2:00–2:40", "Appetite / insurance = board decision", "Slide 4 + Controls & ROI"],
        ["2:40–3:20", "What data is / isn’t available (A–M)", "Slide 5 + Intake A–M table"],
        ["3:20–3:45", "Why designed this way + close", "Slide 6 + Sensitivity tornado"],
    ], widths=[1.2, 2.8, 2.7], font=9)

    # ----- slides -----
    doc.add_heading("Slide bullets (copy onto deck)", level=1)

    doc.add_heading("Slide 1 — Company posture (Part 3 headline)", level=2)
    bullets(doc, [
        "Coinbase insider risk quantified with FAIR + Monte Carlo (10,000 years)",
        "Data: 500 synthetic incidents · columns A–M only · 93 linked campaigns",
        "Inherent expected loss ≈ $97M / yr · 1-in-20 year ≈ $381M",
        "Coinbase FY2025 actual $345M sits on our exceedance curve (back-test)",
        "Message: averages hide the crisis year the board must underwrite",
    ])
    figure(doc, "05_monte_carlo", "Slide 1 visual — Monte Carlo / exceedance.")

    doc.add_heading("Slide 2 — Where the risk sits", level=2)
    bullets(doc, [
        "One drop-down re-scopes every KPI: company · response team · business unit",
        "Customer support ≈ $45M · Operations ≈ $26M of inherent exposure",
        "~80% of expected loss is bribed / colluding data exfiltration (S1)",
        "Business units partition the total (no double-count); response teams overlap",
        "Design choice: make budget owners see their own risk in one click",
    ])
    figure(doc, "04_customer_support_view", "Slide 2 visual — Customer support department view.")

    doc.add_heading("Slide 3 — Treatment plan & ROI", level=2)
    bullets(doc, [
        "Recommended portfolio: C1–C6, C8, C9 (NIST 800-53 + CSF mapped)",
        "Annual cost $10.6M · loss avoided ~$85M · net benefit $73.9M · ROSI ~700%",
        "Residual expected loss ≈ $11M · P($100M+) 22% → 3.3%",
        "Shareholder takeaway: protects earnings power and disclosure risk, not just “security spend”",
        "Compliance note: some controls (e.g., immutable logging) justified by PCI/SOX even if ROI is weak",
    ])
    figure(doc, "06_controls_portfolio", "Slide 3 visual — portfolio frontier.")

    doc.add_heading("Slide 4 — Risk appetite & transfer", level=2)
    bullets(doc, [
        "Objective modes: max net benefit · cheapest within appetite · budget-constrained",
        "Strict appetite (~1–2% chance of $100M+ year) pulls in insurance tower (C10)",
        "That is a board decision, not a SOC ticket",
        "Over-fulfillment: residual risk + transfer, not only “buy more controls”",
    ])
    figure(doc, "03_appetite_heatmap", "Slide 4 visual — appetite + heat map.")

    doc.add_heading("Slide 5 — What data is / isn’t available", level=2)
    bullets(doc, [
        "IS available: A–M attributes (type, line, role, records, detect/contain, motivation, impact class)",
        "IS available: cited benchmarks B01–B22; Coinbase 8-K/10-K anchors",
        "NOT loaded: synthetic USD columns (N–T) — avoids circular “fake precision”",
        "NOT available yet: production SSO webform (Marie future work); unit-level insurance layers",
        "Honesty about gaps is part of the A — we show limitations in the Methodology tab",
    ])
    figure(doc, "10_intake_form", "Slide 5 visual — A–M intake / availability.")

    doc.add_heading("Slide 6 — Design choices & uncertainty", level=2)
    bullets(doc, [
        "Designed for decisions under uncertainty: tornado + 17-case stability, not one ALE",
        "Highest value of information: escalation probability (SLEF)",
        "Features we picked on purpose: department lens, pills, log scales, live intake loop",
        "Features we deferred: full webform attach (time) — PoC form proves the path",
        "Close: “This is a working risk product Coinbase leaders can operate, not a slideware model.”",
    ])
    figure(doc, "08_sensitivity", "Slide 6 visual — sensitivity tornado.")

    # ----- script -----
    doc.add_heading("Spoken script (≈ 3:45 — speak naturally; do not rush)", level=1)

    doc.add_heading("Beat 1 — Company (≈ 40s)", level=2)
    para(
        doc,
        "“I’ll demo the working dashboard that turns our insider scenario into decisions. "
        "Company-wide, expected annual loss is about ninety-seven million dollars. "
        "But look at the Monte Carlo tab: the one-in-twenty year is about three hundred eighty-one million — "
        "and Coinbase’s real three hundred forty-five million dollar loss sits right on this exceedance curve. "
        "If we only reported an average, we would mislead the board.”",
        italic=True,
    )

    doc.add_heading("Beat 2 — Department (≈ 40s)", level=2)
    para(
        doc,
        "“I designed a single department drop-down so every number re-scopes. "
        "Switch to Business unit · Customer support: about forty-five million of the exposure lives here, "
        "almost all bribed or colluding data exfiltration — the same pattern as the 2024–25 case. "
        "Operations is next at about twenty-six million. Business-unit views add up to the company total, "
        "so owners can actually budget against their slice.”",
        italic=True,
    )

    doc.add_heading("Beat 3 — Controls / ROSI (≈ 40s)", level=2)
    para(
        doc,
        "“Clear the controls, then hit Recommended. Residual expected loss falls to about eleven million. "
        "Eight controls — each mapped to NIST 800-53 and CSF — cost ten-point-six million a year and "
        "deliver about seventy-four million in net benefit, roughly a seven-hundred percent ROSI. "
        "That is the shareholder story: this is not security theater; it protects earnings and disclosure risk.”",
        italic=True,
    )

    doc.add_heading("Beat 4 — Appetite (≈ 40s)", level=2)
    para(
        doc,
        "“On Controls and ROI, if the board wants the chance of a hundred-million-dollar year closer to "
        "one or two percent, mitigation alone is not enough — the optimizer pulls in the insurance tower. "
        "We surface that as a board appetite decision, not something buried in a SOC backlog.”",
        italic=True,
    )

    doc.add_heading("Beat 5 — Data available / not (≈ 40s)", level=2)
    para(
        doc,
        "“Report intake shows exactly what feeds the model: Dheya’s synthetic history, columns A through M only — "
        "incident type, business line, role, records exposed, detection and containment, motivation, impact class. "
        "We deliberately do not load the synthetic USD loss columns, so dollar magnitude stays tied to "
        "Ponemon and Coinbase SEC filings. What we do not have yet is a production webform wired to SSO — "
        "Marie covers that as future work — but the live PoC form shows the loop is ready.”",
        italic=True,
    )

    doc.add_heading("Beat 6 — Design why + close (≈ 25s)", level=2)
    para(
        doc,
        "“Finally, Sensitivity: escalation probability dominates the tornado. We designed the product for "
        "uncertainty — tornado plus seventeen stress cases — so recommendations stay honest when assumptions move. "
        "That is the dashboard: a working FAIR and Monte Carlo decision system for Coinbase insider risk.”",
        italic=True,
    )

    doc.add_heading("Live click path (rehearse once)", level=1)
    bullets(doc, [
        "Open company-wide Dashboard → glance KPIs → Monte Carlo tab (Beat 1)",
        "Sidebar → Business unit · Customer support (Beat 2)",
        "Clear → Recommended; note residual + ROSI (Beat 3)",
        "Controls & ROI → cheapest within appetite / mention insurance (Beat 4)",
        "Report intake → point at A–M table; say USD excluded (Beat 5)",
        "Sensitivity → longest tornado bar = SLEF; close (Beat 6)",
    ], numbered=True)

    doc.add_heading("Professor Q-ready one-liners", level=1)
    bullets(doc, [
        ("“Is the data real?” ",
         "“Synthetic A–M attributes + cited benchmarks; USD columns excluded on purpose.”"),
        ("“Why FAIR and Monte Carlo?” ",
         "“FAIR structures LEF×LM; Monte Carlo shows the board the tail, not one ALE.”"),
        ("“Why should shareholders care?” ",
         "“~$74M net benefit / yr and tail probability of a $100M year down from 22% to 3%.”"),
        ("“What’s weakest?” ",
         "“SLEF — and the tornado proves we know that.”"),
    ])

    out = OUT_DIR / "Amy Dashboard Demo Pack - Slides and Script.docx"
    doc.save(out)
    print("Wrote", out)


if __name__ == "__main__":
    build_writeup()
    build_demo()

"""Capture annotated dashboard screenshots for the user guide.

Usage:  streamlit run app.py   (in another terminal)
        python scripts/capture_screenshots.py
Needs:  pip install playwright   (uses the installed Google Chrome)
Writes: docs/screenshots/*.png  - numbered red callouts match the guide's explanations.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parents[1] / "docs" / "screenshots"
URL = "http://localhost:8501"
RED = (239, 68, 68)
FONT = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)


def box(locator):
    b = locator.bounding_box()
    return None if b is None else (b["x"], b["y"], b["x"] + b["width"], b["y"] + b["height"])


def union(boxes):
    boxes = [b for b in boxes if b]
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def annotate(page, name, marks, region=None, pad=18):
    """marks: list of (locator-or-box, number). region: optional fixed crop box."""
    raw = OUT / f"_{name}.png"
    page.screenshot(path=str(raw))
    boxes = [(m if isinstance(m, tuple) else box(m), n) for m, n in marks]
    boxes = [(b, n) for b, n in boxes if b]
    img = Image.open(raw).convert("RGB")
    draw = ImageDraw.Draw(img)
    for (x0, y0, x1, y1), n in boxes:
        draw.rounded_rectangle((x0 - 5, y0 - 5, x1 + 5, y1 + 5), radius=8, outline=RED, width=4)
        cx, cy, r = x0 - 5, y0 - 5, 17
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=RED)
        draw.text((cx, cy), str(n), fill="white", font=FONT, anchor="mm")
    if region is None:
        u = union([b for b, _ in boxes])
        region = (max(u[0] - 40, 0), max(u[1] - 40, 0), min(u[2] + pad + 20, img.width), min(u[3] + pad + 20, img.height))
    img.crop(tuple(int(v) for v in region)).save(OUT / f"{name}.png")
    raw.unlink()
    print("saved", name)


def visible(page, selector):
    return page.locator(selector).locator("visible=true")


def open_tab(page, label):
    page.get_by_role("tab", name=label).click()
    page.wait_for_timeout(3500)


def choose(page, label, option):
    page.locator("[data-testid='stSelectbox']").filter(has_text=label).get_by_role("combobox").click()
    page.get_by_role("option", name=option, exact=True).click()
    page.wait_for_timeout(400)


def choose_multi(page, label, option):
    page.locator("[data-testid='stMultiSelect']").filter(has_text=label).get_by_role("combobox").click()
    page.get_by_role("option", name=option, exact=True).click()
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1500, "height": 2500})
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector("text=Expected loss / yr", timeout=90000)
        page.wait_for_timeout(4000)
        side = page.locator("[data-testid='stSidebar']")
        metrics = visible(page, "[data-testid='stMetric']")

        # 1. Overview of the landing view
        annotate(page, "01_overview", [
            (side.locator("[data-testid='stSelectbox']").first, 1),
            (union([box(side.locator("[data-testid='stMultiSelect']").first),
                    box(side.locator("[data-testid='stHorizontalBlock']").first)]), 2),
            (union([box(e) for e in side.locator("[data-testid='stExpander']").all()]), 3),
            (union([box(metrics.nth(i)) for i in range(5)]), 4),
            (page.get_by_role("tablist"), 5),
            (visible(page, "[data-testid='stPlotlyChart']").first, 6),
            (visible(page, "[data-testid='stColumn']").filter(has_text="Recommended controls for this view").last, 7),
        ], region=(0, 0, 1500, 1120))

        # 2. Department drop-down opened
        side.locator("[data-testid='stSelectbox']").first.get_by_role("combobox").click()
        page.wait_for_timeout(800)
        listbox = page.get_by_role("listbox")
        annotate(page, "02_department_dropdown", [(listbox, 1)], region=(0, 0, 760, 1000))
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        # 3. Lower half of the dashboard
        charts = visible(page, "[data-testid='stPlotlyChart']")
        appetite = visible(page, "[data-testid='stHorizontalBlock']").filter(has_text="Board appetite").first
        annotate(page, "03_appetite_heatmap", [
            (appetite, 1),
            (visible(page, "[data-testid='stButtonGroup']").first, 2),
            (charts.nth(1), 3),
            (charts.nth(2), 4),
            (visible(page, "[data-testid='stDownloadButton']").first, 5),
        ])

        # 4. Business-unit view
        side.locator("[data-testid='stSelectbox']").first.get_by_role("combobox").click()
        page.get_by_role("option", name="Business unit · Customer support").click()
        page.wait_for_timeout(5000)
        metrics = visible(page, "[data-testid='stMetric']")
        annotate(page, "04_customer_support_view", [
            (side.locator("[data-testid='stSelectbox']").first, 1),
            (union([box(metrics.nth(i)) for i in range(5)]), 2),
            (visible(page, "[data-testid='stPlotlyChart']").first, 3),
            (visible(page, "[data-testid='stColumn']").filter(has_text="Recommended controls for this view").last, 4),
        ], region=(0, 0, 1500, 1120))
        side.locator("[data-testid='stSelectbox']").first.get_by_role("combobox").click()
        page.get_by_role("option", name="Company-wide").click()
        page.wait_for_timeout(5000)

        # 5. Monte Carlo
        open_tab(page, "Monte Carlo")
        charts = visible(page, "[data-testid='stPlotlyChart']")
        annotate(page, "05_monte_carlo", [
            (charts.nth(0), 1), (charts.nth(1), 2),
            (visible(page, "[data-testid='stDataFrame']").first, 3),
            (charts.nth(2), 4),
            (visible(page, "[data-testid='stColumn']").filter(has_text="Back-test against the real 2025 breach").last, 5),
        ])

        # 6. Controls & ROI
        open_tab(page, "Controls & ROI")
        annotate(page, "06_controls_portfolio", [
            (visible(page, "[data-testid='stRadio']").first, 1),
            (union([box(visible(page, "[data-testid='stMetric']").nth(i)) for i in range(5, 8)]), 2),
            (visible(page, "[data-testid='stButton']").filter(has_text="Deploy this portfolio").first, 3),
            (visible(page, "[data-testid='stPlotlyChart']").first, 4),
        ])
        frames = visible(page, "[data-testid='stDataFrame']")
        annotate(page, "07_control_catalog", [(frames.nth(0), 1), (frames.nth(1), 2)])

        # 7. Sensitivity
        open_tab(page, "Sensitivity")
        charts = visible(page, "[data-testid='stPlotlyChart']")
        annotate(page, "08_sensitivity", [
            (visible(page, "[data-testid='stRadio']").first, 1),
            (charts.nth(0), 2),
            (visible(page, "[data-testid='stAlert']").first, 3),
        ])
        stab_cols = visible(page, "[data-testid='stHorizontalBlock']").filter(has_text="Core (optimal in every case)").first
        annotate(page, "09_robustness", [(charts.nth(1), 1),
                                        (stab_cols.locator("[data-testid='stColumn']").nth(1), 2)])

        # 9. Methodology
        open_tab(page, "Methodology & sources")
        graphs = visible(page, "[data-testid='stGraphVizChart']")
        annotate(page, "12_methodology", [(graphs.nth(0), 1), (graphs.nth(1), 2),
                                          (visible(page, "[data-testid='stDataFrame']").first, 3)])
        # 8. Report intake: form, then result
        open_tab(page, "Report intake (Parts 1–2)")
        visible(page, "[data-testid='stExpander']").filter(has_text="Submit a new insider report").first \
            .locator("summary").click()
        page.wait_for_timeout(1200)
        choose(page, "Subject type", "Contractor or temp")
        choose(page, "Subject's team", "Operations")
        choose(page, "Whose data?", "Customer")
        choose(page, "Records affected", "100 to 1,000")
        choose(page, "External party involved?", "Confirmed")
        choose(page, "Analyst triage: incident type (A)", "Bribed or colluding data exfiltration")
        choose_multi(page, "What did they do?", "Copied, photographed, downloaded or sent data out")
        choose_multi(page, "Evidence", "Ticket or system log")
        page.locator("[data-testid='stTextArea'] textarea").fill(
            "Night-shift contractor exported customer contact lists after a cash offer.")
        form = visible(page, "[data-testid='stForm']").first
        annotate(page, "10_intake_form", [
            (union([box(visible(page, "[data-testid='stMetric']").nth(i)) for i in range(5)]), 1),
            (form, 2),
            (visible(page, "[data-testid='stFormSubmitButton']").first, 3),
        ])
        visible(page, "[data-testid='stFormSubmitButton']").first.click()
        page.wait_for_timeout(7000)
        if not page.get_by_role("tab", name="Report intake (Parts 1–2)").get_attribute("aria-selected") == "true":
            open_tab(page, "Report intake (Parts 1–2)")
        frames = visible(page, "[data-testid='stDataFrame']")
        annotate(page, "11_intake_result", [
            (visible(page, "[data-testid='stAlert']").first, 1),
            (frames.nth(0), 2),
            (frames.nth(1), 3),
        ])

        browser.close()


if __name__ == "__main__":
    main()

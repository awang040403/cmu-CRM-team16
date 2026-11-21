# Part 4: Dashboard interface design

Team 16 · CMU 14-817 · Run with `streamlit run app.py`

## 4.1 Design goal

Each stakeholder should answer their own question in under a minute from one screen. The landing view keeps expected loss, P10–P90, residual loss, scenario bars, NIST-mapped controls, and appetite status. Everything else is one click deeper.

Data note: the website loads **Dheya’s synthetic history, columns A–M only** (no USD loss fields). Magnitudes remain anchored on cited Ponemon / Coinbase SEC inputs.

| User | Question | Where they get it |
|---|---|---|
| Board / audit committee | "Are we within risk appetite? What is the 1-in-20 year?" | Dashboard → appetite; Monte Carlo → exceedance |
| CISO / insider-risk lead | "Which controls, in what order, for how much?" | Controls & ROI |
| Department head | "How much of this is mine?" | Department drop-down (e.g. Customer support ≈ $45M) |
| Response team | "What is in my queue?" | Response-team view; Report intake |
| Analyst / auditor | "Where does each number come from?" | Methodology (A–M field table); Sensitivity |

## 4.2 The department drop-down

Three lenses: **Company-wide**, **Response team**, **Business unit**. Business-unit views partition the company total (Poisson thinning). Response-team views overlap by design.

With the synthetic A–M history, concentration is clear: Customer support and Operations dominate; bribed / colluding exfiltration drives most of the ALE.

## 4.3 Tabs

Dashboard · Monte Carlo · Controls & ROI · Sensitivity · Report intake (A–M table + live PoC form) · Methodology & sources.

## 4.4 Suggested live demo (3–4 minutes)

See **Amy Dashboard Demo Pack - Slides and Script.docx** for slide bullets, screenshots, and the spoken script. Headline path:

1. Company-wide → Monte Carlo: ~$97M expected, ~$381M P95, $345M actual on the curve.
2. Business unit · Customer support: ~$45M, mostly S1.
3. Clear → Recommended: residual ~$11M, ROSI ~700%.
4. Appetite mode: insurance appears when the board is strict.
5. Intake: show A–M only; state USD columns excluded.
6. Sensitivity: SLEF dominates — design for uncertainty.

## 4.5 Accessibility and integrity

- Dark theme; color is never the only signal (pills + labels).
- Banner states proof-of-concept and A–M-only data policy.
- Fixed seed 14817 and trial count shown for reproducibility.

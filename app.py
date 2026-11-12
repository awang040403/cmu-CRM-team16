"""Insider Risk Dashboard - Part 4 of the Team 16 pipeline (CMU 14-817).

Run:  streamlit run app.py
"""
from __future__ import annotations

import datetime as dt
from math import erf, log, sqrt
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from insider_risk.categorize import (  # noqa: E402
    ACTIVITY_CIA, EVIDENCE_WEIGHT, IMPACT_TO_FAIR, PRECURSOR_NAME, URGENCY_TIER,
    campaigns, categorize, leading_indicators, observation_years, suggest_routing,
)
from insider_risk.controls import (  # noqa: E402
    best_portfolio, cheapest_within_appetite, control_value_table, department_recommendations,
    efficient_frontier, evaluate_all_portfolios, scenario_reduction,
)
from insider_risk.data import (  # noqa: E402
    BUSINESS_UNITS, RESPONSE_TEAMS, benchmark_value, department_options, load_benchmarks,
    load_control_effects, load_controls, load_reports, load_scenarios, parse_department, split_multi,
)
from insider_risk.quantify import (  # noqa: E402
    Assumptions, apply_controls, build_inputs, calibration_check, exceedance_curve, exceedance_probability,
    expected_annual_loss, expected_loss_by_scenario, frequency_posterior, lognormal_from_interval,
    simulate, summarize,
)
from insider_risk.sensitivity import recommendation_stability, tornado  # noqa: E402

st.set_page_config(page_title="Insider Risk Dashboard · Coinbase", page_icon="🛡️", layout="wide")

INHERENT_COLOR = "#64748B"
RESIDUAL_COLOR = "#3B82F6"
ALERT_COLOR = "#F59E0B"
DANGER_COLOR = "#EF4444"
OK_COLOR = "#10B981"

st.markdown(
    """
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 3rem;}
div[data-testid="stMetric"] {background:#181B22; border:1px solid #262A33; border-radius:10px; padding:12px 14px;}
div[data-testid="stMetricValue"] {font-size:1.75rem;}
.poc-banner {background:#3A2A0A; color:#F5B544; border-radius:8px; padding:8px 14px; font-size:.9rem; margin-bottom:.6rem;}
.ctl-row {display:flex; justify-content:space-between; border-bottom:1px solid #262A33; padding:9px 2px; gap:12px;}
.ctl-name {font-weight:600;}
.ctl-meta {color:#9CA3AF; font-size:.82rem;}
.ctl-reg {color:#9CA3AF; font-size:.85rem; text-align:right; white-space:nowrap;}
.pill {display:inline-block; padding:1px 8px; border-radius:999px; font-size:.75rem; margin-left:6px;}
.pill-on {background:#0F3D2E; color:#34D399;} .pill-off {background:#262A33; color:#9CA3AF;}
.pill-rec {background:#172554; color:#93C5FD;}
.status-ok {color:#10B981; font-weight:700;} .status-bad {color:#EF4444; font-weight:700;}
.small-note {font-size:.84rem; color:#9CA3AF;}
</style>
""",
    unsafe_allow_html=True,
)


def money(x: float) -> str:
    ax = abs(x)
    if ax >= 1e9:
        return f"${x / 1e9:.2f}B"
    if ax >= 1e8:
        return f"${x / 1e6:.0f}M"
    if ax >= 1e6:
        return f"${x / 1e6:.1f}M"
    if ax >= 1e3:
        return f"${x / 1e3:.0f}K"
    return f"${x:,.0f}"


def style_fig(fig: go.Figure, height: int = 380) -> go.Figure:
    fig.update_layout(template="plotly_dark", height=height, paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=50, b=10),
                      legend=dict(orientation="h", yanchor="top", y=-0.16, x=0))
    return fig


def money_cols(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        out[c] = out[c].apply(lambda v: "–" if pd.isna(v) else money(v))
    return out


LOG_TICKS = [1e5, 1e6, 1e7, 1e8, 1e9]
LOG_LABELS = ["$100K", "$1M", "$10M", "$100M", "$1B"]

# --------------------------------------------------------------------------- data & caching

scenarios = load_scenarios()
controls = load_controls()
effects = load_control_effects()
benchmarks = load_benchmarks()
SCENARIO_NAMES = dict(zip(scenarios.scenario_id, scenarios.scenario))
CONTROL_NAMES = dict(zip(controls.control_id, controls.control))


@st.cache_data(show_spinner=False)
def cached_categorize(reports: pd.DataFrame) -> pd.DataFrame:
    return categorize(reports, scenarios)


@st.cache_data(show_spinner=False)
def cached_inputs(categorized: pd.DataFrame, a: Assumptions, lens: str, name: str | None) -> pd.DataFrame:
    return build_inputs(categorized, scenarios, a, lens, name)


@st.cache_data(show_spinner="Running Monte Carlo simulation…")
def cached_simulation(inputs: pd.DataFrame, n_trials: int, seed: int):
    return simulate(inputs, n_trials, seed)


@st.cache_data(show_spinner=False)
def cached_portfolios(inputs: pd.DataFrame, effectiveness: float, cost_mult: float, threshold: float):
    return evaluate_all_portfolios(inputs, controls, effects, effectiveness, cost_mult, threshold)


@st.cache_data(show_spinner=False)
def cached_department_matrix(categorized: pd.DataFrame, a: Assumptions, selected: tuple[str, ...]):
    rows = []
    for unit in BUSINESS_UNITS:
        inp = build_inputs(categorized, scenarios, a, "unit", unit)
        before = expected_loss_by_scenario(inp)
        after = expected_loss_by_scenario(apply_controls(inp, effects, list(selected), a.control_effectiveness))
        for (_, b), (_, r) in zip(before.iterrows(), after.iterrows()):
            rows.append({"unit": unit, "scenario": b.scenario, "inherent": b.expected_annual_loss,
                         "residual": r.expected_annual_loss})
    for team in RESPONSE_TEAMS:
        inp = build_inputs(categorized, scenarios, a, "team", team)
        before = expected_loss_by_scenario(inp).expected_annual_loss.sum()
        after = expected_loss_by_scenario(
            apply_controls(inp, effects, list(selected), a.control_effectiveness)).expected_annual_loss.sum()
        rows.append({"unit": f"team:{team}", "scenario": "All", "inherent": before, "residual": after})
    return pd.DataFrame(rows)


@st.cache_data(show_spinner="Running sensitivity analysis…")
def cached_tornado(categorized, a, selected, lens, name, metric):
    return tornado(categorized, scenarios, controls, effects, a, list(selected), lens, name, metric)


@st.cache_data(show_spinner="Re-optimizing under each assumption…")
def cached_stability(categorized, a):
    return recommendation_stability(categorized, scenarios, controls, effects, a)


base_reports = load_reports()
if "extra_reports" not in st.session_state:
    st.session_state.extra_reports = []
reports = pd.concat([base_reports, pd.DataFrame(st.session_state.extra_reports)], ignore_index=True) \
    if st.session_state.extra_reports else base_reports
for col in ("report_date", "first_noticed"):
    reports[col] = pd.to_datetime(reports[col])
categorized = cached_categorize(reports)

if "controls" not in st.session_state:
    default_inputs = cached_inputs(categorized, Assumptions(), "company", None)
    st.session_state.controls = list(best_portfolio(cached_portfolios(default_inputs, 1.0, 1.0, 100e6)).controls)


def set_controls(ids):
    st.session_state.controls = list(ids)


# --------------------------------------------------------------------------- sidebar

with st.sidebar:
    st.markdown("### 🛡️ Insider Risk Dashboard")
    st.caption("Coinbase · malicious insiders only · Team 16")
    dept_label = st.selectbox("Department view", department_options(), index=0,
                              help="Company-wide, a response team (who receives the report), or a business unit "
                                   "(where the insider works). Business-unit views add up to company-wide.")
    lens, dept_name = parse_department(dept_label)

    st.markdown("#### Controls to deploy")
    st.multiselect("Selected controls", list(controls.control_id), key="controls",
                   format_func=lambda c: f"{c} · {CONTROL_NAMES[c]}", label_visibility="collapsed")
    b1, b2 = st.columns(2)
    b2.button("Clear", on_click=set_controls, args=([],), width="stretch")

    with st.expander("Model assumptions", expanded=False):
        prior_rate = st.slider("Industry prior: malicious incidents / yr", 1.0, 15.0,
                               benchmark_value(benchmarks, "B14"), 0.1, help="Ponemon/DTEX 2026 (B14) = 6.3")
        prior_weight = st.slider("Weight on industry prior (years)", 0.25, 5.0, 1.0, 0.25,
                                 help="How many years of internal reports the benchmark is worth. "
                                      "Lower = trust Marie's intake data more.")
        cred_scale = st.slider("Report credibility scale", 0.5, 1.5, 1.0, 0.05)
        prim_mult = st.slider("Primary-loss multiplier", 0.5, 2.0, 1.0, 0.05)
        slef_mult = st.slider("Escalation probability (SLEF) multiplier", 0.33, 3.0, 1.0, 0.01)
        slm_mult = st.slider("Secondary-loss magnitude multiplier", 0.5, 1.5, 1.0, 0.05)
        ctl_eff = st.slider("Control effectiveness multiplier", 0.5, 1.25, 1.0, 0.05)
        cost_mult = st.slider("Control cost multiplier", 0.5, 1.5, 1.0, 0.05)
        n_trials = st.select_slider("Monte Carlo trials", [5_000, 10_000, 25_000, 50_000], value=10_000)
        seed = int(st.number_input("Random seed", 1, 99_999_999, 14817))

    with st.expander("Risk appetite", expanded=False):
        threshold = st.select_slider("Loss threshold", [50e6, 100e6, 180e6, 250e6, 345.2e6], value=100e6,
                                     format_func=money,
                                     help="$100M ≈ 7.7% of FY2025 net income ($1.3B, B22).")
        max_prob = st.slider("Max acceptable annual probability", 0.5, 10.0, 5.0, 0.5, format="%.1f%%") / 100

a = Assumptions(prior_rate=prior_rate, prior_weight_years=prior_weight, credibility_scale=cred_scale,
                primary_multiplier=prim_mult, slef_multiplier=slef_mult, slm_multiplier=slm_mult,
                control_effectiveness=ctl_eff, cost_multiplier=cost_mult)
selected = list(st.session_state.controls)

company_inputs = cached_inputs(categorized, a, "company", None)
view_inputs = cached_inputs(categorized, a, lens, dept_name)
view_residual_inputs = apply_controls(view_inputs, effects, selected, ctl_eff)
sim_in = cached_simulation(view_inputs, n_trials, seed)
sim_res = cached_simulation(view_residual_inputs, n_trials, seed)
stats_in, stats_res = summarize(sim_in.total), summarize(sim_res.total)
portfolios = cached_portfolios(company_inputs, ctl_eff, cost_mult, threshold)
recommended = best_portfolio(portfolios)
b1.button("Recommended", on_click=set_controls, args=(recommended.controls,), width="stretch",
          help=f"Net-benefit-maximizing portfolio: {recommended.portfolio}")


def view_mask(df: pd.DataFrame) -> pd.Series:
    if lens == "unit":
        return df.subject_team == dept_name
    if lens == "team":
        return df.route_to.apply(lambda v: dept_name in split_multi(v))
    return pd.Series(True, index=df.index)


view_reports = categorized[view_mask(categorized)]
latest = categorized.report_date.max()
q_now = latest.to_period("Q")
reports_q = int((view_reports.report_date.dt.to_period("Q") == q_now).sum())
reports_prev = int((view_reports.report_date.dt.to_period("Q") == q_now - 1).sum())
selected_cost = controls.loc[controls.control_id.isin(selected), "annual_cost"].sum() * cost_mult

# --------------------------------------------------------------------------- header

st.markdown(f"## {dept_label}")
st.markdown(
    '<div class="poc-banner">Proof of concept: frequencies blend Ponemon/DTEX 2026 benchmarks with Marie\'s '
    f'{len(base_reports)} sample web-form reports; magnitudes are anchored on Ponemon and Coinbase SEC filings. '
    'Team estimates are labeled in the Methodology tab.</div>', unsafe_allow_html=True)

def money_short(x: float) -> str:
    return f"${x / 1e6:.0f}M" if abs(x) >= 1e6 else money(x)


k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Expected loss / yr", money(stats_in["mean"]),
          help="Inherent: mean of the simulated annual loss distribution before the selected controls.")
k2.metric("P10–P90 range", f"{money_short(stats_in['p10'])}–{money_short(stats_in['p90'])}",
          help="80% of simulated years fall in this range (inherent).")
k3.metric("Reports this qtr", reports_q, delta=reports_q - reports_prev, delta_color="inverse",
          help=f"{q_now}, compared with the previous quarter, for this department view.")
k4.metric("Residual loss / yr", money(stats_res["mean"]),
          delta=f"-{(1 - stats_res['mean'] / stats_in['mean']):.0%}" if stats_in["mean"] else None,
          delta_color="inverse", help="Mean annual loss after the controls selected in the sidebar.")
if lens == "company":
    rosi = (stats_in["mean"] - stats_res["mean"] - selected_cost) / selected_cost if selected_cost else 0
    k5.metric("ROSI", f"{rosi:.0%}" if selected_cost else "–",
              help=f"Return on security investment = (loss avoided − cost) / cost. "
                   f"Annual cost of selected controls: {money(selected_cost)}.")
else:
    k5.metric("Loss avoided / yr", money(stats_in["mean"] - stats_res["mean"]),
              help="Control costs are company-wide, so ROSI is shown only in the company-wide view.")

tabs = st.tabs(["Dashboard", "Monte Carlo", "Controls & ROI", "Sensitivity",
                "Report intake (Parts 1–2)", "Methodology & sources"])

# --------------------------------------------------------------------------- tab 1: dashboard

with tabs[0]:
    left, right = st.columns([1.15, 1])
    with left:
        sc = scenario_reduction(view_inputs, effects, selected, ctl_eff).sort_values("inherent")
        fig = go.Figure()
        fig.add_bar(y=sc.scenario, x=sc.inherent, orientation="h", name="Inherent", marker_color=INHERENT_COLOR,
                    text=[money(v) for v in sc.inherent], textposition="outside")
        fig.add_bar(y=sc.scenario, x=sc.residual, orientation="h", name="With selected controls",
                    marker_color=RESIDUAL_COLOR, text=[money(v) for v in sc.residual], textposition="outside")
        fig.update_layout(title="Expected annual loss by scenario", barmode="group",
                          xaxis_tickprefix="$", xaxis_tickformat="~s",
                          xaxis_range=[0, max(sc.inherent.max(), 1) * 1.2])
        st.plotly_chart(style_fig(fig, 360), width="stretch")
    with right:
        st.markdown("##### Recommended controls for this view")
        mitigations = controls[controls.treatment == "Mitigate"]
        recs = department_recommendations(view_inputs, mitigations, effects, ctl_eff, top=4)
        html = []
        for _, r in recs.iterrows():
            nist = r.nist_800_53.split(";")[0]
            if r.control_id in selected:
                pill = '<span class="pill pill-on">deployed</span>'
            elif r.control_id in recommended.controls:
                pill = '<span class="pill pill-rec">in optimal portfolio</span>'
            else:
                pill = '<span class="pill pill-off">outside optimal portfolio</span>'
            html.append(
                f'<div class="ctl-row"><div><div class="ctl-name">{nist} · {r.control}{pill}</div>'
                f'<div class="ctl-meta">{r.csf_function} · removes {money(r.loss_avoided)}/yr in this view · '
                f'costs {money(r.annual_cost * cost_mult)}/yr company-wide</div></div>'
                f'<div class="ctl-reg">{r.regulation.split(";")[0]}</div></div>')
        st.markdown("".join(html), unsafe_allow_html=True)
        st.caption("Mitigation controls ranked by the expected loss each one removes from this view on its own. "
                   "A control can rank high here yet sit outside the optimal portfolio when other controls "
                   "already cover the same loss (see Controls & ROI → marginal net benefit).")

    st.markdown("##### Risk appetite check")
    p_in = exceedance_probability(sim_in.total, threshold)
    p_res = exceedance_probability(sim_res.total, threshold)
    c1, c2, c3 = st.columns(3)
    c1.metric(f"P(annual loss ≥ {money(threshold)}) · inherent", f"{p_in:.1%}")
    c2.metric(f"P(annual loss ≥ {money(threshold)}) · residual", f"{p_res:.1%}")
    ok = p_res <= max_prob
    c3.markdown(
        f"**Board appetite:** ≤ {max_prob:.1%} chance of a {money(threshold)}+ year<br>"
        f"<span class='{'status-ok' if ok else 'status-bad'}'>"
        f"{'WITHIN APPETITE' if ok else 'OUTSIDE APPETITE'}</span>"
        f"<div class='small-note'>{'' if ok else 'See Controls & ROI → cheapest portfolio within appetite.'}</div>",
        unsafe_allow_html=True)

    st.markdown("##### Where the risk sits")
    show = st.segmented_control("Show", ["Inherent", "Residual"], default="Residual", key="heat_mode") or "Residual"
    show_col = "residual" if show == "Residual" else "inherent"
    dm = cached_department_matrix(categorized, a, tuple(selected))
    units = dm[~dm.unit.str.startswith("team:")]
    pivot = units.pivot(index="unit", columns="scenario", values=show_col).reindex(BUSINESS_UNITS)
    pivot = pivot[[s for s in scenarios.scenario]]
    ylabels = [f"▶ {u}" if (lens == "unit" and u == dept_name) else u for u in pivot.index]
    hc1, hc2 = st.columns([1.5, 1])
    with hc1:
        heat = go.Figure(go.Heatmap(
            z=pivot.values / 1e6, x=pivot.columns, y=ylabels, colorscale="YlOrRd",
            text=[[money(v) for v in row] for row in pivot.values], texttemplate="%{text}",
            hovertemplate="%{y}<br>%{x}<br>%{text}/yr<extra></extra>", colorbar=dict(title="$M/yr")))
        heat.update_layout(title=f"Business unit × scenario expected loss ({show.lower()})",
                           yaxis_autorange="reversed")
        st.plotly_chart(style_fig(heat, 400), width="stretch")
    with hc2:
        teams = dm[dm.unit.str.startswith("team:")].copy()
        teams["team"] = teams.unit.str.replace("team:", "", regex=False)
        teams = teams.sort_values(show_col)
        colors = [RESIDUAL_COLOR if (lens == "team" and t == dept_name) else INHERENT_COLOR for t in teams.team]
        tf = go.Figure(go.Bar(y=teams.team, x=teams[show_col], orientation="h", marker_color=colors,
                              text=[money(v) for v in teams[show_col]], textposition="outside"))
        tf.update_layout(title="Exposure each response team must handle", xaxis_tickprefix="$",
                         xaxis_tickformat="~s", xaxis_range=[0, max(teams[show_col].max(), 1) * 1.25])
        st.plotly_chart(style_fig(tf, 400), width="stretch")
        st.caption("Response-team exposures overlap (one report is routed to several teams); "
                   "business-unit exposures partition the company total.")

    brief = f"""# Insider-risk executive brief: {dept_label}
Generated {dt.date.today():%d %b %Y} · {n_trials:,} Monte Carlo trials · seed {seed}

| Metric | Inherent | With selected controls |
|---|---|---|
| Expected annual loss | {money(stats_in['mean'])} | {money(stats_res['mean'])} |
| Median year | {money(stats_in['median'])} | {money(stats_res['median'])} |
| 1-in-20 year (P95) | {money(stats_in['p95'])} | {money(stats_res['p95'])} |
| 1-in-100 year (P99) | {money(stats_in['p99'])} | {money(stats_res['p99'])} |
| P(loss ≥ {money(threshold)}) | {p_in:.1%} | {p_res:.1%} |

Selected controls: {', '.join(selected) or 'none'} (annual cost {money(selected_cost)}).
Board appetite (≤ {max_prob:.1%} chance of a {money(threshold)}+ year): {'met' if ok else 'NOT met'}.
Top recommended controls for this view: {', '.join(recs.control_id)}.
"""
    st.download_button("Download executive brief (Markdown)", brief.encode(), "executive_brief.md", "text/markdown")

# --------------------------------------------------------------------------- tab 2: Monte Carlo

with tabs[1]:
    st.markdown(f"##### {n_trials:,} simulated years · FAIR frequency × magnitude · seed {seed}")
    m1, m2 = st.columns(2)
    with m1:
        hist = go.Figure()
        for label, sim, color in (("Inherent", sim_in, INHERENT_COLOR), ("With selected controls", sim_res, RESIDUAL_COLOR)):
            hist.add_histogram(x=np.log10(np.maximum(sim.total, 1e4)), name=label, opacity=0.65,
                               marker_color=color, xbins=dict(start=4, end=9.3, size=0.08))
        hist.update_layout(barmode="overlay", title="Distribution of annual loss (log scale)",
                           xaxis=dict(tickvals=np.log10(LOG_TICKS), ticktext=LOG_LABELS, title="Annual loss"),
                           yaxis_title="Simulated years")
        st.plotly_chart(style_fig(hist, 400), width="stretch")
        st.caption("Two humps: ordinary years driven by primary losses, and rare escalation years where a "
                   "secondary loss (extortion, mass scams, regulators) dominates. Years with no loss event "
                   "are stacked at the left edge.")
    with m2:
        lec = go.Figure()
        for label, sim, color in (("Inherent", sim_in, INHERENT_COLOR), ("With selected controls", sim_res, RESIDUAL_COLOR)):
            curve = exceedance_curve(sim.total)
            lec.add_scatter(x=curve.loss, y=curve.probability, mode="lines", name=label, line=dict(color=color, width=3))
        lec.add_scatter(x=[threshold], y=[max_prob], mode="markers", name="Board appetite",
                        marker=dict(symbol="x", size=14, color=DANGER_COLOR))
        for x, txt, ypos in ((180e6, "Coinbase 8-K<br>low $180M", 0.10), (345.2e6, "FY2025<br>actual<br>$345M", 0.30)):
            lec.add_vline(x=x, line_dash="dot", line_color=ALERT_COLOR)
            lec.add_annotation(x=np.log10(x), y=ypos, yref="paper", text=txt, showarrow=False,
                               xanchor="right", font=dict(size=10, color=ALERT_COLOR))
        lec.update_layout(title="Loss exceedance curve", xaxis_type="log", yaxis_type="log",
                          xaxis=dict(tickvals=LOG_TICKS, ticktext=LOG_LABELS, title="Annual loss ≥ x"),
                          yaxis=dict(title="Probability", tickformat=".1%", range=[np.log10(5e-4), 0]))
        st.plotly_chart(style_fig(lec, 400), width="stretch")

    t1, t2, t3 = st.columns([1, 1, 1])
    with t1:
        st.markdown("**Tail statistics**")
        rows = [("Mean (expected loss)", "mean"), ("Median year", "median"), ("P10", "p10"), ("P90", "p90"),
                ("P95 · 1-in-20 year", "p95"), ("P99 · 1-in-100 year", "p99"), ("TVaR 95 (avg of worst 5%)", "tvar95")]
        st.dataframe(pd.DataFrame([{"Statistic": lab, "Inherent": money(stats_in[k]),
                                    "With controls": money(stats_res[k])} for lab, k in rows]),
                     hide_index=True, width="stretch")
    with t2:
        st.markdown("**What drives the average vs. the tail** (inherent)")
        by = sim_in.by_scenario
        tail_mask = sim_in.total >= stats_in["p95"]
        contrib = pd.DataFrame({"scenario": by.columns,
                                "Share of expected loss": by.mean().to_numpy() / max(by.mean().sum(), 1),
                                "Share of worst-5% years": by[tail_mask].mean().to_numpy() / max(by[tail_mask].mean().sum(), 1)})
        cf = go.Figure()
        for col, color in (("Share of expected loss", INHERENT_COLOR), ("Share of worst-5% years", DANGER_COLOR)):
            cf.add_bar(y=contrib.scenario, x=contrib[col], orientation="h", name=col, marker_color=color)
        cf.update_layout(barmode="group", xaxis_tickformat=".0%")
        st.plotly_chart(style_fig(cf, 300), width="stretch")
    with t3:
        st.markdown("**Back-test against the real 2025 breach**")
        s1 = scenarios.set_index("scenario_id").loc["S1"]
        mu_s, sd_s = lognormal_from_interval(s1.slm_lo * slm_mult, s1.slm_hi * slm_mult)
        pct = 0.5 * (1 + erf((log(345.2e6) - mu_s) / (sd_s * sqrt(2))))
        if lens == "company":
            st.markdown(
                f"- P(annual loss ≥ $180M), inherent: **{exceedance_probability(sim_in.total, 180e6):.1%}** "
                f"(about 1 year in {1 / max(exceedance_probability(sim_in.total, 180e6), 1e-4):.0f})\n"
                f"- P(annual loss ≥ $345.2M, the FY2025 actual): **{exceedance_probability(sim_in.total, 345.2e6):.1%}**\n"
                f"- Given an escalation, the $345.2M actual sits at the **{pct:.0%} percentile** of the modeled "
                f"secondary-loss range, so the model reproduces the size of the real event.")
        else:
            st.markdown("Switch to **Company-wide** to compare against the 2025 Coinbase breach.")
        split = pd.DataFrame({"component": ["Primary (response, replacement)", "Secondary (fines, scams, reputation)"],
                              "value": [sim_in.primary.mean(), sim_in.secondary.mean()]})
        st.caption(f"Expected loss split: primary {money(split.value[0])}, secondary {money(split.value[1])}.")

    st.download_button("Download simulated annual losses (CSV)",
                       pd.DataFrame({"inherent_usd": sim_in.total, "residual_usd": sim_res.total})
                       .to_csv(index=False).encode(), "simulated_annual_losses.csv", "text/csv")

# --------------------------------------------------------------------------- tab 3: controls

with tabs[2]:
    st.markdown("##### Choose the control portfolio")
    st.caption("All 1,024 combinations of the 10 controls are evaluated in closed form on the company-wide "
               "model (control costs are company-wide). The tail probability is an analytic screen; "
               "the Monte Carlo tab confirms the selected portfolio.")
    oc1, oc2 = st.columns([1.2, 1])
    with oc1:
        objective = st.radio("Objective", ["Maximize net benefit (expected value)",
                                           "Cheapest portfolio that meets risk appetite",
                                           "Best net benefit within a budget"], horizontal=False)
        budget = None
        if objective.startswith("Best net"):
            budget = st.slider("Annual budget", 0.0, 20e6, 5e6, 0.5e6, format="$%.0f")
    if objective.startswith("Maximize"):
        pick = recommended
    elif objective.startswith("Cheapest"):
        pick = cheapest_within_appetite(portfolios, max_prob)
    else:
        pick = best_portfolio(portfolios, budget)
    with oc2:
        if pick is None:
            st.error(f"No combination of controls meets ≤ {max_prob:.1%} chance of a {money(threshold)}+ year. "
                     "Raise the threshold, accept the residual risk formally, or transfer more of it.")
        else:
            st.markdown(f"**Portfolio:** {pick.portfolio}")
            p1, p2, p3 = st.columns(3)
            p1.metric("Annual cost", money(pick.annual_cost))
            p2.metric("Net benefit / yr", money(pick.net_benefit))
            p3.metric(f"P(≥ {money(threshold)})", f"{pick.p_exceed:.1%}")
            st.button("Deploy this portfolio", type="primary", on_click=set_controls, args=(pick.controls,))

    frontier = efficient_frontier(portfolios)
    current = portfolios[portfolios.controls.apply(lambda c: sorted(c) == sorted(selected))].iloc[0]
    ff = go.Figure()
    meets = portfolios.p_exceed <= max_prob
    for mask, label, color in ((~meets, "Outside appetite", "#4B5563"), (meets, "Within appetite", OK_COLOR)):
        sub = portfolios[mask]
        ff.add_scatter(x=sub.annual_cost, y=sub.residual_ale, mode="markers", name=label,
                       marker=dict(size=6, color=color, opacity=0.55), text=sub.portfolio,
                       hovertemplate="%{text}<br>Cost %{x:$,.0f}<br>Residual ALE %{y:$,.0f}<extra></extra>")
    ff.add_scatter(x=frontier.annual_cost, y=frontier.residual_ale, mode="lines", name="Efficient frontier",
                   line=dict(color=RESIDUAL_COLOR, width=2))
    ff.add_scatter(x=[current.annual_cost], y=[current.residual_ale], mode="markers", name="Currently selected",
                   marker=dict(symbol="star", size=18, color=ALERT_COLOR))
    if pick is not None:
        ff.add_scatter(x=[pick.annual_cost], y=[pick.residual_ale], mode="markers", name="Objective's pick",
                       marker=dict(symbol="diamond-open", size=18, color="white", line=dict(width=2)))
    base_ale = portfolios.residual_ale.iloc[0]
    xs = np.linspace(0, portfolios.annual_cost.max(), 50)
    ff.add_scatter(x=xs, y=base_ale - xs, mode="lines", name="Break-even (cost = loss avoided)",
                   line=dict(color=DANGER_COLOR, dash="dot"))
    ff.update_layout(title="Cost (x) vs. residual expected loss (y) for every portfolio", xaxis_title=None,
                     yaxis_title="Residual expected annual loss", xaxis_tickprefix="$", xaxis_tickformat="~s",
                     yaxis_tickprefix="$", yaxis_tickformat="~s")
    st.plotly_chart(style_fig(ff, 460), width="stretch")
    st.caption("Points below the red line pay for themselves. The frontier flattens: after ~$8M/yr each extra "
               "dollar buys less than a dollar of loss reduction, which is why insurance (C10) only appears "
               "when the appetite is strict.")

    st.markdown("##### Control catalog with NIST and regulatory mapping")
    cv = control_value_table(company_inputs, controls, effects, selected, ctl_eff, cost_mult)
    cv = cv.merge(controls[["control_id", "treatment", "nist_800_53", "csf_function", "regulation", "gap_addressed"]],
                  on="control_id")
    st.dataframe(
        money_cols(cv, ["annual_cost", "standalone_loss_avoided", "marginal_net_benefit"])[
            ["control_id", "control", "treatment", "selected", "annual_cost", "standalone_loss_avoided",
             "standalone_pct", "benchmark_pct", "marginal_net_benefit", "nist_800_53", "csf_function",
             "regulation", "gap_addressed"]],
        hide_index=True, width="stretch",
        column_config={
            "control_id": "ID", "control": st.column_config.TextColumn("Control", width="large"),
            "treatment": "Treatment", "selected": "Deployed",
            "annual_cost": "Annual cost",
            "standalone_loss_avoided": "Loss avoided alone",
            "standalone_pct": st.column_config.NumberColumn("Alone, % of ALE", format="percent"),
            "benchmark_pct": st.column_config.NumberColumn("Ponemon benchmark %", format="percent",
                                                           help="Ponemon/DTEX 2026 cost reduction ÷ $19.5M average"),
            "marginal_net_benefit": st.column_config.TextColumn("Marginal net benefit",
                                                                help="Given the other selected controls"),
            "nist_800_53": "NIST SP 800-53", "csf_function": "NIST CSF 2.0", "regulation": "Regulation",
            "gap_addressed": "Gap addressed",
        })
    st.caption("Our modeled effects stay at or below the Ponemon benchmarks (compare the two % columns): "
               "Ponemon reports cross-sectional associations, not causal effects, so we take the conservative side.")

    st.markdown("##### Scenario-level effect of the selected controls (company-wide)")
    sr = scenario_reduction(company_inputs, effects, selected, ctl_eff)
    st.dataframe(money_cols(sr, ["inherent", "residual"])[["scenario", "inherent", "residual", "reduction_pct"]],
                 hide_index=True, width="stretch",
                 column_config={"scenario": "Scenario", "inherent": "Inherent ALE", "residual": "Residual ALE",
                                "reduction_pct": st.column_config.NumberColumn("Reduction", format="percent")})

# --------------------------------------------------------------------------- tab 4: sensitivity

with tabs[3]:
    metric_label = st.radio("Output to stress-test", ["Inherent expected loss", "Residual expected loss",
                                                      "Net benefit of selected controls"], horizontal=True)
    metric = {"Inherent expected loss": "baseline", "Residual expected loss": "residual",
              "Net benefit of selected controls": "net"}[metric_label]
    tor = cached_tornado(categorized, a, tuple(selected), lens, dept_name, metric)
    center = tor.center.iloc[0]
    tf = go.Figure()
    tf.add_bar(y=tor.parameter, x=tor.at_low - center, base=center, orientation="h", name="Low end of range",
               marker_color="#60A5FA", customdata=tor.low_input,
               hovertemplate="%{y}<br>input %{customdata}<br>result %{x:$,.0f}<extra></extra>")
    tf.add_bar(y=tor.parameter, x=tor.at_high - center, base=center, orientation="h", name="High end of range",
               marker_color=ALERT_COLOR, customdata=tor.high_input,
               hovertemplate="%{y}<br>input %{customdata}<br>result %{x:$,.0f}<extra></extra>")
    tf.add_vline(x=center, line_color="white", annotation_text=f"Base: {money(center)}")
    tf.update_layout(barmode="overlay", title=f"Tornado: {metric_label.lower()} ({dept_label})",
                     xaxis_tickprefix="$", xaxis_tickformat="~s")
    st.plotly_chart(style_fig(tf, 430), width="stretch")
    top = tor.iloc[-1]
    st.info(f"**What would change our answer:** *{top.parameter}* moves the result between "
            f"{money(min(top.at_low, top.at_high))} and {money(max(top.at_low, top.at_high))}. "
            "That is where better data has the highest value of information.")
    st.dataframe(tor.sort_values("swing", ascending=False)[["parameter", "low_input", "high_input", "range_basis"]],
                 hide_index=True, width="stretch",
                 column_config={"parameter": "Input", "low_input": "Low", "high_input": "High",
                                "range_basis": st.column_config.TextColumn("Why this range", width="large")})

    st.markdown("##### Is the recommended portfolio robust?")
    stab = cached_stability(categorized, a)
    freq_in = {cid: stab.best_portfolio.apply(lambda p, c=cid: c in p.split(", ")).mean()
               for cid in controls.control_id}
    core = [c for c, f in freq_in.items() if f == 1.0]
    never = [c for c, f in freq_in.items() if f == 0.0]
    swing = [c for c, f in freq_in.items() if 0 < f < 1]
    sc1, sc2 = st.columns([1, 1.3])
    with sc1:
        bars = pd.DataFrame({"control": [f"{c} · {CONTROL_NAMES[c][:38]}" for c in freq_in],
                             "share": list(freq_in.values())}).sort_values("share")
        sf = go.Figure(go.Bar(y=bars.control, x=bars.share, orientation="h",
                              marker_color=[OK_COLOR if s == 1 else (ALERT_COLOR if s > 0 else "#4B5563")
                                            for s in bars.share],
                              text=[f"{s:.0%}" for s in bars.share], textposition="outside", cliponaxis=False))
        sf.update_layout(title=f"Share of {len(stab)} stress cases where each control is optimal",
                         xaxis_tickformat=".0%", xaxis_range=[0, 1.3])
        st.plotly_chart(style_fig(sf, 400), width="stretch")
    with sc2:
        st.markdown(
            f"- **Core (optimal in every case):** {', '.join(core) or 'none'}. These are no-regret investments.\n"
            f"- **Swing (depends on assumptions):** {', '.join(swing) or 'none'}. Pilot first and decide with data.\n"
            f"- **Never optimal on expected value:** {', '.join(never) or 'none'}. Justify only through risk "
            f"appetite or regulation, not ROI.\n"
            f"- Lowest net benefit across all stress cases: **{money(stab.net_benefit.min())}/yr**, "
            f"{'still positive' if stab.net_benefit.min() > 0 else 'negative in at least one case'}.")
    st.dataframe(money_cols(stab, ["net_benefit"]), hide_index=True, width="stretch",
                 column_config={"case": "Stress case", "best_portfolio": "Best portfolio",
                                "net_benefit": "Net benefit / yr", "same_as_base": "Same as base?"})

# --------------------------------------------------------------------------- tab 5: intake

with tabs[4]:
    flash = st.session_state.pop("flash", None)
    if flash:
        row = categorized.loc[categorized.report_id == flash["id"]].iloc[0]
        new_ale = expected_annual_loss(company_inputs)
        if not row.is_loss_event:
            how = "It is a precursor signal, so it is tracked as a leading indicator, not a loss event."
        elif row.campaign_size > 1:
            how = (f"It was linked to existing campaign {row.campaign_id} ({row.campaign_size} reports), so it adds "
                   "evidence about an ongoing event instead of counting as a new one.")
        else:
            how = f"It opened new campaign {row.campaign_id} with event weight {row.credibility:.1f}."
        st.success(f"**{flash['id']}** routed to {', '.join(flash['route'])}. {how} Company-wide expected loss: "
                   f"{money(flash['prev_ale'])} → {money(new_ale)}.")
        st.toast(f"{flash['id']} submitted · expected loss {money(flash['prev_ale'])} → {money(new_ale)}")

    li = leading_indicators(view_reports) if len(view_reports) else None
    st.markdown("##### Leading indicators" + ("" if lens == "company" else f" · {dept_label}"))
    if li:
        l1, l2, l3, l4, l5 = st.columns(5)
        l1.metric("Reports in view", len(view_reports))
        l2.metric("Precursor-only reports", li["precursors"], help="Signals with no loss yet: tracked as KRIs, "
                                                                     "not counted as loss events.")
        l3.metric("Days to report", f"{li['median_detection_lag']:.0f}",
                  help="Median days from first noticed to reported. Ponemon average time to contain: "
                       f"{benchmark_value(benchmarks, 'B02'):.0f} days (B02).")
        l4.metric("Involving vendor/BPO staff", f"{li['vendor_share']:.0%}")
        l5.metric("Still happening", li["ongoing"])
    else:
        st.info("No reports in this department view yet; its risk comes from the smoothed company-wide prior.")

    with st.expander("➕ Submit a new insider report (Part 1: department web form)", expanded=False):
        with st.form("new_report", clear_on_submit=True):
            f1, f2, f3 = st.columns(3)
            report_date = f1.date_input("Report date", value=dt.date.today())
            first_noticed = f1.date_input("First noticed", value=dt.date.today() - dt.timedelta(days=3))
            reporter_rel = f1.selectbox("Your relationship", ["Coworker", "I manage them", "They manage me",
                                                              "No direct relationship"])
            anonymous = f1.radio("Anonymous?", ["Yes", "No"], horizontal=True)
            subject_type = f2.selectbox("Subject type", ["Employee", "Contractor or temp",
                                                         "Outsourced vendor staff (BPO, call center)"])
            subject_team = f2.selectbox("Subject's team", BUSINESS_UNITS)
            subject_access = f2.selectbox("Subject's access", ["Standard tools only", "Customer records and support tools",
                                                               "Admin or privileged system access",
                                                               "Wallets, payments or fund movement"])
            activities = f2.multiselect("What did they do?", list(ACTIVITY_CIA))
            data_owner = f3.selectbox("Whose data?", ["", "Customer", "Employee", "Company"])
            records = f3.selectbox("Records affected", ["", "10 to 100", "100 to 1,000", "Over 1,000"])
            external = f3.selectbox("External party involved?", ["No", "Suspected", "Confirmed"])
            evidence = f3.multiselect("Evidence", list(EVIDENCE_WEIGHT))
            urgency = st.selectbox("Urgency", list(URGENCY_TIER))
            incident_type = st.selectbox("Analyst triage: incident type (A)",
                                         list(scenarios.form_scenario_name) + [PRECURSOR_NAME])
            impacts = st.multiselect("Expected impact categories (C)", list(IMPACT_TO_FAIR))
            note = st.text_area("What happened?")
            submitted = st.form_submit_button("Submit report", type="primary")
        if submitted:
            sid = dict(zip(scenarios.form_scenario_name, scenarios.scenario_id)).get(incident_type, "P0")
            route = suggest_routing(sid, subject_type, subject_team, data_owner or None, external)
            new_id = f"IR-2026-{len(reports) + 1:04d}"
            st.session_state.extra_reports.append({
                "report_id": new_id, "report_date": pd.Timestamp(report_date), "form": "company-wide",
                "reporter_team": None, "reporter_relationship": reporter_rel, "anonymous": anonymous,
                "subject_type": subject_type, "subject_team": subject_team, "subject_access": subject_access,
                "subject_location": None, "activities": "; ".join(activities), "data_owner": data_owner or None,
                "customer_data": None, "employee_data": None, "company_data": None,
                "records_affected": records or None, "exfil_method": None, "external_party_involved": external,
                "first_noticed": pd.Timestamp(first_noticed), "frequency": None, "still_happening": "Not sure",
                "found_out_by": None, "evidence": "; ".join(evidence) or "Nothing yet", "urgency": urgency,
                "note": note, "scenario_name": incident_type, "impact_categories": "; ".join(impacts) or None,
                "route_to": "; ".join(route)})
            st.session_state.flash = {"id": new_id, "route": route,
                                      "prev_ale": expected_annual_loss(company_inputs)}
            st.rerun()
        if st.session_state.extra_reports:
            st.caption(f"{len(st.session_state.extra_reports)} report(s) added this session.")
            if st.button("Remove reports added this session"):
                st.session_state.extra_reports = []
                st.rerun()

    st.markdown("##### Categorized reports (Part 2: A · B · C · D)")
    st.dataframe(
        view_reports[["report_id", "report_date", "subject_team", "subject_type", "scenario_name", "intent",
                      "cia", "severity_tier", "primary_loss_forms", "secondary_loss_forms", "credibility",
                      "records_est", "detection_lag_days", "campaign_id", "route_to", "note"]],
        hide_index=True, width="stretch",
        column_config={
            "report_id": "Report", "subject_team": "Business unit", "subject_type": "Insider type",
            "intent": "Intent", "route_to": "Routed to",
            "report_date": st.column_config.DateColumn("Date"), "scenario_name": "A · Incident type",
            "cia": "B · CIA property", "severity_tier": "B · Severity tier",
            "primary_loss_forms": "C · Primary loss (FAIR)", "secondary_loss_forms": "C · Secondary loss (FAIR)",
            "credibility": st.column_config.ProgressColumn("D · Credibility", min_value=0, max_value=1, format="%.1f"),
            "records_est": "D · Records (est.)", "detection_lag_days": "D · Days to report",
            "campaign_id": "Campaign", "note": st.column_config.TextColumn("Note", width="large"),
        })
    st.markdown("##### Linked campaigns (what the frequency model counts)")
    st.caption("Reports with the same scenario, business unit and insider type within 90 days are one campaign. "
               "IR-0001, IR-0002 and IR-0008 arrived seven weeks apart and describe the same bribery ring.")
    st.dataframe(campaigns(categorized), hide_index=True, width="stretch",
                 column_config={"campaign_id": "Campaign", "scenario_id": "Scenario", "subject_team": "Business unit",
                                "reports": "Reports", "n_reports": "# reports",
                                "first_report": st.column_config.DateColumn("First report"),
                                "last_report": st.column_config.DateColumn("Last report"),
                                "event_weight": st.column_config.NumberColumn(
                                    "Event weight", format="%.2f",
                                    help="Highest report credibility in the campaign = probability it is a real event")})
    st.download_button("Download intake log (CSV)", categorized.to_csv(index=False).encode(),
                       "insider_reports_categorized.csv", "text/csv")

# --------------------------------------------------------------------------- tab 6: methodology

with tabs[5]:
    st.markdown("##### Pipeline")
    st.graphviz_chart("""
digraph { rankdir=LR; bgcolor="transparent"; node [shape=box style="rounded,filled" fontname="Helvetica"
  fillcolor="#1E2230" fontcolor="#E5E7EB" color="#3B82F6"]; edge [color="#9CA3AF"];
  R [label="1. Report\\nDepartment web forms\\n(Marie's intake sample)"];
  C [label="2. Categorize\\nA incident type · B CIA + severity\\nC FAIR loss forms · D credibility, records\\n+ campaign linking"];
  Q [label="3. Quantify\\nGamma-Poisson LEF (Ponemon prior)\\nLognormal primary + secondary loss\\n10,000-trial Monte Carlo"];
  D [label="4. Dashboard\\nDepartment & company views\\nControls, ROI, appetite\\nNIST 800-53 / CSF 2.0 / regulation" fillcolor="#0F3D2E" color="#10B981"];
  R -> C -> Q -> D; D -> R [label=" new reports update\\n the posterior" style=dashed fontcolor="#9CA3AF" fontsize=10];
}""", width="stretch")

    st.markdown("##### FAIR ontology: where each number comes from")
    st.graphviz_chart("""
digraph { rankdir=TB; bgcolor="transparent"; node [shape=box style="rounded,filled" fontname="Helvetica"
  fillcolor="#1E2230" fontcolor="#E5E7EB" color="#4B5563" fontsize=11]; edge [color="#9CA3AF"];
  RISK [label="Annualized loss exposure" color="#3B82F6"];
  LEF [label="Loss Event Frequency\\nGamma(6.3 prior + credible campaigns)\\nB14 + intake log"];
  LM [label="Loss Magnitude"];
  PL [label="Primary loss\\nLognormal 90% interval\\nB03, B11, B15, B19/B20"];
  SL [label="Secondary loss"];
  SLEF [label="SLEF: escalation probability\\nteam estimate, 1%-8% tested"];
  SLM [label="SLM: Lognormal\\nCoinbase 8-K $180M-$400M (B18)"];
  CTRL [label="Controls (C1-C10)\\nreduce LEF, PL, SLEF, SLM\\nbenchmarked to B05-B09, B16/B17" fillcolor="#0F3D2E" color="#10B981"];
  RISK -> LEF; RISK -> LM; LM -> PL; LM -> SL; SL -> SLEF; SL -> SLM;
  CTRL -> LEF [style=dashed]; CTRL -> PL [style=dashed]; CTRL -> SLEF [style=dashed]; CTRL -> SLM [style=dashed];
}""", width="stretch")

    st.markdown("##### Bayesian frequency update (company-wide)")
    t_years = observation_years(categorized)
    fp = frequency_posterior(categorized, scenarios, a)
    fp.insert(1, "scenario", fp.scenario_id.map(SCENARIO_NAMES))
    st.markdown(
        f"Prior: Ponemon/DTEX 2026 average of **{prior_rate:g} malicious incidents per year**, split evenly over "
        f"four scenarios and worth **{prior_weight:g} year(s)** of evidence. Data: credibility-weighted campaigns "
        f"over a **{t_years * 365.25:.0f}-day** window. Credibility factor Z = t / (t + w) = "
        f"**{fp.credibility_Z.iloc[0]:.2f}**: internal data moves the estimate {fp.credibility_Z.iloc[0]:.0%} "
        "of the way from the benchmark toward the observed rate. As reports accumulate, Z rises toward 1.")
    st.dataframe(fp[["scenario", "campaigns", "effective_events", "prior_rate", "observed_rate", "posterior_rate",
                     "rate_p05", "rate_p95"]], hide_index=True, width="stretch",
                 column_config={
                     "scenario": "Scenario", "campaigns": "Campaigns",
                     "effective_events": st.column_config.NumberColumn("Weighted events", format="%.2f"),
                     "prior_rate": st.column_config.NumberColumn("Prior / yr", format="%.2f"),
                     "observed_rate": st.column_config.NumberColumn("Observed / yr", format="%.2f"),
                     "posterior_rate": st.column_config.NumberColumn("Posterior / yr", format="%.2f"),
                     "rate_p05": st.column_config.NumberColumn("Posterior P5", format="%.2f"),
                     "rate_p95": st.column_config.NumberColumn("Posterior P95", format="%.2f")})

    st.markdown("##### Calibration check against cited benchmarks")
    cc = calibration_check(company_inputs, benchmarks)
    cc["ratio"] = cc.model / cc.benchmark
    for col in ("model", "benchmark"):
        cc[col] = [f"{v:.1f} / yr" if q.startswith("Malicious") else money(v) for q, v in zip(cc.quantity, cc[col])]
    st.dataframe(cc, hide_index=True, width="stretch",
                 column_config={"quantity": "Quantity", "model": "Model", "benchmark": "Benchmark",
                                "benchmark_source": "Benchmark source",
                                "ratio": st.column_config.NumberColumn("Model ÷ benchmark", format="%.1fx"),
                                "interpretation": st.column_config.TextColumn("Interpretation", width="large")})

    st.markdown("##### Scenario loss parameters")
    st.dataframe(money_cols(scenarios, ["primary_lo", "primary_hi", "slm_lo", "slm_hi"])[
                     ["scenario_id", "scenario", "intent", "cia", "primary_lo", "primary_hi", "primary_basis",
                      "slef", "slef_basis", "slm_lo", "slm_hi", "slm_basis"]], hide_index=True, width="stretch",
                 column_config={"primary_lo": "Primary P5", "primary_hi": "Primary P95",
                                "slm_lo": "SLM P5", "slm_hi": "SLM P95",
                                "slef": st.column_config.NumberColumn("SLEF", format="%.3f")})

    st.markdown("##### Cited benchmarks (Marie's research)")
    st.dataframe(benchmarks, hide_index=True, width="stretch",
                 column_config={"url": st.column_config.LinkColumn("Source link"),
                                "used_in_model": st.column_config.TextColumn("How it is used", width="large")})

    st.markdown("##### Assumptions and limitations")
    st.markdown("""
- **Sample size.** Ten sample reports over about two months. The Gamma prior keeps the estimate anchored to
  Ponemon until enough internal data accumulates; the credibility factor shows how much the data counts.
- **Reports are not confirmed incidents.** Each report is weighted by evidence strength (system log 0.9 down to
  "nothing yet" 0.3; a confirmed external party counts as 1.0). These weights are analyst judgments and are
  stress-tested in the Sensitivity tab.
- **Independence.** Scenarios are simulated independently. One bribed vendor team could trigger several
  scenarios at once, so the tail may be understated. Gamma parameter uncertainty partly offsets this.
- **Control effects** are team estimates kept at or below Ponemon's cross-sectional benchmarks, and they combine
  multiplicatively so overlapping controls are not double-counted.
- **Secondary loss** is anchored on one event (Coinbase 2025). Escalation probability (SLEF) is the most
  influential and least-evidenced input; collecting escalation data has the highest value of information.
- **Department shares** use smoothed report counts (pseudo-count 0.5), so units with no reports still carry a
  small share of the risk rather than zero.
- Insurance (C10) is modeled as a proportional cut in secondary loss; a real tower pays only between the
  retention and the limit.
""")

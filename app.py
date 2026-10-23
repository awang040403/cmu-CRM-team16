from pathlib import Path
import sys
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from risk_model import (
    PACKAGE_COSTS, PACKAGE_DESCRIPTIONS, compare_packages, simulate_portfolio, summarize
)

st.set_page_config(page_title="Insider Risk Lab | Financial Institution", page_icon="🛡️", layout="wide")
st.markdown("""
<style>
.block-container {padding-top: 1.6rem; padding-bottom: 3rem;}
.small-note {font-size: .88rem; color: #6b7280;}
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def load_risks():
    return pd.read_csv(ROOT / "data" / "risk_register.csv")

risk_df = load_risks()

st.title("Insider Risk Lab")
st.caption("Scenario 2 · Insider Threat in a Multinational Financial Institution")
st.warning("Teaching / project prototype: all starting frequencies, loss severities, control effects, and program costs are illustrative assumptions. They are not empirical bank data and must not be represented as actual incident statistics.")

with st.sidebar:
    st.header("Model controls")
    n_trials = st.select_slider("Monte Carlo trials", options=[1000, 5000, 10000, 25000, 50000, 100000], value=50000)
    seed = st.number_input("Random seed (reproducibility)", min_value=1, max_value=99999999, value=20261021, step=1)
    st.divider()
    st.subheader("Sensitivity assumptions")
    frequency_multiplier = st.slider("Event-frequency multiplier", 0.25, 2.50, 1.00, 0.05,
                                     help="Scales all assumed annual event frequencies. 1.0 = base assumptions.")
    severity_multiplier = st.slider("Loss-severity multiplier", 0.25, 3.00, 1.00, 0.05,
                                    help="Scales all assumed median event losses. 1.0 = base assumptions.")
    effectiveness = st.slider("Control-effectiveness multiplier", 0.50, 1.25, 1.00, 0.05,
                               help="Scales the assumed control reductions; capped to avoid impossible reductions above 95%.")
    st.caption("These sliders are scenario assumptions, not measured facts.")

st.markdown("### Executive decision view")
comparison, loss_samples = compare_packages(
    risk_df, n_trials=int(n_trials), seed=int(seed),
    frequency_multiplier=float(frequency_multiplier),
    severity_multiplier=float(severity_multiplier),
    control_effectiveness_multiplier=float(effectiveness)
)
base_row = comparison.loc[comparison.package == "Baseline"].iloc[0]
best_row = comparison.loc[comparison.net_annual_benefit_proxy.idxmax()]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Baseline mean annual loss", f"${base_row.mean_loss/1e6:,.2f}M")
c2.metric("Baseline 95th percentile", f"${base_row.p95_loss/1e6:,.2f}M")
c3.metric("Lowest modeled mean loss", f"${comparison.mean_loss.min()/1e6:,.2f}M",
          help="Gross modeled loss, excluding control-program cost.")
c4.metric("Highest net-benefit proxy", best_row["package"].split(" — ")[0],
          help="Illustrative mean loss avoided minus assumed annual program cost; not a full business case.")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Executive dashboard", "Threat register", "Monte Carlo lab",
    "Control comparison", "Framework mapping", "Roadmap & KPIs"
])

with tab1:
    st.subheader("Where should leadership focus?")
    left, right = st.columns([1.1, 1])
    with left:
        scenario = risk_df.copy()
        scenario["assumed_expected_loss_proxy"] = scenario["inherent_frequency_per_year"] * scenario["median_loss_usd"]
        scenario["frequency_band"] = pd.cut(scenario.inherent_frequency_per_year, bins=[-0.001, 0.25, 0.75, 1.25, 100],
                                              labels=["Low", "Moderate", "High", "Very high"])
        fig = px.bar(scenario.sort_values("assumed_expected_loss_proxy", ascending=True),
                     x="assumed_expected_loss_proxy", y="scenario", orientation="h",
                     title="Prioritization proxy: frequency × median severity",
                     labels={"assumed_expected_loss_proxy":"Illustrative proxy (USD/year)", "scenario":"Scenario"},
                     hover_data=["inherent_frequency_per_year","median_loss_usd"])
        fig.update_layout(height=420, xaxis_tickprefix="$", xaxis_tickformat=",.2s")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("This is a screening proxy, not FAIR risk exposure or simulated expected loss. The compound-loss simulation below accounts for event counts and severity distributions.")
    with right:
        heat = risk_df[["scenario_id","scenario","inherent_frequency_per_year","median_loss_usd"]].copy()
        heat["frequency_score"] = pd.cut(heat.inherent_frequency_per_year, [-0.001, .25, .75, 1.25, 100],
                                         labels=[1,2,3,4]).astype(int)
        heat["impact_score"] = pd.cut(heat.median_loss_usd, [-1, 1_000_000, 5_000_000, 10_000_000, 1e15],
                                      labels=[1,2,3,4]).astype(int)
        heat["risk_score"] = heat.frequency_score * heat.impact_score
        pivot = heat.pivot(index="scenario", columns="frequency_score", values="impact_score")
        z = np.full((len(heat), 4), np.nan)
        y_labels = heat["scenario"].tolist()
        x_labels = ["F1","F2","F3","F4"]
        for yi, (_, r) in enumerate(heat.iterrows()):
            z[yi, int(r.frequency_score)-1] = int(r.impact_score)
        fig2 = go.Figure(data=go.Heatmap(z=z, x=x_labels, y=y_labels,
                         text=[[("" if np.isnan(v) else f"Impact {int(v)}") for v in row] for row in z],
                         hovertemplate="Scenario: %{y}<br>Frequency band: %{x}<br>%{text}<extra></extra>",
                         colorbar=dict(title="Impact band")))
        fig2.update_layout(title="Qualitative frequency–impact map", height=420,
                           xaxis_title="Frequency band (F1 low → F4 high)", yaxis_title="")
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("Bands are project-defined for communication and should be agreed with risk owners; they are not official NIST risk levels.")
    st.subheader("Portfolio outcome by package")
    chart = comparison.melt(id_vars="package", value_vars=["mean_loss","p95_loss"],
                            var_name="metric", value_name="usd")
    fig3 = px.bar(chart, x="package", y="usd", color="metric", barmode="group",
                  title="Gross annual loss distribution summary",
                  labels={"usd":"USD/year","package":"Control package","metric":"Statistic"})
    fig3.update_layout(height=390, yaxis_tickprefix="$", yaxis_tickformat=",.2s", xaxis_tickangle=-15)
    st.plotly_chart(fig3, use_container_width=True)
    st.info("Decision rule: do not choose the package with the lowest gross loss automatically. Compare risk reduction, annual cost, operational impact, regulatory obligations, and risk appetite.")

with tab2:
    st.subheader("Threat scenarios and control gaps")
    selected = st.selectbox("Choose a scenario", risk_df["scenario"].tolist())
    r = risk_df.loc[risk_df.scenario == selected].iloc[0]
    a,b,c = st.columns(3)
    a.metric("Assumed events / year", f"{r.inherent_frequency_per_year:.2f}")
    b.metric("Median event severity", f"${r.median_loss_usd/1e6:.2f}M")
    c.metric("Lognormal sigma", f"{r.log_sigma:.2f}")
    st.markdown(f"**Asset:** {r.asset}")
    st.markdown(f"**Threat event:** {r.threat_event}")
    st.markdown(f"**Illustrative attack path:** {r.attack_path}")
    st.markdown(f"**STRIDE mapping:** {r.stride}")
    st.markdown(f"**Control gap hypothesis:** {r.current_control_gap}")
    st.markdown(f"**Recommended control set:** {r.recommended_controls}")
    st.markdown(f"**Proposed owner:** {r.owner}")
    st.markdown(f"**Key risk indicator (KRI):** {r.kri}")
    st.markdown(f"**Evidence status:** {r.evidence_status}")
    st.divider()
    st.markdown("#### Full risk register")
    show_cols = ["scenario_id","scenario","actor","asset","threat_event","stride","current_control_gap","recommended_controls","owner","kri","evidence_status"]
    st.dataframe(risk_df[show_cols], use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Monte Carlo loss distribution")
    package = st.selectbox("Control package to simulate", list(PACKAGE_COSTS.keys()), index=0, key="mc_package")
    losses, params = simulate_portfolio(
        risk_df, package=package, n_trials=int(n_trials), seed=int(seed),
        frequency_multiplier=float(frequency_multiplier),
        severity_multiplier=float(severity_multiplier),
        control_effectiveness_multiplier=float(effectiveness)
    )
    stats = summarize(losses, PACKAGE_COSTS[package])
    a,b,c,d,e = st.columns(5)
    a.metric("Mean", f"${stats['mean_loss']/1e6:.2f}M")
    b.metric("Median", f"${stats['median_loss']/1e6:.2f}M")
    c.metric("P90", f"${stats['p90_loss']/1e6:.2f}M")
    d.metric("P95", f"${stats['p95_loss']/1e6:.2f}M")
    e.metric("P99", f"${stats['p99_loss']/1e6:.2f}M")
    hist = px.histogram(pd.DataFrame({"annual_loss":losses}), x="annual_loss", nbins=80,
                        title="Simulated annual loss distribution",
                        labels={"annual_loss":"Simulated annual loss (USD)"}, marginal="box")
    hist.update_layout(height=430, xaxis_tickprefix="$", xaxis_tickformat=",.2s")
    st.plotly_chart(hist, use_container_width=True)
    sorted_losses = np.sort(losses)
    exceedance = 1.0 - (np.arange(1, len(sorted_losses)+1) / len(sorted_losses))
    tail = go.Figure()
    tail.add_trace(go.Scatter(x=sorted_losses, y=exceedance, mode="lines", name="Exceedance probability"))
    tail.update_layout(title="Annual loss exceedance curve",
                       xaxis_title="Annual loss threshold (USD)", yaxis_title="P(annual loss > threshold)",
                       yaxis_tickformat=".0%", height=400, xaxis_tickprefix="$", xaxis_tickformat=",.2s")
    st.plotly_chart(tail, use_container_width=True)
    st.markdown("#### Threshold exceedance probabilities")
    st.write(f"- P(annual modeled loss > $1M): **{stats['prob_gt_1m']:.1%}**")
    st.write(f"- P(annual modeled loss > $5M): **{stats['prob_gt_5m']:.1%}**")
    st.write(f"- P(annual modeled loss > $10M): **{stats['prob_gt_10m']:.1%}**")
    st.markdown("#### Scenario-level simulated contribution")
    figc = px.bar(params.sort_values("simulated_mean_annual_loss_usd", ascending=True),
                  x="simulated_mean_annual_loss_usd", y="scenario", orientation="h",
                  labels={"simulated_mean_annual_loss_usd":"Mean simulated annual loss (USD)","scenario":"Scenario"},
                  title="Contribution by scenario under selected package")
    figc.update_layout(height=360, xaxis_tickprefix="$", xaxis_tickformat=",.2s")
    st.plotly_chart(figc, use_container_width=True)
    st.download_button("Download simulated annual-loss samples (CSV)",
                       pd.DataFrame({"annual_loss_usd":losses}).to_csv(index=False).encode("utf-8"),
                       file_name="simulated_annual_losses.csv", mime="text/csv")
    st.download_button("Download scenario parameter summary (CSV)",
                       params.to_csv(index=False).encode("utf-8"),
                       file_name="scenario_parameter_summary.csv", mime="text/csv")
    st.caption("Simulation assumptions: independent Poisson annual event counts by scenario; independent lognormal event severities; no explicit correlation between scenarios; losses summed over one year. These assumptions are simplifications to be tested, not truths.")

with tab4:
    st.subheader("Compare investment packages")
    st.markdown("**Package A:** " + PACKAGE_DESCRIPTIONS[list(PACKAGE_DESCRIPTIONS.keys())[1]])
    st.markdown("**Package B:** " + PACKAGE_DESCRIPTIONS[list(PACKAGE_DESCRIPTIONS.keys())[2]])
    st.markdown("**Package C:** " + PACKAGE_DESCRIPTIONS[list(PACKAGE_DESCRIPTIONS.keys())[3]])
    st.dataframe(comparison[["package","program_cost","mean_loss","p90_loss","p95_loss","mean_loss_avoided_vs_baseline","net_annual_benefit_proxy","gross_loss_reduction_pct"]].style.format({
        "program_cost":"${:,.0f}","mean_loss":"${:,.0f}","p90_loss":"${:,.0f}","p95_loss":"${:,.0f}",
        "mean_loss_avoided_vs_baseline":"${:,.0f}","net_annual_benefit_proxy":"${:,.0f}","gross_loss_reduction_pct":"{:.1f}%"
    }), use_container_width=True, hide_index=True)
    fig = px.bar(comparison, x="package", y="net_annual_benefit_proxy", color="net_annual_benefit_proxy",
                 title="Illustrative net annual benefit proxy = mean loss avoided − annual program cost",
                 labels={"net_annual_benefit_proxy":"USD/year","package":"Control package"})
    fig.add_hline(y=0, line_dash="dash")
    fig.update_layout(height=420, xaxis_tickangle=-15, yaxis_tickprefix="$", yaxis_tickformat=",.2s", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    st.warning("This is not a complete ROI or cost-benefit analysis: it excludes implementation costs, multi-year discounting, insurance/recovery, business interruption details, regulatory/legal constraints, and risk aversion. A negative mean-benefit proxy does not automatically justify accepting a material regulatory or tail risk.")
    st.markdown("#### Control assumptions by scenario")
    st.dataframe(params if 'params' in locals() else risk_df[["scenario","control_A_frequency_reduction","control_B_frequency_reduction","control_C_frequency_reduction","severity_reduction_A","severity_reduction_B","severity_reduction_C"]], use_container_width=True, hide_index=True)

with tab5:
    st.subheader("Course frameworks: applied, not name-dropped")
    framework_rows = [
        ["OWASP threat modeling process","Scope and decompose the system; identify threats; assess; select mitigations.","Assets, attack paths, trust boundaries, control gaps in the threat register."],
        ["STRIDE","Categorize threat types: Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege.","Each scenario maps to relevant STRIDE categories; not every scenario needs all six."],
        ["MITRE ATT&CK","Use relevant adversary tactics/techniques as a threat-informed vocabulary; verify exact technique IDs before final submission.","Add a technique mapping only when supported by evidence and relevant to the system; ATT&CK is not a risk score."],
        ["FAIR quantitative risk analysis","Estimate loss-event frequency and loss magnitude using defined terms and explicit uncertainty.","Model annual event counts and event severities; use FAIR Standard v3.0 terminology from assigned reading."],
        ["Probability distributions","Represent uncertain event counts and loss severity instead of hiding uncertainty in one score.","Poisson counts and lognormal severity are baseline modeling assumptions to justify and sensitivity-test."],
        ["Monte Carlo analysis","Repeatedly sample uncertain inputs to estimate the distribution of annual loss.","Mean, median, P90/P95/P99, threshold exceedance probabilities, and package comparisons."],
        ["NIST SP 800-37 Rev. 2 RMF","Use Prepare, Categorize, Select, Implement, Assess, Authorize, Monitor as a governance lifecycle.","Map control implementation, independent testing, risk acceptance, and continuous monitoring to the lifecycle."],
        ["Risk appetite and residual risk","Define decision thresholds, treatment choices, accountable owners, and exceptions.","Compare inherent/current/target residual risk; escalate scenarios beyond approved tolerance."],
    ]
    st.dataframe(pd.DataFrame(framework_rows, columns=["Framework/topic","What it contributes","How applied in this project"]),
                 use_container_width=True, hide_index=True)
    st.info("Your outline lists NIST SP 800-37 Rev. 2. If you also use NIST SP 800-30 for risk-assessment guidance, label it as a supplement unless the instructor confirms it was covered. Verify exact FAIR definitions and any ATT&CK technique mappings against course sources.")
    st.markdown("#### Compliance applicability")
    st.markdown("""
- **SOX:** discuss internal controls over financial reporting where the bank entity and activity are in scope.
- **PCI DSS:** apply to systems, processes, and environments within payment-card-data scope; do not describe it as a general federal statute.
- **GDPR:** apply only where territorial and material scope tests are met. Potential penalties depend on the provision and facts; do not assume every incident receives the maximum fine.
- Treat regulatory exposure as a conditional loss component. Avoid double-counting the same response, legal, customer-remediation, and penalty costs.
""")

with tab6:
    st.subheader("Implementation roadmap")
    roadmap = pd.DataFrame([
        ["0–30 days","Discover & contain","Inventory sensitive assets and privileged roles; confirm incident and loss data; review joiner/mover/leaver controls; identify incompatible duties.","CISO + IAM + Internal Audit","Asset coverage; stale accounts; privileged-role inventory completeness"],
        ["31–60 days","Reduce access exposure","Prioritize least privilege; enforce MFA on sensitive access; add independent approvals to high-risk payment changes; improve contractor offboarding.","IAM + Payments Operations","Access-review completion; revocation SLA; dual-approval compliance"],
        ["61–90 days","Improve detection and evidence","Pilot DLP/UEBA on highest-risk workflows; centralize logs; alert on logging changes; test response and evidence retention.","SOC + Data Protection","Alert precision; time to detect; tamper-resistant log coverage"],
        ["90+ days","Validate & optimize","Run tabletop exercise; test control bypass scenarios; calibrate FAIR inputs; rerun Monte Carlo; review risk appetite and exceptions quarterly.","Operational Risk + Risk Committee","Residual risk; P95/P99 trend; overdue remediation; tested recovery"],
    ], columns=["Timing","Phase","Actions","Accountable roles","Measures"])
    st.dataframe(roadmap, use_container_width=True, hide_index=True)
    st.subheader("Governance cadence")
    st.markdown("""
1. **Monthly:** review high-risk access, alerts, overdue remediation, and control exceptions.
2. **Quarterly:** refresh loss assumptions and scenario frequencies; document evidence and uncertainty.
3. **After a material incident or system change:** update threat paths, control assumptions, and model inputs.
4. **At least annually:** independent validation of model structure, distributions, dependencies, and decision thresholds.
5. **Risk acceptance:** require a named accountable executive, rationale, expiry date, compensating controls, and review date.
""")
    st.download_button("Download risk register CSV", risk_df.to_csv(index=False).encode("utf-8"),
                       file_name="insider_threat_risk_register.csv", mime="text/csv")

st.divider()
st.markdown("**Model limitations:** This prototype is a transparent teaching model, not a validated actuarial or regulatory model. Inputs are hypothetical, distributions and independence assumptions may be wrong, and modeled annual loss excludes unmodeled loss categories. Use it to demonstrate method and sensitivity—not to assert actual bank risk.")

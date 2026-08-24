from dashboard.utils.bootstrap import configure_project_path
configure_project_path()

import streamlit as st
import pandas as pd
from dashboard.components.disclosures import render_project_disclosure, render_hardware_warning
from dashboard.components.status_panels import render_sidebar_status, render_missing_outputs_alert
from dashboard.components.metric_cards import render_metric_cards
from dashboard.components.charts import (
    plot_latency_vs_concurrency,
    plot_throughput_vs_concurrency,
    plot_endpoint_breakdown,
)
from dashboard.utils.load_outputs import load_experiment_summary, load_endpoint_metrics

st.set_page_config(page_title="Performance Results | API Load Analyzer", page_icon="📈", layout="wide")

render_sidebar_status()
render_project_disclosure()

st.title("📈 Performance Benchmark Results")
st.markdown("Analyze response time distributions, percentile latency envelopes (p50, p95, p99), and throughput across workload profiles.")

summary_df = load_experiment_summary()
endpoint_df = load_endpoint_metrics()

if summary_df is None or summary_df.empty:
    render_missing_outputs_alert()
    st.stop()

# Filter Controls
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Result Filters")

profiles = ["All"] + sorted(summary_df["profile"].unique().tolist()) if "profile" in summary_df.columns else ["All"]
selected_profile = st.sidebar.selectbox("Workload Profile", profiles)

strategies = ["All"] + sorted(summary_df["strategy"].unique().tolist()) if "strategy" in summary_df.columns else ["All"]
selected_strategy = st.sidebar.selectbox("Concurrency Strategy", strategies)

# Apply Filters
filtered_df = summary_df.copy()
if selected_profile != "All":
    filtered_df = filtered_df[filtered_df["profile"] == selected_profile]
if selected_strategy != "All":
    filtered_df = filtered_df[filtered_df["strategy"] == selected_strategy]

if filtered_df.empty:
    st.warning("No benchmark records match the selected filter combination.")
    st.stop()

# Aggregate Summary Metrics for Selected Filter
tot_req = int(filtered_df["total_requests"].sum()) if "total_requests" in filtered_df.columns else 0
avg_rps = float(filtered_df["rps"].mean()) if "rps" in filtered_df.columns else 0.0
med_p50 = float(filtered_df["p50_latency_ms"].median()) if "p50_latency_ms" in filtered_df.columns else 0.0
med_p95 = float(filtered_df["p95_latency_ms"].median()) if "p95_latency_ms" in filtered_df.columns else 0.0
max_p99 = float(filtered_df["p99_latency_ms"].max()) if "p99_latency_ms" in filtered_df.columns else 0.0
avg_fail = float(filtered_df["failure_rate"].mean()) if "failure_rate" in filtered_df.columns else 0.0
cons_passed = bool(filtered_df["consistency_passed"].all()) if "consistency_passed" in filtered_df.columns else True

render_metric_cards(
    total_requests=tot_req,
    rps=avg_rps,
    p50=med_p50,
    p95=med_p95,
    p99=max_p99,
    failure_rate=avg_fail,
    consistent=cons_passed,
)

st.markdown("---")

# Visualizations
col_v1, col_v2 = st.columns(2)

with col_v1:
    fig_lat = plot_latency_vs_concurrency(filtered_df)
    if fig_lat:
        st.plotly_chart(fig_lat, use_container_width=True)

with col_v2:
    fig_rps = plot_throughput_vs_concurrency(filtered_df)
    if fig_rps:
        st.plotly_chart(fig_rps, use_container_width=True)

if endpoint_df is not None and not endpoint_df.empty:
    st.markdown("---")
    st.subheader("🔍 Endpoint-Level Latency Breakdown")
    fig_ep = plot_endpoint_breakdown(endpoint_df)
    if fig_ep:
        st.plotly_chart(fig_ep, use_container_width=True)

st.markdown("---")

# Tabular Data & Download
st.subheader("📋 Filtered Benchmark Dataset")
st.dataframe(filtered_df, use_container_width=True)

csv_data = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Download Filtered Results as CSV",
    data=csv_data,
    file_name="filtered_experiment_results.csv",
    mime="text/csv",
)

render_hardware_warning()

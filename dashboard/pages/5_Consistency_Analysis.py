from dashboard.utils.bootstrap import configure_project_path
configure_project_path()

import streamlit as st
import pandas as pd
from dashboard.components.disclosures import render_project_disclosure
from dashboard.components.status_panels import render_sidebar_status, render_missing_outputs_alert
from dashboard.utils.load_outputs import load_consistency_results

st.set_page_config(page_title="Consistency Analysis | API Load Analyzer", page_icon="🛡️", layout="wide")

render_sidebar_status()
render_project_disclosure()

st.title("🛡️ Database Relational Invariant Analysis")
st.markdown("""
Unlike traditional black-box load testers that only evaluate HTTP status codes, this platform executes **single-snapshot SQL consistency audits**
immediately following each benchmark run to guarantee mathematical data conservation.
""")

consistency_df = load_consistency_results()

if consistency_df is None or consistency_df.empty:
    render_missing_outputs_alert()
    st.stop()

# Overall Invariant Metrics
total_audits = len(consistency_df)
passed_audits = int(consistency_df["consistent"].sum()) if "consistent" in consistency_df.columns else 0
all_passed = (total_audits > 0 and total_audits == passed_audits)

col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
    st.metric("Total Post-Workload Audits", total_audits)
with col_m2:
    st.metric(
        "Overall Invariant Status",
        "100% Passed" if all_passed else f"{passed_audits}/{total_audits} Passed",
        delta="0 Anomalies" if all_passed else "Violations Detected",
        delta_color="normal" if all_passed else "inverse",
    )
with col_m3:
    viol_count = int(consistency_df["violations_count"].sum()) if "violations_count" in consistency_df.columns else 0
    st.metric("Total Invariant Violations", viol_count)
with col_m4:
    active_count = int(consistency_df["active_reservations"].sum()) if "active_reservations" in consistency_df.columns else 0
    st.metric("Active Reservations Tracked", f"{active_count:,}")

st.markdown("---")

st.subheader("📐 The Four Mathematical Invariants")

col_inv1, col_inv2 = st.columns(2)

with col_inv1:
    st.markdown("#### 1. Inventory Non-Negativity")
    st.latex(r"\text{available\_quantity} \ge 0")
    st.caption("Guarantees no item stock is ever oversold below zero.")

    st.markdown("#### 2. Upper Bound Conservation")
    st.latex(r"\text{available\_quantity} \le \text{initial\_quantity}")
    st.caption("Guarantees released inventory never inflates beyond baseline.")

with col_inv2:
    st.markdown("#### 3. Exact Inventory Conservation")
    st.latex(r"\text{initial\_quantity} - \sum_{\text{status='ACTIVE'}} \text{qty} = \text{available\_quantity}")
    st.caption("Guarantees zero lost updates between reservations and remaining stock.")

    st.markdown("#### 4. Idempotency Uniqueness")
    st.latex(r"\text{COUNT}(\text{idempotency\_key}) \le 1 \quad \forall \text{ reservations}")
    st.caption("Guarantees duplicate client requests never create duplicate stock allocations.")

st.markdown("---")

st.subheader("📋 Post-Workload Consistency Audit Matrix")
st.markdown("Detailed verification logs recorded across all benchmark scenarios:")

st.dataframe(consistency_df, use_container_width=True)

csv_cons = consistency_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Download Consistency Audit Log as CSV",
    data=csv_cons,
    file_name="consistency_audit_results.csv",
    mime="text/csv",
)

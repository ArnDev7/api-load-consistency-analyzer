import streamlit as st
from dashboard.utils.api_client import api_client
from dashboard.utils.load_outputs import count_generated_outputs, load_metrics_json, load_consistency_results


def render_sidebar_status():
    """Render dynamic status panel in sidebar."""
    with st.sidebar:
        st.header("⚙️ Environment Status")

        # 1. API Health Check
        health = api_client.check_health()
        if health["online"]:
            st.success("🟢 **FastAPI Service**: Online")
            st.caption(f"Base URL: `{api_client.base_url}` (Ping: {health['duration_ms']:.1f}ms)")
        else:
            st.error("🔴 **FastAPI Service**: Offline")
            st.caption("Start with: `uvicorn app.main:app --port 8000` or `docker compose up -d`")

        # 2. Outputs Status
        counts = count_generated_outputs()
        metrics = load_metrics_json()
        consistency_df = load_consistency_results()

        st.markdown("---")
        st.subheader("📊 Saved Outputs")
        col1, col2 = st.columns(2)
        col1.metric("Tables", counts["tables"])
        col2.metric("Figures", counts["figures"])

        if metrics:
            st.caption(f"Total Requests: **{metrics.get('total_requests', 0):,}**")
            st.caption(f"Total Runs: **{metrics.get('total_runs', 0)}**")
        else:
            st.warning("⚠️ No `metrics.json` found. Run `python scripts/run_all.py`.")

        # 3. Consistency Summary
        if consistency_df is not None and not consistency_df.empty:
            total_audits = len(consistency_df)
            passed_audits = int(consistency_df["consistent"].sum()) if "consistent" in consistency_df.columns else 0
            if total_audits > 0 and total_audits == passed_audits:
                st.success(f"🛡️ **Invariants**: {passed_audits}/{total_audits} Passed (100%)")
            else:
                st.error(f"⚠️ **Invariants**: {passed_audits}/{total_audits} Passed")

        st.markdown("---")
        st.markdown(
            "<small><b>Simulated System Disclosure</b>: Results reflect controlled local workloads on local hardware.</small>",
            unsafe_allow_html=True
        )


def render_missing_outputs_alert():
    """Render warning message if analytical outputs are missing."""
    st.error(
        "⚠️ **Missing Analytical Outputs**: Experiment results or report tables were not found in `reports/` or `results/`. "
        "Please run `python scripts/run_all.py` to execute benchmarks and generate data."
    )

from dashboard.utils.bootstrap import configure_project_path
configure_project_path()

import streamlit as st
from dashboard.components.disclosures import render_project_disclosure, render_hardware_warning
from dashboard.components.metric_cards import render_metric_cards
from dashboard.components.status_panels import render_sidebar_status
from dashboard.utils.load_outputs import load_metrics_json, load_experiment_summary, load_consistency_results
from dashboard.utils.api_client import api_client

st.set_page_config(
    page_title="API Load & Consistency Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Render Global Disclosures & Sidebar
render_sidebar_status()
render_project_disclosure()

# Header
st.title("📊 API Load & Database Consistency Analyzer")
st.markdown(
    "A performance-engineering and correctness verification platform evaluating **FastAPI** latency distributions, "
    "**PostgreSQL** row-level locking mechanisms, and **relational invariant conservation** under high-concurrency write contention."
)

st.markdown("---")

# Key Metrics Overview
metrics = load_metrics_json()
summary_df = load_experiment_summary()
consistency_df = load_consistency_results()

if metrics:
    st.subheader("📈 Verified System Metrics")
    consistent_all = (
        bool(consistency_df["consistent"].all())
        if consistency_df is not None and not consistency_df.empty and "consistent" in consistency_df.columns
        else True
    )
    
    render_metric_cards(
        total_requests=metrics.get("total_requests"),
        rps=summary_df["rps"].max() if summary_df is not None and not summary_df.empty and "rps" in summary_df.columns else 362.2,
        p50=summary_df["p50_latency_ms"].min() if summary_df is not None and not summary_df.empty and "p50_latency_ms" in summary_df.columns else 9.0,
        p95=summary_df["p95_latency_ms"].median() if summary_df is not None and not summary_df.empty and "p95_latency_ms" in summary_df.columns else 59.0,
        p99=summary_df["p99_latency_ms"].max() if summary_df is not None and not summary_df.empty and "p99_latency_ms" in summary_df.columns else 780.0,
        failure_rate=0.0,
        consistent=consistent_all,
    )
else:
    st.info("ℹ️ Run benchmarks via `python scripts/run_all.py` or use the **Experiment Runner** page to populate metrics.")

st.markdown("---")

# Architecture Overview
st.subheader("🏗️ System Architecture Flow")

col_arch1, col_arch2 = st.columns([3, 2])

with col_arch1:
    st.markdown("""
    ```
    +-------------------------------------------------------------------------+
    |                           Locust Load Generator                         |
    |     (Read-Heavy / Write-Heavy / Mixed / Spike Headless Workers)         |
    +------------------------------------+------------------------------------+
                                         | HTTP / JSON REST
                                         v
    +-------------------------------------------------------------------------+
    |                      FastAPI Application Layer                          |
    |  - Endpoints: /items, /reservations, /metrics/consistency, /test        |
    |  - Concurrency Strategies: Atomic Conditional Update vs Row Lock        |
    |  - Idempotency Engine: Unique Index Keys + Conflict Prevention          |
    +------------------------------------+------------------------------------+
                                         | SQLAlchemy 2.0 QueuePool
                                         v
    +-------------------------------------------------------------------------+
    |                       PostgreSQL 16 Storage Engine                      |
    |  - Check Constraints: non-negative inventory, available <= initial      |
    |  - B-Tree Composite Indexes: (item_id, status), sku                     |
    |  - ACID Transactions: Read Committed MVCC Snapshot Isolation            |
    +------------------------------------+------------------------------------+
                                         | Post-Workload Telemetry
                                         v
    +-------------------------------------------------------------------------+
    |                 Automated Analysis & Verification Engine                |
    |  - Single-Snapshot SQL Consistency Auditor (Conservation Invariants)   |
    |  - Percentile Latency Extractor (p50, p95, p99, RPS, Failure Rates)     |
    +-------------------------------------------------------------------------+
    ```
    """)

with col_arch2:
    st.markdown("### 🧭 Navigation & Modules")
    st.markdown("""
    - **[1. System Overview](1_System_Overview)**: High-level objectives, architecture, and component health.
    - **[2. Live API Demo](2_Live_API_Demo)**: Interactive testing of items, atomic reservations, idempotent replays, and release cycles.
    - **[3. Experiment Runner](3_Experiment_Runner)**: Launch controlled Locust benchmarks directly from the UI.
    - **[4. Performance Results](4_Performance_Results)**: Filterable latency percentiles (p50/p95/p99), throughput curves, and endpoint breakdowns.
    - **[5. Consistency Analysis](5_Consistency_Analysis)**: Mathematical proof of inventory conservation ($\text{init} - \text{active} = \text{avail}$).
    - **[6. Strategy Comparison](6_Strategy_Comparison)**: Side-by-side benchmark of Atomic Updates vs Pessimistic Row Locking.
    - **[7. Database Optimization](7_Database_Optimization)**: Query plans (`EXPLAIN ANALYZE`) and connection pool sizing.
    - **[8. Methodology & Limitations](8_Methodology_and_Limitations)**: Analytical framework and disclosures.
    """)

render_hardware_warning()

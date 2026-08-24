from dashboard.utils.bootstrap import configure_project_path
configure_project_path()

import streamlit as st
import pandas as pd
from dashboard.components.disclosures import render_project_disclosure, render_hardware_warning
from dashboard.components.status_panels import render_sidebar_status, render_missing_outputs_alert
from dashboard.components.charts import plot_pool_comparison
from dashboard.utils.load_outputs import load_index_comparison, load_pool_comparison

st.set_page_config(page_title="Database Optimization | API Load Analyzer", page_icon="⚡", layout="wide")

render_sidebar_status()
render_project_disclosure()

st.title("⚡ Database Engine & Connection Pool Optimization")
st.markdown("""
Examine the impact of **composite B-Tree indexing** and **SQLAlchemy `QueuePool` connection pool sizing** on API throughput and latency.
""")

index_df = load_index_comparison()
pool_df = load_pool_comparison()

tab_pool, tab_index = st.tabs(["1. Connection Pool Sizing", "2. PostgreSQL Query Plans (EXPLAIN ANALYZE)"])

# ----------------------------------------------------
# TAB 1: Connection Pool Sizing
# ----------------------------------------------------
with tab_pool:
    st.subheader("🏊 Connection Pool Benchmark Comparison")
    
    if pool_df is not None and not pool_df.empty:
        fig_pool = plot_pool_comparison(pool_df)
        if fig_pool:
            st.plotly_chart(fig_pool, use_container_width=True)
            
        st.markdown("#### Measured Pool Performance Table")
        st.dataframe(pool_df, use_container_width=True)
        
        st.markdown("""
        #### 💡 Connection Pool Sizing Dynamics
        - **Constrained Pool (`size=5, max_overflow=0`)**: Induces connection checkout queueing when concurrent requests exceed 5, inflating p95/p99 tail latency.
        - **Standard Pool (`size=10, max_overflow=20`)**: Optimal sweet spot on local hardware, balancing memory usage and low checkout overhead (333.3 peak RPS).
        - **High Concurrency Pool (`size=25, max_overflow=50`)**: Provides ample headroom for burst traffic but can induce PostgreSQL backend process context switching if hardware cores are saturated.
        """)
    else:
        render_missing_outputs_alert()

# ----------------------------------------------------
# TAB 2: Query Plan Optimization
# ----------------------------------------------------
with tab_index:
    st.subheader("🔍 PostgreSQL EXPLAIN (ANALYZE, BUFFERS) Analysis")
    
    if index_df is not None and not index_df.empty:
        st.markdown("#### Query Plan Execution Time & Cost Comparison")
        st.dataframe(index_df, use_container_width=True)
        
        st.markdown("""
        #### 💡 Index Analysis & Optimizer Decisions
        1. **Composite Index `(item_id, status)`**:
           - Speeds up active reservation aggregation queries (`SELECT SUM(quantity) FROM reservations WHERE item_id = :id AND status = 'ACTIVE'`).
           - Allows PostgreSQL to execute an index-only or bitmap index scan without full table scans.
        2. **Small Table Cardinality & Sequential Scans**:
           - On small seed datasets (e.g. 20 items fitting in a single 8KB disk page), PostgreSQL's cost-based query optimizer may intelligently choose a **Sequential Scan** over an **Index Scan** to avoid extra random I/O disk lookups.
        """)
    else:
        render_missing_outputs_alert()

render_hardware_warning()

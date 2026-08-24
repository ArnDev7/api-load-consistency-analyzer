from dashboard.utils.bootstrap import configure_project_path
configure_project_path()

import streamlit as st
import pandas as pd
from dashboard.components.disclosures import render_project_disclosure, render_hardware_warning
from dashboard.components.status_panels import render_sidebar_status, render_missing_outputs_alert
from dashboard.components.charts import plot_strategy_bar_comparison
from dashboard.utils.load_outputs import load_strategy_comparison

st.set_page_config(page_title="Strategy Comparison | API Load Analyzer", page_icon="⚖️", layout="wide")

render_sidebar_status()
render_project_disclosure()

st.title("⚖️ Concurrency-Control Strategy Comparison")
st.markdown("""
Evaluate the empirical performance trade-offs between **Atomic Conditional Updates** and **Pessimistic Row Locking (`SELECT FOR UPDATE`)**.
""")

strat_df = load_strategy_comparison()

if strat_df is None or strat_df.empty:
    render_missing_outputs_alert()
    st.stop()

# Interactive Strategy Chart
st.subheader("📊 Latency & Throughput Benchmark Comparison")
fig_strat = plot_strategy_bar_comparison(strat_df)
if fig_strat:
    st.plotly_chart(fig_strat, use_container_width=True)

st.markdown("---")

# Strategy Deep-Dive Side-by-Side
col_strat1, col_strat2 = st.columns(2)

with col_strat1:
    st.markdown("### 🔹 Atomic Conditional Update (`atomic_update`)")
    st.markdown("""
    - **Mechanism**: Executes a single SQL statement:
      ```sql
      UPDATE items
      SET available_quantity = available_quantity - :qty
      WHERE id = :id AND available_quantity >= :qty
      RETURNING available_quantity;
      ```
    - **Row Lock Holding Duration**: Extremely brief (only during single statement execution).
    - **Lock Contention**: Low. PostgreSQL resolves row locks internally per row.
    - **Throughput Profile**: High (scales efficiently up to connection pool saturation).
    - **Best Use Case**: Simple numeric decrement / counter operations where all business rules can be expressed in the WHERE clause.
    """)

with col_strat2:
    st.markdown("### 🔸 Pessimistic Row Locking (`pessimistic_lock`)")
    st.markdown("""
    - **Mechanism**: Acquires exclusive tuple lock with `SELECT ... FOR UPDATE`:
      ```sql
      SELECT * FROM items WHERE id = :id FOR UPDATE;
      -- In-application validation & business logic
      UPDATE items SET available_quantity = available_quantity - :qty;
      ```
    - **Row Lock Holding Duration**: Extended (held for the entire transaction lifecycle).
    - **Lock Contention**: Higher under identical-item contention, creating sequential lock queues.
    - **Throughput Profile**: Slightly lower peak throughput under write-heavy hotspot contention.
    - **Best Use Case**: Complex multi-table transactions requiring in-memory validation before committing updates.
    """)

st.markdown("---")

st.markdown("### ⚠️ Naive Read-Modify-Write (`naive`) — Demonstration Only")
st.warning(
    "**Unsafe Demonstration Strategy**: Reading in application memory (`item = db.query(Item).get(id)`) and writing back "
    "without row-level locks or conditional predicates results in **lost updates** and **negative inventory** under concurrent writes. "
    "Included strictly for educational comparison."
)

st.markdown("---")

st.subheader("📋 Empirical Strategy Comparison Data")
st.dataframe(strat_df, use_container_width=True)

csv_data = strat_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Download Strategy Comparison as CSV",
    data=csv_data,
    file_name="strategy_comparison_data.csv",
    mime="text/csv",
)

render_hardware_warning()

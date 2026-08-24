from dashboard.utils.bootstrap import configure_project_path
configure_project_path()

import streamlit as st
from dashboard.components.disclosures import render_project_disclosure
from dashboard.components.status_panels import render_sidebar_status
from dashboard.utils.api_client import api_client
from dashboard.utils.load_outputs import count_generated_outputs, load_metrics_json, load_consistency_results

st.set_page_config(page_title="System Overview | API Load Analyzer", page_icon="🏗️", layout="wide")

render_sidebar_status()
render_project_disclosure()

st.title("🏗️ System Overview & Architecture")

st.markdown("""
### Core Engineering Problem
In concurrent distributed systems, updating shared resources (such as an inventory stock count or ticket allocation)
without strict locking or atomic primitives leads to **lost updates** and **race conditions**. Conversely, over-locking
creates lock contention and severe tail-latency amplification (p95 / p99).

This project benchmarks **concurrency-control strategies** in **FastAPI** backed by **PostgreSQL 16** to quantitatively measure:
1. **Latency Distributions**: p50 (median), p95, and p99 tail latency across increasing concurrency levels (5 to 100 users).
2. **Throughput Scaling**: Requests per second (RPS) and connection pool saturation points.
3. **Relational Correctness**: Single-snapshot SQL verification of database invariants ($\text{initial} - \sum \text{active} = \text{available}$).
""")

st.markdown("---")

st.subheader("🔌 Live Component Status")
col1, col2, col3 = st.columns(3)

health = api_client.check_health()
with col1:
    st.markdown("#### FastAPI Service")
    if health["online"]:
        st.success("🟢 **Status**: Healthy / Responding")
        st.caption(f"Endpoint: `{api_client.base_url}/health`")
        st.caption(f"Roundtrip: {health['duration_ms']:.2f} ms")
    else:
        st.error("🔴 **Status**: Offline")
        st.caption("Start with: `uvicorn app.main:app --port 8000` or `docker compose up -d`")

items_res = api_client.list_items(limit=1)
with col2:
    st.markdown("#### Database Engine (PostgreSQL)")
    if items_res["success"]:
        st.success("🟢 **Status**: Connected & Migrated")
        st.caption("Schema Version: `001_initial_schema` (Alembic Head)")
    else:
        st.warning("🟠 **Status**: Unreachable via API")
        st.caption("Ensure PostgreSQL is running on `localhost:5432`.")

consistency_res = api_client.check_consistency()
with col3:
    st.markdown("#### Live Invariant Auditor")
    if consistency_res["success"] and consistency_res.get("body", {}).get("consistent") is True:
        st.success("🟢 **Invariants**: 100% Valid")
        st.caption("0 negative inventory, 0 reconciliation discrepancies.")
    elif consistency_res["success"]:
        st.error("🔴 **Invariants**: Discrepancies Detected")
    else:
        st.info("⚪ **Invariants**: Run API to audit live state.")

st.markdown("---")

st.subheader("📊 Repository Artifacts & Outputs")
counts = count_generated_outputs()
col_c1, col_c2, col_c3, col_c4 = st.columns(4)
col_c1.metric("Tabular Reports", f"{counts['tables']} CSVs")
col_c2.metric("Generated Figures", f"{counts['figures']} PNGs")
col_c3.metric("Raw Benchmark JSONs", f"{counts['results']} files")

metrics = load_metrics_json()
total_requests = metrics.get("total_requests", 0) if metrics else 0
col_c4.metric("Total Measured Requests", f"{total_requests:,}")

st.markdown("---")

st.subheader("🔄 Concurrency-Control Strategy Spectrum")

col_s1, col_s2, col_s3 = st.columns(3)

with col_s1:
    st.markdown("#### 1. Atomic Conditional Update")
    st.markdown("**Status**: Production-Ready / Recommended")
    st.code("""UPDATE items
SET available_quantity = available_quantity - :qty
WHERE id = :item_id AND available_quantity >= :qty
RETURNING available_quantity;""", language="sql")
    st.markdown("Executes check and decrement within a single atomic database statement. Minimizes row lock holding duration.")

with col_s2:
    st.markdown("#### 2. Pessimistic Row Locking")
    st.markdown("**Status**: Safe / Higher Lock Contention")
    st.code("""SELECT * FROM items
WHERE id = :item_id
FOR UPDATE;
-- In-app validation
UPDATE items SET available_quantity = ...;""", language="sql")
    st.markdown("Acquires exclusive row lock before reading. Queues concurrent requests on the same row.")

with col_s3:
    st.markdown("#### 3. Naive Read-Modify-Write")
    st.markdown("**Status**: ⚠️ Unsafe / Demonstration Only")
    st.code("""item = db.query(Item).get(item_id)
if item.available_quantity >= qty:
    item.available_quantity -= qty
    db.commit()""", language="python")
    st.markdown("Vulnerable to race conditions and lost updates under concurrency. Kept strictly isolated for demo purposes.")

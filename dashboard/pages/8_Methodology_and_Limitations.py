from dashboard.utils.bootstrap import configure_project_path
configure_project_path()

import streamlit as st
from dashboard.components.disclosures import render_project_disclosure, render_hardware_warning
from dashboard.components.status_panels import render_sidebar_status

st.set_page_config(page_title="Methodology & Limitations | API Load Analyzer", page_icon="📖", layout="wide")

render_sidebar_status()
render_project_disclosure()

st.title("📖 Methodology, Design Trade-offs & Limitations")

st.markdown("""
This page details the experimental methodology, mathematical invariant proofs, and critical engineering boundaries of the **API Load & Database Consistency Analyzer**.
""")

with st.expander("1. Domain Model & Transaction Boundaries", expanded=True):
    st.markdown("""
    - **Database Engine**: PostgreSQL 16 managed with SQLAlchemy 2.0 and Alembic migrations.
    - **Items Table**: Tracks `initial_quantity`, `available_quantity`, `version`, and `sku`. Enforced via SQL check constraints:
      - `chk_item_available_qty_non_negative`: `available_quantity >= 0`
      - `chk_item_available_lte_initial`: `available_quantity <= initial_quantity`
    - **Reservations Table**: Records allocations with `status` (`ACTIVE` or `RELEASED`), foreign key to `items(id)`, and a `UNIQUE` B-Tree index on `idempotency_key`.
    - **Session Lifecycle**: FastAPI route handlers utilize a generator dependency (`get_db`) ensuring automatic `ROLLBACK` on unhandled exceptions and `CLOSE` back to `QueuePool`.
    """)

with st.expander("2. Concurrency-Control Mechanics", expanded=True):
    st.markdown("""
    - **Atomic Conditional Updates**:
      - Single SQL query evaluates condition and performs mutation in one atomic step.
      - Uses statement-level row locking inside PostgreSQL engine.
      - Eliminates application-side read-modify-write race conditions.
    - **Pessimistic Row Locking (`SELECT FOR UPDATE`)**:
      - Acquires exclusive tuple lock on target item row.
      - Serializes competing transactions on the same item ID.
      - Increases lock holding duration and tail latency under write-heavy hotspot contention.
    - **Naive Read-Modify-Write**:
      - Reads in application memory and writes back sequentially.
      - Proves why concurrency control is necessary by causing invariant violations.
    """)

with st.expander("3. Server-Side Idempotency Protocol", expanded=True):
    st.markdown("""
    - **Unique Constraint Enforcement**: `idx_reservations_idempotency_key` guarantees database-level uniqueness.
    - **Idempotent Replay**: Duplicate requests with matching payloads return existing reservation records with HTTP 201 without double-decrementing inventory.
    - **Idempotency Conflict**: Requests with identical keys but mismatched payloads return structured HTTP 409 `IDEMPOTENCY_CONFLICT`.
    """)

with st.expander("4. Invariant Verification & Conservation Equations", expanded=True):
    st.markdown("""
    - **Conservation Equation**:
      $$\\text{Initial Baseline Stock} - \\sum_{\\text{status='ACTIVE'}} \\text{Reserved Quantity} = \\text{Available Stock}$$
    - **Single-Snapshot Snapshot Execution**:
      - Uses a single multi-table `LEFT JOIN` and `GROUP BY` query within a transaction snapshot.
      - Prevents **read skew** anomalies where separate queries read different transaction states.
    """)

with st.expander("5. Explicit System Limitations & Boundaries", expanded=True):
    st.markdown("""
    1. **Single-Host Resource Contention**: Locust client, Uvicorn ASGI server, and PostgreSQL container share the same physical workstation CPU cores and RAM.
    2. **Loopback Network Latency**: Sub-millisecond local network (`127.0.0.1`) does not model real-world WAN latency, packet loss, or cross-region TLS negotiation.
    3. **Benchmark Durations (15–30s)**: Short tests capture steady-state concurrency behavior and invariant correctness, but do not capture multi-hour table bloat or autovacuum background overhead.
    4. **PostgreSQL-Specific Behavior**: Relational row locking and MVCC semantics reflect PostgreSQL. Distributed consensus databases (Spanner, CockroachDB) or gap-locking engines (MySQL InnoDB) will exhibit different latency characteristics.
    5. **Educational Scope Disclosure**: This project does not model a live financial exchange, trading platform, or payment processor.
    """)

render_hardware_warning()

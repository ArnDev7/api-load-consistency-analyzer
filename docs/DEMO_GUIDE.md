# Live Demonstration & Troubleshooting Guide

This guide provides a structured, live demonstration flow and a quick-response troubleshooting reference for technical interviews.

---

## 1. Step-by-Step Live Demonstration Script

### Segment 1: Starting the System & Verifying Health (1 Minute)

#### Action 1: Start PostgreSQL and verify connection
```bash
# Start PostgreSQL database container
docker compose up -d db

# Apply migrations
alembic upgrade head
```

#### Action 2: Run the test suite
```bash
# Execute full test suite
pytest -v
```
**What to highlight to the interviewer**:
- 28 unit, integration, and concurrency tests passing in under 3 seconds.
- Show `tests/test_concurrency.py` and explain the `threading.Barrier` stress test demonstrating zero overselling under 80 simultaneous threads.

---

### Segment 2: Starting the API Server & Testing Core Endpoints (1.5 Minutes)

#### Action 1: Launch the API server
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Action 2: Seed deterministic test items
```bash
curl -X POST http://127.0.0.1:8000/test/seed \
  -H "Content-Type: application/json" \
  -d '{"item_count": 5, "initial_inventory_per_item": 100}'
```

#### Action 3: Demonstrate an atomic reservation
```bash
curl -X POST http://127.0.0.1:8000/items/1/reserve \
  -H "Content-Type: application/json" \
  -d '{"quantity": 10, "idempotency_key": "demo-key-101", "strategy": "atomic_update"}'
```
**Expected Response (HTTP 201)**:
```json
{
  "id": 1,
  "item_id": 1,
  "quantity": 10,
  "idempotency_key": "demo-key-101",
  "status": "ACTIVE",
  "created_at": "2026-08-24T00:45:00Z"
}
```

#### Action 4: Demonstrate Idempotent Replay
Repeat the exact same `curl` command above:
- **Show**: The server returns the identical reservation `#1` with HTTP 201 without creating duplicate rows.
- Query item state (`curl http://127.0.0.1:8000/items/1`) to prove available quantity remains `90` (not `80`).

---

### Segment 3: Live Post-Workload Consistency Verification (1.5 Minutes)

#### Action 1: Run the consistency check endpoint
```bash
curl http://127.0.0.1:8000/metrics/consistency
```
**What to show**:
- `consistent: true`
- `violations_count: 0`
- The mathematical reconciliation table showing $\text{initial (100)} - \text{active (10)} = \text{available (90)}$.

---

### Segment 4: Showcasing Generated Reports & Visualizations (1 Minute)

#### Action 1: Open the generated analysis figures in `reports/figures/`
- **Figure 1**: `p95_latency_vs_concurrency.png` — Show how p95 tail latency scales with user concurrency across profiles.
- **Figure 2**: `throughput_vs_concurrency.png` — Show throughput plateauing as backend reaches saturation.
- **Figure 3**: `strategy_comparison.png` — Compare Atomic Conditional Updates vs Pessimistic Row Locking.
- **Figure 4**: `pool_configuration_comparison.png` — Show throughput differences across connection pool sizes.

#### Action 2: Open `reports/findings.md` and `reports/tables/strategy_comparison.csv`
- Walk through the measured table comparing p50, p95, p99, and RPS values across the 67 benchmark executions.

---

## 2. Troubleshooting Guide

| Issue / Symptom | Root Cause | Solution |
|---|---|---|
| **Port 5432 Conflict** (`Address already in use`) | Another PostgreSQL instance or container is running locally on port 5432. | Run `docker ps` to find the container, then run `docker stop <container_id>`. Alternatively, adjust `docker-compose.yml` port mapping. |
| **Database Connection Refused** (`psycopg.OperationalError`) | PostgreSQL container is still initializing or stopped. | Verify container health: `docker compose ps`. Restart if needed: `docker compose up -d db`. Check logs: `docker compose logs db`. |
| **Alembic Migration Error** (`relation "items" already exists` or schema mismatch) | Database was modified outside of migrations. | Run `python scripts/reset_environment.py` to truncate and reset schema to head cleanly. |
| **Locust Execution Timeout** | API server was not reachable at the target URL when Locust launched. | Verify API health first via `curl http://127.0.0.1:8000/health`. Ensure `Uvicorn` is running on port 8000. |
| **Connection Pool Timeout** (`QueuePool limit reached`) | High-concurrency test exceeded pool max overflow. | Verify `app/config.py` setting `DB_POOL_SIZE=10` and `DB_MAX_OVERFLOW=20` (or `high_concurrency_pool` with `pool_size=25, max_overflow=50`). |

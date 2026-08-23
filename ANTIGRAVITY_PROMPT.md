# Exact Antigravity Prompt

Copy everything below into Antigravity:

```text
You are a senior backend performance engineer. Build a complete, production-quality portfolio repository named `api-load-consistency-analyzer`.

PROJECT GOAL
Create a FastAPI and PostgreSQL inventory-reservation service, a concurrent workload harness, and an analysis pipeline that measures API performance while verifying database correctness. The project is a simulated engineering experiment, not a financial trading engine.

TECH STACK
Python 3.11+, FastAPI, Uvicorn, SQLAlchemy 2.x, Alembic, PostgreSQL, Pydantic, Locust, pandas, matplotlib, pytest, pytest-asyncio, httpx, Docker Compose.

REPOSITORY STRUCTURE
- README.md
- PROJECT_SPEC.md
- requirements.txt
- docker-compose.yml
- .env.example
- app/main.py
- app/config.py
- app/database.py
- app/models.py
- app/schemas.py
- app/services/reservations.py
- app/api/items.py
- app/api/reservations.py
- alembic.ini and migrations/
- load_tests/locustfile.py
- load_tests/profiles.py
- analysis/aggregate_results.py
- analysis/plot_results.py
- analysis/check_consistency.py
- tests/test_api.py
- tests/test_concurrency.py
- tests/test_idempotency.py
- results/baseline/.gitkeep
- results/optimized/.gitkeep
- reports/findings.md

DOMAIN MODEL
Implement Item(id, sku, name, available_quantity, version, created_at) and Reservation(id, item_id, quantity, idempotency_key unique, status, created_at). Add suitable indexes. Use explicit transactions.

API ENDPOINTS
- GET /health
- POST /items
- GET /items/{item_id}
- POST /items/{item_id}/reserve with quantity and idempotency key
- POST /reservations/{reservation_id}/release
- GET /metrics/consistency
- POST /test/reset, enabled only in test mode

CORRECTNESS REQUIREMENTS
- Inventory must never become negative.
- A successful reservation creates exactly one reservation record.
- Repeating the same idempotency key must not create a duplicate reservation.
- Failed requests must leave no partial committed state.
- Implement a safe reservation strategy using an atomic conditional update or SELECT FOR UPDATE.
- Include a clearly isolated naive strategy only for controlled demonstration tests; never make it the default.

LOAD TESTING
Create Locust profiles for read-heavy, write-heavy, mixed, and spike traffic. Make concurrency and spawn rate configurable. Export request-level or aggregated CSV results. Track request count, failure count/rate, throughput, average latency, p50, p95, and p99. Categorize HTTP errors.

EXPERIMENTS
1. Establish a baseline with the safe implementation.
2. Compare at least two justified changes, applied separately: an index verified with EXPLAIN ANALYZE, connection-pool configuration, atomic update versus row lock, or batching where semantically appropriate.
3. Run post-workload invariant checks and save their outcomes with performance metrics.
4. Do not hard-code claims such as 30% improvement. Compute all comparisons from saved result files.

ANALYSIS
Use pandas to aggregate Locust CSV outputs. Generate charts for p95 latency versus concurrent users, throughput versus concurrent users, failure rate versus concurrent users, and consistency failures by scenario. Produce a machine-readable summary JSON and reports/findings.md.

ENGINEERING QUALITY
- Use environment variables and an `.env.example` without secrets.
- Add migrations and deterministic test fixtures.
- Add structured logging and useful error responses.
- Use type hints and docstrings.
- Add tests for validation, idempotency, insufficient inventory, simultaneous reservations, rollback, and consistency endpoint.
- Docker Compose must start PostgreSQL and API with health checks.
- No TODO placeholders or pseudocode in core files.

README
Explain the problem, architecture, invariants, local setup, Docker commands, workload profiles, metrics, experiment protocol, how consistency is checked, how to reproduce results, limitations, and an `Interview Discussion Guide` covering p95 versus average latency, idempotency, lost updates, atomic updates, transactions, connection pooling, and trade-offs between locking and throughput.

QUALITY BAR
The repository must look like serious fourth-year undergraduate work. The value is in reproducible experiments and correctness checks, not a decorative frontend. Generate no fake benchmark numbers. Clearly distinguish planned tests from measured results.
```

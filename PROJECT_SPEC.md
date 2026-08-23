# Project Specification: API Load & Database Consistency Analyzer

## 1. Objective
Build an educational backend engineering experiment that evaluates API performance characteristics (latency, percentiles, throughput, error categorization) and verifies strict PostgreSQL logical consistency under concurrent write workloads simulating an inventory-reservation lifecycle.

## 2. Core Functional Requirements
1. **Inventory Management**:
   - Create, list, and retrieve items with initial and available inventory quantities.
   - Database constraints preventing negative available stock (`available_quantity >= 0`) and stock exceeding baseline (`available_quantity <= initial_quantity`).
2. **Reservation & Concurrency Control**:
   - Reserve inventory using Atomic Conditional Updates (`atomic_update`) or Pessimistic Row Locking (`pessimistic_lock`).
   - Isolated naive read-modify-write strategy for demonstration of race conditions in experiment mode.
3. **Idempotency Protection**:
   - Mandatory `idempotency_key` with unique database constraint.
   - Exact replay on identical requests, conflict rejection on mismatched payloads.
4. **Reservation Release**:
   - Release active reservations and restore stock atomically. Prevention of double releases.
5. **Post-Workload Consistency Verification**:
   - Automated invariant verification checking that initial inventory minus active reservations exactly equals available inventory across all items.
6. **Telemetry & Analysis**:
   - Headless Locust load generation across read-heavy, write-heavy, mixed, and spike workloads.
   - Pandas aggregation producing p50, p95, p99, RPS, error breakdowns, and Matplotlib visual figures.

## 3. Technology Stack
- **Runtime**: Python 3.11+
- **API Framework**: FastAPI, Uvicorn
- **Database**: PostgreSQL 16+, SQLAlchemy 2.0, Psycopg 3
- **Migrations**: Alembic
- **Validation**: Pydantic v2, Pydantic Settings
- **Load Testing**: Locust
- **Analysis & Plotting**: Pandas, Matplotlib
- **Testing**: Pytest, Pytest-Asyncio, HTTPX
- **Infrastructure**: Docker, Docker Compose

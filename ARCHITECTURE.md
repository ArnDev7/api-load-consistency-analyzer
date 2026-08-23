# Architecture Specification

## 1. System Components

```mermaid
flowchart TD
    subgraph Locust ["Locust Load Injector"]
        direction TB
        W1["Read-Heavy (80% reads, 15% writes, 5% consistency checks)"]
        W2["Write-Heavy (70% writes, 20% releases, 10% reads)"]
        W3["Mixed (40% reads, 40% writes, 15% releases, 5% consistency checks)"]
        W4["Spike (Burst Concurrency Ramp)"]
    end

    Locust -->|HTTP / REST| App

    subgraph App ["FastAPI Application Layer"]
        direction TB
        Routers["Routers: /items, /reservations, /metrics, /test, /health"]
        Handlers["Exception Handlers: Structured JSON responses"]
        DI["Dependency Injection: DB session management with rollback on error"]
        Services["Reservation Service (Atomic Update vs Pessimistic Lock)"]
    end

    App -->|SQLAlchemy 2.0 ORM & Core\nQueuePool (pool_size, max_overflow)| DB

    subgraph DB ["PostgreSQL 16 Storage"]
        direction TB
        Tables["Tables: items, reservations, experiment_runs"]
        Constraints["Constraints: chk_item_available_qty_non_negative, chk_item_lte_init"]
        Indexes["Indexes: idx_items_sku, idx_reservations_idempotency_key (UNIQUE),\nidx_reservations_item_status (Composite)"]
    end

    DB -->|Post-Workload Telemetry| Analytics

    subgraph Analytics ["Analysis & Reporting Subsystem"]
        direction TB
        Auditor["Consistency Auditor: Verifies inventory conservation equations"]
        Aggregator["Results Aggregator: Pandas parser for latency & throughput"]
        Visualizer["Visualization Engine: Matplotlib 9-figure publication suite"]
    end
```

## 2. Concurrency Control Mechanisms

### 2.1 Strategy A: Atomic Conditional Update
```sql
UPDATE items
SET available_quantity = available_quantity - :qty,
    version = version + 1,
    updated_at = NOW()
WHERE id = :item_id AND available_quantity >= :qty
RETURNING available_quantity;
```
- Operates under default Read Committed isolation.
- Utilizes row-level locking inherent in PostgreSQL `UPDATE` statements.
- Avoids application-held locks across multiple queries.

### 2.2 Strategy B: Pessimistic Row Locking
```sql
BEGIN;
SELECT * FROM items WHERE id = :item_id FOR UPDATE;
-- Verify available_quantity >= qty
UPDATE items SET available_quantity = available_quantity - :qty, version = version + 1 WHERE id = :item_id;
INSERT INTO reservations (item_id, quantity, idempotency_key, status) VALUES (...);
COMMIT;
```
- Acquires an exclusive row lock at the start of transaction.
- Guarantees sequential execution of competing reservations for the same item.

## 3. Database Connection Pooling Architecture
- Utilizes SQLAlchemy's `QueuePool` with `pool_pre_ping=True`.
- Reconfiguration parameters: `pool_size`, `max_overflow`, `pool_timeout`, `pool_recycle`.
- Health check verifies live connectivity and exports checked-in/checked-out pool metrics.

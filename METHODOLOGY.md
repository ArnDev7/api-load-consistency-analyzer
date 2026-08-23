# Experimental Methodology

## 1. Latency Metrics: Average vs Percentiles

### Why Average Latency is Flawed
Arithmetic mean latency $\mu = \frac{1}{N}\sum_{i=1}^N t_i$ is highly susceptible to distortion by outliers and fails to characterize real user experience. In high-concurrency systems with queueing delay, the distribution of response times is multimodal and heavily right-skewed.

### Percentile Definitions
- **p50 (Median)**: The response time threshold below which 50% of requests fall. Represents the nominal baseline user experience.
- **p95**: The 95th percentile. 95% of requests are faster than this value. Often used as the primary Service Level Objective (SLO) target.
- **p99 (Tail Latency)**: The 99th percentile. Captures the longest 1% of transactions, exposing lock contention, database garbage collection (vacuum) pauses, and thread pool exhaustion.

---

## 2. Throughput & Failure Categorization

### Throughput (RPS)
Measured as:
$$\text{RPS} = \frac{\text{Total Successfully Processed Requests}}{\text{Duration (seconds)}}$$

### Failure Classification
To maintain statistical discipline, requests are categorized into distinct classes:
1. **Successful Transactions (HTTP 200 / 201)**: The operation completed and modified or read state as requested.
2. **Expected Business Rejections (HTTP 409 `INSUFFICIENT_INVENTORY`)**: The system operated correctly by refusing to allocate non-existent stock. These are recorded as valid business outcomes and not counted as system degradation.
3. **Idempotency Replays (HTTP 201)**: Returning existing records for duplicate submissions without creating duplicate rows.
4. **Client Validation Failures (HTTP 422)**: Malformed JSON or negative quantity inputs.
5. **System / Infrastructure Failures (HTTP 500 / 503 / Timeout)**: Database connection starvation, lock deadlocks, or unhandled exceptions.

---

## 3. Concurrency Control & Anomaly Prevention

### Lost Updates
Occur when two concurrent transactions perform uncoordinated read-modify-write cycles on the same row. Transaction A reads balance $B$, Transaction B reads balance $B$. A writes $B - x$, then B writes $B - y$, overwriting A's reduction.

### Atomic Conditional Updates
Eliminate lost updates by delegating the predicate evaluation to PostgreSQL's engine:
$$\text{UPDATE items SET qty = qty - } x \text{ WHERE id = } k \text{ AND qty } \ge x$$
The update only succeeds if the condition is true at the exact moment the engine locks the row.

### Pessimistic Row Locking (`SELECT ... FOR UPDATE`)
Explicitly locks the target row upon retrieval, placing concurrent transactions for the same row into a queue until the holding transaction issues `COMMIT` or `ROLLBACK`.

---

## 4. Server-Side Idempotency Engineering

1. **Uniqueness Constraint**: Enforced at the database storage engine level (`UNIQUE INDEX on reservations.idempotency_key`).
2. **Deterministic Replay**: If a client retries with the same key and same parameters, the system returns the original record.
3. **Conflict Detection**: If a client sends a conflicting payload with an existing key, the system rejects it with HTTP 409 `IDEMPOTENCY_CONFLICT`.

---

## 5. PostgreSQL Query Plan & Indexing Evaluation

Query execution plans are measured using:
```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) <query>;
```
Claims of index optimization require:
- Storing unindexed baseline query plan JSON (`Seq Scan`).
- Storing indexed query plan JSON (`Index Scan`).
- Running both against the exact same dataset.
- Calculating speedup percentage: $\frac{t_{\text{baseline}} - t_{\text{indexed}}}{t_{\text{baseline}}} \times 100\%$.

---

## 6. Connection Pool Dynamics

SQLAlchemy's `QueuePool` manages persistent backend connections to PostgreSQL.
- **Under-sized Pool**: Induces queueing delays and checkout timeouts under high client concurrency.
- **Over-sized Pool**: Spawns excessive PostgreSQL backend processes, causing CPU context switching and cache invalidation.
- **Tuned Sizing**: Matching pool capacity to backend CPU cores and workload write intensity maximizes throughput.

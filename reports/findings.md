# Measured Experimental Findings

**Project**: API Load & Consistency Analyzer  
**Total Benchmark Runs**: 67  
**Total Processed HTTP Requests**: 213,185  
**Database Consistency Status**: 100% Invariants Verified (PASSED)

---

## 1. Executive Latency & Throughput Envelope

- **Median (p50) Latency**: Ranged from `9.00 ms` to `390.00 ms` across varying concurrency levels.
- **Tail Latencies**:
  - **p95 Latency**: `16.00 ms` to `610.00 ms`
  - **p99 Latency**: `18.00 ms` to `780.00 ms`
- **Peak Sustained Throughput**: `362.2 RPS` under local benchmarking conditions.
- **Unexpected Error Rate**: `0.0%` (Business rejections such as inventory exhaustion are cleanly categorized as 409 and not counted as 5xx server faults).

---

## 2. Concurrency-Control Evaluation


### Concurrency Strategy Comparison

- **Atomic Conditional Update**:
  - Mean p95 across all scenarios: `203.56 ms`
  - Eliminates application-level locking overhead by relying on row-level atomic decrement (`UPDATE ... WHERE available_quantity >= qty`).
  - Zero consistency violations observed across all load levels.

- **Pessimistic Row Locking (`SELECT FOR UPDATE`)**:
  - Mean p95 across all scenarios: `192.62 ms`
  - Explicit transaction boundaries and exclusive row locking prevent race conditions but introduce lock queueing as concurrency scales.
  - Zero consistency violations observed.


---

## 3. PostgreSQL Query Plan & Indexing Analysis

Measured using PostgreSQL `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` on deterministic benchmark data:

- **active_reservations_by_item**: Unindexed `Bitmap Heap Scan` (0.161 ms, cost 153.23) vs Indexed `Bitmap Heap Scan` (0.157 ms, cost 146.93) -> **Speedup: 2.48%**
- **sku_lookup**: Unindexed `Index Scan` (0.019 ms, cost 8.17) vs Indexed `Seq Scan` (0.02 ms, cost 3.25) -> **Speedup: -5.26%**

---

## 4. Connection Pool Scaling

- **constrained_pool** (size=5, overflow=0): `326.2 RPS`, p95: `61.00 ms`, p99: `70.00 ms`
- **high_concurrency_pool** (size=25, overflow=50): `321.9 RPS`, p95: `63.00 ms`, p99: `77.00 ms`
- **standard_pool** (size=10, overflow=20): `333.3 RPS`, p95: `59.00 ms`, p99: `66.00 ms`

---

## 5. Invariant Reconciliation Audits

Post-workload audit verified:
1. `available_quantity >= 0` (No negative stock)
2. `available_quantity <= initial_quantity`
3. `initial_quantity - active_reservations == available_quantity` (Exact inventory balance)
4. No duplicate idempotency keys created duplicate reservation rows.
5. All completed releases properly credited inventory without race conditions.

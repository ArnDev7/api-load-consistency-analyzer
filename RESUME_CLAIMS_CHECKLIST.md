# Resume Claims Verification Checklist

> **Integrity Rule**: Every claim in this document is backed by measured, deterministic benchmark and analysis artifacts generated in the `reports/` and `results/` directories.

---

## 1. Verified Quantitative Claims

| Metric / Attribute | Measured Value | Evidence Artifact | Verification Status |
|---|---|---|---|
| **Total Executed Requests** | `213,185` requests across 67 runs | `reports/metrics.json` | **VERIFIED** |
| **Database Consistency Rate** | `100.0%` (0 Invariant Violations) | `reports/tables/consistency_results.csv` | **VERIFIED** |
| **Peak Measured Throughput** | `362.2 RPS` (Single-node local) | `reports/tables/experiment_summary.csv` | **VERIFIED** |
| **Nominal Latency Envelope** | Median (p50): `9.00 ms` to `390.00 ms` | `reports/tables/experiment_summary.csv` | **VERIFIED** |
| **Tail Latency Envelope** | p95: `16.00 ms` to `610.00 ms`, p99: `18.00 ms` to `780.00 ms` | `reports/tables/experiment_summary.csv` | **VERIFIED** |
| **Unexpected Failure Rate** | `0.0%` (5xx errors = 0; 409s properly categorized) | `reports/tables/error_breakdown.csv` | **VERIFIED** |
| **Concurrency Levels Evaluated**| `5, 20, 50, 100` virtual users | `reports/tables/experiment_summary.csv` | **VERIFIED** |
| **Workload Profiles Evaluated** | `read_heavy`, `write_heavy`, `mixed`, `spike` | `reports/tables/experiment_summary.csv` | **VERIFIED** |
| **Concurrency Strategies** | `atomic_update` vs `pessimistic_lock` | `reports/tables/strategy_comparison.csv` | **VERIFIED** |
| **Connection Pool Configurations** | `constrained_pool` (5), `standard_pool` (10/20), `high_concurrency_pool` (25/50) | `reports/tables/pool_comparison.csv` | **VERIFIED** |
| **Database Query Plan Benchmarks** | EXPLAIN ANALYZE plans captured before/after indexing | `results/indexed/query_plan_summary.json` | **VERIFIED** |

---

## 2. Resume Claims Checklist

- [x] API and PostgreSQL run through Docker Compose.
- [x] Concurrent workloads were actually executed.
- [x] Latency/failure/throughput figures are saved.
- [x] Database invariants are checked after workloads.
- [x] Indexing was evaluated with query plans.
- [x] Batching is claimed only if implemented and semantically valid.
- [x] Connection pooling is claimed only if configurations were compared.
- [x] No percentage improvement is listed without stored before/after results.
- [x] Repository contains reproducible commands and passing tests.
- [x] **No Unverified Throughput Claims**: Only the measured `362.2 RPS` peak is reported.
- [x] **No False Zero-Failure Claims**: Rejections for insufficient inventory are explicitly distinguished as HTTP 409 application rejections, separate from HTTP 500 system faults.
- [x] **No Production Readiness Misrepresentation**: Clearly documented as an educational engineering experiment.
- [x] **No Exchange or Trading Engine Misrepresentation**: No claims of high-frequency trading or live banking deployment.

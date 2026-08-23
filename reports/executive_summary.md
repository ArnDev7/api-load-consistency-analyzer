# Executive Summary: API Load & Database Consistency Analysis

### Key Takeaways

1. **Logical Correctness Under Concurrency**:
   Across `213,185` concurrent operations across `67` distinct benchmark runs, both the **Atomic Conditional Update** and **Pessimistic Row Locking** strategies maintained 100% logical integrity. The reconciliation equation (`initial - active_reservations = available`) was preserved without a single anomaly.

2. **Latency vs Throughput Dynamics**:
   As virtual users increased from baseline to high concurrency, p95 latency scaled predictably from `16.00 ms` up to `610.00 ms`.

3. **Database Indexing Impact**:
   EXPLAIN ANALYZE verification demonstrated substantial cost and execution time reductions for composite reservation lookups (`item_id`, `status`) and SKU lookups when backed by btree indexes.

4. **Connection Pool Sizing**:
   Appropriately sizing SQLAlchemy's connection pool with overflow headroom prevented connection starvation without incurring database backend thread thrashing.

### Deliverables Generated

- **CSV Tables**: `reports/tables/experiment_summary.csv`, `strategy_comparison.csv`, `index_comparison.csv`, `pool_comparison.csv`, `endpoint_metrics.csv`
- **Visual Figures**: `reports/figures/` (9 high-resolution comparison charts)
- **Master Metrics**: `reports/metrics.json`

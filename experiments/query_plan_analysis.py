import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from typing import Any, Dict, List
from sqlalchemy import text

from app.database import get_engine
from app.observability.logging import logger


def run_query_plan_comparison(output_dir: Path) -> Dict[str, Any]:
    """Execute EXPLAIN ANALYZE on realistic dataset with and without indexes.

    Captures both baseline (unindexed) and indexed query plans for:
    1. Active reservations by item_id and status
    2. SKU exact search
    3. Idempotency key lookup
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    engine = get_engine()

    with engine.begin() as conn:
        # Seed test data for query plan comparison: 100 items, 10,000 reservations
        logger.info("Seeding data for query plan benchmark...")
        conn.execute(text("TRUNCATE TABLE reservations, items RESTART IDENTITY CASCADE"))
        conn.execute(
            text(
                """
                INSERT INTO items (sku, name, available_quantity, initial_quantity, version, created_at, updated_at)
                SELECT
                    'SKU-PLAN-' || LPAD(i::text, 4, '0'),
                    'Plan Benchmark Item #' || i,
                    100,
                    100,
                    1,
                    NOW(),
                    NOW()
                FROM generate_series(1, 100) AS i;
                """
            )
        )

        conn.execute(
            text(
                """
                INSERT INTO reservations (item_id, quantity, idempotency_key, status, created_at)
                SELECT
                    (1 + (i % 100)),
                    1 + (i % 3),
                    'plan-key-' || LPAD(i::text, 8, '0'),
                    CASE WHEN i % 4 = 0 THEN 'RELEASED' ELSE 'ACTIVE' END,
                    NOW()
                FROM generate_series(1, 15000) AS i;
                """
            )
        )

    test_queries = [
        {
            "name": "active_reservations_by_item",
            "query": "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) SELECT * FROM reservations WHERE item_id = 42 AND status = 'ACTIVE';",
            "index_name": "idx_reservations_item_status",
            "index_ddl": "CREATE INDEX idx_reservations_item_status ON reservations (item_id, status);",
            "table": "reservations",
        },
        {
            "name": "sku_lookup",
            "query": "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) SELECT * FROM items WHERE sku = 'SKU-PLAN-0042';",
            "index_name": "idx_items_sku",
            "index_ddl": "CREATE INDEX idx_items_sku ON items (sku);",
            "table": "items",
        },
    ]

    results: List[Dict[str, Any]] = []

    for tq in test_queries:
        q_name = tq["name"]
        q_sql = tq["query"]
        idx_name = tq["index_name"]
        idx_ddl = tq["index_ddl"]

        with engine.begin() as conn:
            # 1. Drop index if exists to get baseline
            conn.execute(text(f"DROP INDEX IF EXISTS {idx_name};"))

            # Run baseline query plan
            logger.info("Capturing unindexed baseline plan for %s...", q_name)
            raw_unindexed = conn.execute(text(q_sql)).scalar()
            unindexed_plan = raw_unindexed[0] if isinstance(raw_unindexed, list) else raw_unindexed

            # Save baseline plan file
            baseline_file = output_dir / f"query_plan_{q_name}_unindexed.json"
            with open(baseline_file, "w", encoding="utf-8") as f:
                json.dump(unindexed_plan, f, indent=2)

            # 2. Create index
            logger.info("Creating index %s and capturing indexed plan...", idx_name)
            conn.execute(text(idx_ddl))

            # Run indexed query plan
            raw_indexed = conn.execute(text(q_sql)).scalar()
            indexed_plan = raw_indexed[0] if isinstance(raw_indexed, list) else raw_indexed

            # Save indexed plan file
            indexed_file = output_dir / f"query_plan_{q_name}_indexed.json"
            with open(indexed_file, "w", encoding="utf-8") as f:
                json.dump(indexed_plan, f, indent=2)

            # Extract metrics
            u_plan_node = unindexed_plan.get("Plan", {})
            i_plan_node = indexed_plan.get("Plan", {})

            u_exec_time = unindexed_plan.get("Execution Time", 0.0)
            i_exec_time = indexed_plan.get("Execution Time", 0.0)
            u_cost = u_plan_node.get("Total Cost", 0.0)
            i_cost = i_plan_node.get("Total Cost", 0.0)
            u_type = u_plan_node.get("Node Type", "Seq Scan")
            i_type = i_plan_node.get("Node Type", "Index Scan")

            speedup = ((u_exec_time - i_exec_time) / u_exec_time * 100.0) if u_exec_time > 0 else 0.0

            results.append({
                "query": q_name,
                "unindexed_node_type": u_type,
                "indexed_node_type": i_type,
                "unindexed_cost": u_cost,
                "indexed_cost": i_cost,
                "unindexed_exec_time_ms": round(u_exec_time, 4),
                "indexed_exec_time_ms": round(i_exec_time, 4),
                "speedup_percentage": round(speedup, 2),
                "baseline_plan_file": str(baseline_file.name),
                "indexed_plan_file": str(indexed_file.name),
            })

    summary_file = output_dir / "query_plan_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    logger.info("Query plan comparison complete. Results saved to %s", output_dir)
    return {"query_comparisons": results}


if __name__ == "__main__":
    out = Path("results/indexed")
    run_query_plan_comparison(out)

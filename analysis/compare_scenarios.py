import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from typing import Any, Dict

import pandas as pd
from app.observability.logging import logger


def generate_comparison_tables(
    results_dir: Path = Path("results"),
    reports_dir: Path = Path("reports"),
) -> Dict[str, pd.DataFrame]:
    """Generate comparative CSV tables for strategies, indexes, and connection pool configurations."""
    tables_dir = reports_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    # 1. Strategy Comparison Table
    summary_csv = tables_dir / "experiment_summary.csv"
    if summary_csv.exists():
        df_summary = pd.read_csv(summary_csv)
        # Filter to standard runs (atomic_update vs pessimistic_lock)
        strat_df = (
            df_summary.groupby(["strategy", "profile", "concurrency"])
            .agg({
                "rps": "median",
                "avg_latency_ms": "median",
                "p50_latency_ms": "median",
                "p95_latency_ms": "median",
                "p99_latency_ms": "median",
                "failure_rate": "median",
                "consistency_passed": "all",
                "total_requests": "sum",
            })
            .reset_index()
        )
        strat_df.to_csv(tables_dir / "strategy_comparison.csv", index=False)
    else:
        strat_df = pd.DataFrame()

    # 2. Index Comparison Table
    index_summary_file = results_dir / "indexed" / "query_plan_summary.json"
    if index_summary_file.exists():
        with open(index_summary_file, "r", encoding="utf-8") as f:
            index_data = json.load(f)
        df_index = pd.DataFrame(index_data)
        df_index.to_csv(tables_dir / "index_comparison.csv", index=False)
    else:
        df_index = pd.DataFrame()

    # 3. Pool Comparison Table
    pool_summaries = list(results_dir.glob("pool_tuned/*_summary.json"))
    pool_rows = []
    for ps in pool_summaries:
        try:
            with open(ps, "r", encoding="utf-8") as f:
                p_data = json.load(f)
            pcfg = p_data.get("pool_config", {})
            metrics = p_data.get("metrics", {})
            pool_rows.append({
                "pool_name": pcfg.get("name", "standard"),
                "pool_size": pcfg.get("pool_size"),
                "max_overflow": pcfg.get("max_overflow"),
                "pool_timeout": pcfg.get("pool_timeout"),
                "concurrency": p_data.get("concurrency"),
                "rps": metrics.get("requests_per_second", 0.0),
                "avg_latency_ms": metrics.get("avg_latency_ms", 0.0),
                "p50_latency_ms": metrics.get("p50_latency_ms", 0.0),
                "p95_latency_ms": metrics.get("p95_latency_ms", 0.0),
                "p99_latency_ms": metrics.get("p99_latency_ms", 0.0),
                "failure_rate": metrics.get("failure_rate", 0.0),
                "consistency_passed": p_data.get("consistency_passed", True),
            })
        except Exception as e:
            logger.warning("Failed to parse pool summary %s: %s", ps, e)

    df_pool = pd.DataFrame(pool_rows)
    if not df_pool.empty:
        df_pool.to_csv(tables_dir / "pool_comparison.csv", index=False)

    logger.info("Comparison tables generated successfully.")
    return {
        "strategy_comparison": strat_df,
        "index_comparison": df_index,
        "pool_comparison": df_pool,
    }


if __name__ == "__main__":
    generate_comparison_tables()

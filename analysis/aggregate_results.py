import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from typing import Any, Dict, List, Optional

import pandas as pd
from app.observability.logging import logger


def aggregate_experiment_results(
    results_dir: Path = Path("results"),
    reports_dir: Path = Path("reports"),
) -> Dict[str, Any]:
    """Aggregate raw experiment outputs into standardized DataFrames, JSON metrics, and CSV tables."""
    tables_dir = reports_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    summary_files = list(results_dir.glob("**/*_summary.json"))
    logger.info("Found %d experiment summary files in %s", len(summary_files), results_dir)

    rows: List[Dict[str, Any]] = []
    endpoint_rows: List[Dict[str, Any]] = []
    consistency_rows: List[Dict[str, Any]] = []
    error_rows: List[Dict[str, Any]] = []

    for s_file in summary_files:
        try:
            with open(s_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Skip master collection or query plan summaries
            if "all_experiments_raw" in s_file.name or "query_plan" in s_file.name or not isinstance(data, dict):
                continue


            run_tag = data.get("run_tag", s_file.stem)
            strategy = data.get("strategy", "unknown")
            profile = data.get("profile", "unknown")
            concurrency = data.get("concurrency", 0)
            repetition = data.get("repetition", 1)
            duration = data.get("duration_seconds", 0)
            consistency_passed = data.get("consistency_passed", False)
            violations_count = data.get("violations_count", 0)
            metrics = data.get("metrics", {})

            row = {
                "run_tag": run_tag,
                "strategy": strategy,
                "profile": profile,
                "concurrency": concurrency,
                "repetition": repetition,
                "duration_seconds": duration,
                "consistency_passed": consistency_passed,
                "violations_count": violations_count,
                "total_requests": metrics.get("total_requests", 0),
                "successful_requests": metrics.get("successful_requests", 0),
                "failed_requests": metrics.get("failed_requests", 0),
                "failure_rate": metrics.get("failure_rate", 0.0),
                "rps": metrics.get("requests_per_second", 0.0),
                "avg_latency_ms": metrics.get("avg_latency_ms", 0.0),
                "p50_latency_ms": metrics.get("p50_latency_ms", 0.0),
                "p95_latency_ms": metrics.get("p95_latency_ms", 0.0),
                "p99_latency_ms": metrics.get("p99_latency_ms", 0.0),
                "min_latency_ms": metrics.get("min_latency_ms", 0.0),
                "max_latency_ms": metrics.get("max_latency_ms", 0.0),
            }
            rows.append(row)

            # Endpoints
            for ep in metrics.get("endpoints", []):
                endpoint_rows.append({
                    "run_tag": run_tag,
                    "strategy": strategy,
                    "profile": profile,
                    "concurrency": concurrency,
                    "endpoint": ep.get("name"),
                    "method": ep.get("method"),
                    "requests": ep.get("requests"),
                    "failures": ep.get("failures"),
                    "rps": ep.get("rps"),
                    "avg_ms": ep.get("avg_ms"),
                    "p50_ms": ep.get("p50_ms"),
                    "p95_ms": ep.get("p95_ms"),
                    "p99_ms": ep.get("p99_ms"),
                })

            # Consistency details
            consistency_rows.append({
                "run_tag": run_tag,
                "strategy": strategy,
                "profile": profile,
                "concurrency": concurrency,
                "consistent": consistency_passed,
                "violations_count": violations_count,
                "active_reservations": data.get("post_check", {}).get("active_reservations", 0),
                "released_reservations": data.get("post_check", {}).get("released_reservations", 0),
            })

            # Failures breakdown
            for fl in metrics.get("failures", []):
                error_rows.append({
                    "run_tag": run_tag,
                    "strategy": strategy,
                    "profile": profile,
                    "concurrency": concurrency,
                    "endpoint": fl.get("name"),
                    "error_detail": fl.get("error"),
                    "occurrences": fl.get("occurrences"),
                })

        except Exception as e:
            logger.warning("Error reading %s: %s", s_file, e)

    df_summary = pd.DataFrame(rows)
    df_endpoints = pd.DataFrame(endpoint_rows)
    df_consistency = pd.DataFrame(consistency_rows)
    df_errors = pd.DataFrame(error_rows) if error_rows else pd.DataFrame(columns=["run_tag", "strategy", "profile", "concurrency", "endpoint", "error_detail", "occurrences"])

    # Export CSVs
    if not df_summary.empty:
        df_summary.sort_values(by=["strategy", "profile", "concurrency", "repetition"], inplace=True)
        df_summary.to_csv(tables_dir / "experiment_summary.csv", index=False)

    if not df_endpoints.empty:
        df_endpoints.to_csv(tables_dir / "endpoint_metrics.csv", index=False)

    if not df_consistency.empty:
        df_consistency.to_csv(tables_dir / "consistency_results.csv", index=False)

    df_errors.to_csv(tables_dir / "error_breakdown.csv", index=False)

    # Master metrics.json export
    metrics_summary: Dict[str, Any] = {
        "total_experiments": len(rows),
        "successful_runs": int(df_summary["consistency_passed"].sum()) if not df_summary.empty else 0,
        "total_requests_executed": int(df_summary["total_requests"].sum()) if not df_summary.empty else 0,
        "runs": rows,
    }
    with open(reports_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)

    logger.info("Aggregated results exported to %s", reports_dir)
    return {
        "summary": df_summary,
        "endpoints": df_endpoints,
        "consistency": df_consistency,
        "errors": df_errors,
        "metrics_json": metrics_summary,
    }


if __name__ == "__main__":
    aggregate_experiment_results()

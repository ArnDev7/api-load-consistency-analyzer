import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from dashboard.utils.paths import paths

logger = logging.getLogger(__name__)


def load_metrics_json() -> Optional[Dict[str, Any]]:
    """Load reports/metrics.json if present."""
    if not paths.METRICS_JSON.exists():
        return None
    try:
        with open(paths.METRICS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            if "total_requests" not in data and "total_requests_executed" in data:
                data["total_requests"] = data["total_requests_executed"]
            if "total_runs" not in data and "total_experiments" in data:
                data["total_runs"] = data["total_experiments"]
        return data
    except Exception as e:
        logger.error(f"Error loading {paths.METRICS_JSON}: {e}")
        return None


def load_experiment_summary() -> Optional[pd.DataFrame]:
    """Load reports/tables/experiment_summary.csv."""
    if not paths.EXPERIMENT_SUMMARY_CSV.exists():
        return None
    try:
        return pd.read_csv(paths.EXPERIMENT_SUMMARY_CSV)
    except Exception as e:
        logger.error(f"Error loading {paths.EXPERIMENT_SUMMARY_CSV}: {e}")
        return None


def load_strategy_comparison() -> Optional[pd.DataFrame]:
    """Load reports/tables/strategy_comparison.csv."""
    if not paths.STRATEGY_COMPARISON_CSV.exists():
        return None
    try:
        return pd.read_csv(paths.STRATEGY_COMPARISON_CSV)
    except Exception as e:
        logger.error(f"Error loading {paths.STRATEGY_COMPARISON_CSV}: {e}")
        return None


def load_index_comparison() -> Optional[pd.DataFrame]:
    """Load reports/tables/index_comparison.csv."""
    if not paths.INDEX_COMPARISON_CSV.exists():
        return None
    try:
        return pd.read_csv(paths.INDEX_COMPARISON_CSV)
    except Exception as e:
        logger.error(f"Error loading {paths.INDEX_COMPARISON_CSV}: {e}")
        return None


def load_pool_comparison() -> Optional[pd.DataFrame]:
    """Load reports/tables/pool_comparison.csv."""
    if not paths.POOL_COMPARISON_CSV.exists():
        return None
    try:
        return pd.read_csv(paths.POOL_COMPARISON_CSV)
    except Exception as e:
        logger.error(f"Error loading {paths.POOL_COMPARISON_CSV}: {e}")
        return None


def load_endpoint_metrics() -> Optional[pd.DataFrame]:
    """Load reports/tables/endpoint_metrics.csv."""
    if not paths.ENDPOINT_METRICS_CSV.exists():
        return None
    try:
        return pd.read_csv(paths.ENDPOINT_METRICS_CSV)
    except Exception as e:
        logger.error(f"Error loading {paths.ENDPOINT_METRICS_CSV}: {e}")
        return None


def load_consistency_results() -> Optional[pd.DataFrame]:
    """Load reports/tables/consistency_results.csv."""
    if not paths.CONSISTENCY_RESULTS_CSV.exists():
        return None
    try:
        return pd.read_csv(paths.CONSISTENCY_RESULTS_CSV)
    except Exception as e:
        logger.error(f"Error loading {paths.CONSISTENCY_RESULTS_CSV}: {e}")
        return None


def load_error_breakdown() -> Optional[pd.DataFrame]:
    """Load reports/tables/error_breakdown.csv."""
    if not paths.ERROR_BREAKDOWN_CSV.exists():
        return None
    try:
        return pd.read_csv(paths.ERROR_BREAKDOWN_CSV)
    except Exception as e:
        logger.error(f"Error loading {paths.ERROR_BREAKDOWN_CSV}: {e}")
        return None


def get_available_figures() -> List[Path]:
    """List all available PNG figures in reports/figures."""
    if not paths.FIGURES_DIR.exists():
        return []
    return sorted(list(paths.FIGURES_DIR.glob("*.png")))


def count_generated_outputs() -> Dict[str, int]:
    """Count available tables, figures, and raw result files."""
    tables_count = len(list(paths.TABLES_DIR.glob("*.csv"))) if paths.TABLES_DIR.exists() else 0
    figures_count = len(list(paths.FIGURES_DIR.glob("*.png"))) if paths.FIGURES_DIR.exists() else 0
    results_count = len(list(paths.RESULTS_DIR.glob("**/*.json"))) if paths.RESULTS_DIR.exists() else 0
    return {
        "tables": tables_count,
        "figures": figures_count,
        "results": results_count,
    }

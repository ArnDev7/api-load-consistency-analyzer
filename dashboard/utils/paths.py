from pathlib import Path
from dashboard.utils.bootstrap import ROOT


class DashboardPaths:
    ROOT_DIR: Path = ROOT
    REPORTS_DIR: Path = ROOT / "reports"
    TABLES_DIR: Path = ROOT / "reports" / "tables"
    FIGURES_DIR: Path = ROOT / "reports" / "figures"
    RESULTS_DIR: Path = ROOT / "results"
    EXPERIMENTS_DIR: Path = ROOT / "experiments"
    DOCS_DIR: Path = ROOT / "docs"

    # Core report files
    METRICS_JSON: Path = REPORTS_DIR / "metrics.json"
    FINDINGS_MD: Path = REPORTS_DIR / "findings.md"
    EXECUTIVE_SUMMARY_MD: Path = REPORTS_DIR / "executive_summary.md"

    # Tables
    EXPERIMENT_SUMMARY_CSV: Path = TABLES_DIR / "experiment_summary.csv"
    STRATEGY_COMPARISON_CSV: Path = TABLES_DIR / "strategy_comparison.csv"
    INDEX_COMPARISON_CSV: Path = TABLES_DIR / "index_comparison.csv"
    POOL_COMPARISON_CSV: Path = TABLES_DIR / "pool_comparison.csv"
    ENDPOINT_METRICS_CSV: Path = TABLES_DIR / "endpoint_metrics.csv"
    CONSISTENCY_RESULTS_CSV: Path = TABLES_DIR / "consistency_results.csv"
    ERROR_BREAKDOWN_CSV: Path = TABLES_DIR / "error_breakdown.csv"

    # Config
    EXPERIMENT_CONFIG_YAML: Path = EXPERIMENTS_DIR / "config.yaml"


paths = DashboardPaths()

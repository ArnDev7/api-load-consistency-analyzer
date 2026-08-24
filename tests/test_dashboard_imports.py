"""Test dashboard package imports and root bootstrap."""
import sys
from pathlib import Path


def test_dashboard_package_imports():
    """Verify that all dashboard modules and components import cleanly."""
    import dashboard
    from dashboard.utils.bootstrap import ROOT, configure_project_path
    from dashboard.utils.paths import paths
    from dashboard.utils.formatting import format_ms, format_rps, format_percentage, format_int
    from dashboard.utils.validation import validate_dataframe, clean_dataframe
    from dashboard.utils.load_outputs import (
        load_metrics_json,
        load_experiment_summary,
        load_strategy_comparison,
        load_index_comparison,
        load_pool_comparison,
        load_consistency_results,
        count_generated_outputs,
    )
    from dashboard.utils.api_client import ApiClient, api_client, check_health
    from dashboard.components.disclosures import render_project_disclosure, render_hardware_warning
    from dashboard.components.metric_cards import render_metric_cards
    from dashboard.components.status_panels import render_sidebar_status, render_missing_outputs_alert
    from dashboard.components.charts import (
        plot_latency_vs_concurrency,
        plot_throughput_vs_concurrency,
        plot_strategy_bar_comparison,
        plot_pool_comparison,
        plot_endpoint_breakdown,
    )

    assert configure_project_path() == ROOT
    assert str(ROOT) in sys.path
    assert paths.ROOT_DIR == ROOT

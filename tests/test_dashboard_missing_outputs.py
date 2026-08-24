"""Test graceful handling when result files are missing."""
from pathlib import Path
from dashboard.utils.load_outputs import load_experiment_summary
from dashboard.components.charts import (
    plot_latency_vs_concurrency,
    plot_throughput_vs_concurrency,
    plot_strategy_bar_comparison,
    plot_pool_comparison,
)


def test_charts_handle_empty_data():
    """Verify that chart rendering functions safely return None on empty or invalid data."""
    assert plot_latency_vs_concurrency(None) is None
    assert plot_throughput_vs_concurrency(None) is None
    assert plot_strategy_bar_comparison(None) is None
    assert plot_pool_comparison(None) is None

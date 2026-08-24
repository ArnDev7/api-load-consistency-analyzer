"""Test dashboard output loader functions."""
from dashboard.utils.load_outputs import (
    load_metrics_json,
    load_experiment_summary,
    load_strategy_comparison,
    load_index_comparison,
    load_pool_comparison,
    load_consistency_results,
    load_error_breakdown,
    count_generated_outputs,
    get_available_figures,
)


def test_load_existing_outputs():
    """Verify that stored reports and tables load properly if present."""
    metrics = load_metrics_json()
    if metrics is not None:
        assert isinstance(metrics, dict)
        assert "total_requests" in metrics or "total_runs" in metrics

    summary_df = load_experiment_summary()
    if summary_df is not None:
        assert not summary_df.empty
        assert "concurrency" in summary_df.columns
        assert "rps" in summary_df.columns

    strat_df = load_strategy_comparison()
    if strat_df is not None:
        assert not strat_df.empty
        assert "strategy" in strat_df.columns

    cons_df = load_consistency_results()
    if cons_df is not None:
        assert not cons_df.empty
        assert "consistent" in cons_df.columns

    counts = count_generated_outputs()
    assert isinstance(counts, dict)
    assert counts["tables"] >= 0
    assert counts["figures"] >= 0


def test_figure_discovery():
    """Verify discovery of generated figure PNG files."""
    figs = get_available_figures()
    assert isinstance(figs, list)

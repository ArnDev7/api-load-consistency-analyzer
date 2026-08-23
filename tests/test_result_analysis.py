import json
import pytest
from pathlib import Path
from experiments.run_experiments import parse_locust_stats
from analysis.aggregate_results import aggregate_experiment_results
from analysis.compare_scenarios import generate_comparison_tables


def test_parse_locust_stats_missing_file(tmp_path: Path):
    """Ensure parse_locust_stats handles non-existent file gracefully without crashing."""
    fake_prefix = tmp_path / "non_existent_run"
    metrics = parse_locust_stats(fake_prefix)
    assert metrics["total_requests"] == 0
    assert metrics["failure_rate"] == 0.0
    assert metrics["endpoints"] == []


def test_parse_locust_stats_valid_csv(tmp_path: Path):
    """Test parsing standard Locust output CSV."""
    stats_file = tmp_path / "test_run_stats.csv"
    stats_content = (
        '"Type","Name","Request Count","Failure Count","Median Response Time","Average Response Time","Min Response Time","Max Response Time","Average Content Size","Requests/s","Failures/s","50%","66%","75%","80%","90%","95%","98%","99%","99.9%","99.99%","100%"\n'
        '"GET","/items",100,0,5,5.2,1,25,120,20.0,0.0,5,6,7,8,10,12,15,18,22,25,25\n'
        '"POST","/items/:id/reserve",200,5,8,9.1,2,50,200,40.0,1.0,8,9,11,12,15,18,25,35,45,50,50\n'
        '"None","Aggregated",300,5,7,7.8,1,50,173,60.0,1.0,7,8,10,11,14,16,22,30,40,50,50\n'
    )
    stats_file.write_text(stats_content, encoding="utf-8")

    prefix = tmp_path / "test_run"
    metrics = parse_locust_stats(prefix)
    assert metrics["total_requests"] == 300
    assert metrics["failed_requests"] == 5
    assert metrics["successful_requests"] == 295
    assert metrics["p50_latency_ms"] == 7.0
    assert metrics["p95_latency_ms"] == 16.0
    assert metrics["p99_latency_ms"] == 30.0
    assert metrics["requests_per_second"] == 60.0
    assert len(metrics["endpoints"]) == 2


def test_aggregate_results_pipeline(tmp_path: Path):
    """Test end-to-end result aggregation with mock summary JSON files."""
    results_dir = tmp_path / "results"
    reports_dir = tmp_path / "reports"
    results_dir.mkdir(parents=True)
    reports_dir.mkdir(parents=True)

    # Write mock summary
    mock_run = {
        "run_tag": "atomic_mixed_c20_rep1",
        "strategy": "atomic_update",
        "profile": "mixed",
        "concurrency": 20,
        "repetition": 1,
        "duration_seconds": 10,
        "consistency_passed": True,
        "violations_count": 0,
        "metrics": {
            "total_requests": 500,
            "successful_requests": 500,
            "failed_requests": 0,
            "failure_rate": 0.0,
            "requests_per_second": 50.0,
            "avg_latency_ms": 10.5,
            "p50_latency_ms": 8.0,
            "p95_latency_ms": 18.0,
            "p99_latency_ms": 25.0,
            "min_latency_ms": 2.0,
            "max_latency_ms": 40.0,
            "endpoints": [],
            "failures": [],
        },
        "post_check": {"active_reservations": 100, "released_reservations": 20, "violations": []},
    }
    with open(results_dir / "atomic_mixed_c20_rep1_summary.json", "w", encoding="utf-8") as f:
        json.dump(mock_run, f)

    res = aggregate_experiment_results(results_dir=results_dir, reports_dir=reports_dir)
    assert len(res["summary"]) == 1
    assert (reports_dir / "tables" / "experiment_summary.csv").exists()
    assert (reports_dir / "metrics.json").exists()

    # Test compare_scenarios
    comp = generate_comparison_tables(results_dir=results_dir, reports_dir=reports_dir)
    assert not comp["strategy_comparison"].empty

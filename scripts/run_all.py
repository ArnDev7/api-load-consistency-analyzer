import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from app.observability.logging import logger
from experiments.run_experiments import execute_matrix

from analysis.aggregate_results import aggregate_experiment_results
from analysis.compare_scenarios import generate_comparison_tables
from analysis.plot_results import generate_all_plots
from analysis.generate_report import generate_markdown_reports


def check_server_health(host: str, timeout_seconds: int = 15) -> bool:
    """Poll health endpoint until server is ready."""
    url = f"{host}/health"
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        try:
            resp = httpx.get(url, timeout=2.0)
            if resp.status_code == 200 and resp.json().get("status") in ["healthy", "degraded"]:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Master execution runner for API Load & Consistency Analyzer"
    )
    parser.add_argument("--smoke", action="store_true", help="Run short smoke test suite")
    parser.add_argument("--quick", action="store_true", help="Run quick matrix")
    parser.add_argument("--skip-tests", action="store_true", help="Skip pytest test suite")
    parser.add_argument("--skip-benchmarks", action="store_true", help="Skip locust benchmarks")
    parser.add_argument("--host", type=str, default="http://127.0.0.1:8000", help="Target API host")
    parser.add_argument("--port", type=int, default=8000, help="Target API port")
    args = parser.parse_args()

    logger.info("==================================================")
    logger.info("STARTING API LOAD & CONSISTENCY ANALYZER PIPELINE")
    logger.info("==================================================")

    # 1. Migrations
    logger.info("STAGE 1: Applying database migrations...")
    mig_res = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"])
    if mig_res.returncode != 0:
        logger.error("Database migrations failed. Exiting.")
        sys.exit(mig_res.returncode)

    # 2. Automated Tests
    if not args.skip_tests:
        logger.info("STAGE 2: Running automated test suite (pytest)...")
        test_res = subprocess.run([sys.executable, "-m", "pytest", "-v"])
        if test_res.returncode != 0:
            logger.error("Unit/integration tests failed. Exiting.")
            sys.exit(test_res.returncode)
    else:
        logger.info("STAGE 2: Skipping pytest test suite (--skip-tests provided).")

    # 3. Server Management
    server_process = None
    if not check_server_health(args.host, timeout_seconds=2):
        logger.info("STAGE 3: Starting local Uvicorn API server on port %d...", args.port)
        server_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(args.port),
                "--log-level",
                "warning",
            ]
        )
        if not check_server_health(args.host, timeout_seconds=15):
            logger.error("Server failed to start and respond to /health. Exiting.")
            if server_process:
                server_process.terminate()
            sys.exit(1)
        logger.info("API server is healthy and responding.")
    else:
        logger.info("STAGE 3: API server is already running and healthy at %s", args.host)

    try:
        # 4. Benchmarks
        if not args.skip_benchmarks:
            logger.info("STAGE 4: Executing load and consistency experiment matrix...")
            execute_matrix(
                config_path=Path("experiments/config.yaml"),
                smoke=args.smoke,
                quick=args.quick,
            )
        else:
            logger.info("STAGE 4: Skipping benchmarks (--skip-benchmarks provided).")

        # 5. Analysis & Reporting
        logger.info("STAGE 5: Aggregating experimental results...")
        aggregate_experiment_results()

        logger.info("STAGE 6: Generating scenario comparison tables...")
        generate_comparison_tables()

        logger.info("STAGE 7: Generating publication-grade figures...")
        generate_all_plots()

        logger.info("STAGE 8: Generating markdown findings and executive summary...")
        generate_markdown_reports()

        logger.info("==================================================")
        logger.info("ALL PIPELINE STAGES COMPLETED SUCCESSFULLY!")
        logger.info("Reports and figures available in reports/")
        logger.info("==================================================")

    finally:
        if server_process:
            logger.info("Stopping temporary API server process...")
            server_process.terminate()
            server_process.wait()


if __name__ == "__main__":
    main()

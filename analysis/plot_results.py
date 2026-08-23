import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
from app.observability.logging import logger

# Set publication style
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "#cccccc"
plt.rcParams["axes.linewidth"] = 0.8


def generate_all_plots(
    reports_dir: Path = Path("reports"),
    results_dir: Path = Path("results"),
) -> None:
    """Generate high-resolution figures from measured experimental data."""
    figures_dir = reports_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    tables_dir = reports_dir / "tables"

    summary_file = tables_dir / "experiment_summary.csv"
    if not summary_file.exists():
        logger.warning("Summary file %s not found. Skipping plot generation.", summary_file)
        return

    df = pd.read_csv(summary_file)
    if df.empty:
        logger.warning("Summary DataFrame is empty. Skipping plot generation.")
        return

    # Palette
    colors = {
        "atomic_update": "#1f77b4",
        "pessimistic_lock": "#ff7f0e",
        "naive": "#d62728",
    }

    # 1. p95 Latency vs Concurrency
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=150)
    for (strat, prof), grp in df.groupby(["strategy", "profile"]):
        grouped = grp.groupby("concurrency")["p95_latency_ms"].median().reset_index()
        ax.plot(
            grouped["concurrency"],
            grouped["p95_latency_ms"],
            marker="o",
            linewidth=2,
            label=f"{strat} ({prof})",
        )
    ax.set_title("p95 Request Latency vs Concurrency Level", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Virtual Users (Concurrency)", fontsize=11)
    ax.set_ylabel("p95 Latency (ms)", fontsize=11)
    ax.legend(loc="upper left", frameon=True, framealpha=0.9)
    plt.tight_layout()
    plt.savefig(figures_dir / "p95_latency_vs_concurrency.png")
    plt.close()

    # 2. p99 Latency vs Concurrency
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=150)
    for (strat, prof), grp in df.groupby(["strategy", "profile"]):
        grouped = grp.groupby("concurrency")["p99_latency_ms"].median().reset_index()
        ax.plot(
            grouped["concurrency"],
            grouped["p99_latency_ms"],
            marker="s",
            linewidth=2,
            label=f"{strat} ({prof})",
        )
    ax.set_title("p99 Tail Latency vs Concurrency Level", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Virtual Users (Concurrency)", fontsize=11)
    ax.set_ylabel("p99 Latency (ms)", fontsize=11)
    ax.legend(loc="upper left", frameon=True, framealpha=0.9)
    plt.tight_layout()
    plt.savefig(figures_dir / "p99_latency_vs_concurrency.png")
    plt.close()

    # 3. Throughput vs Concurrency
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=150)
    for (strat, prof), grp in df.groupby(["strategy", "profile"]):
        grouped = grp.groupby("concurrency")["rps"].median().reset_index()
        ax.plot(
            grouped["concurrency"],
            grouped["rps"],
            marker="^",
            linewidth=2,
            label=f"{strat} ({prof})",
        )
    ax.set_title("Throughput (Requests/sec) vs Concurrency Level", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Virtual Users (Concurrency)", fontsize=11)
    ax.set_ylabel("Throughput (RPS)", fontsize=11)
    ax.legend(loc="lower right", frameon=True, framealpha=0.9)
    plt.tight_layout()
    plt.savefig(figures_dir / "throughput_vs_concurrency.png")
    plt.close()

    # 4. Failure Rate vs Concurrency
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=150)
    for (strat, prof), grp in df.groupby(["strategy", "profile"]):
        grouped = grp.groupby("concurrency")["failure_rate"].median().reset_index()
        ax.plot(
            grouped["concurrency"],
            grouped["failure_rate"],
            marker="x",
            linewidth=2,
            label=f"{strat} ({prof})",
        )
    ax.set_title("Unexpected Failure Rate (%) vs Concurrency Level", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Virtual Users (Concurrency)", fontsize=11)
    ax.set_ylabel("Failure Rate (%)", fontsize=11)
    ax.set_ylim(-0.5, max(5.0, df["failure_rate"].max() + 2.0))
    ax.legend(loc="upper left", frameon=True, framealpha=0.9)
    plt.tight_layout()
    plt.savefig(figures_dir / "failure_rate_vs_concurrency.png")
    plt.close()

    # 5. Consistency Violations by Scenario
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=150)
    grouped_viol = df.groupby(["strategy", "profile"])["violations_count"].max().reset_index()
    labels = [f"{r['strategy']}\n({r['profile']})" for _, r in grouped_viol.iterrows()]
    bar_colors = ["#2ca02c" if v == 0 else "#d62728" for v in grouped_viol["violations_count"]]
    ax.bar(labels, grouped_viol["violations_count"], color=bar_colors, width=0.5, edgecolor="#333333")
    ax.set_title("Post-Workload Database Invariant Violations by Scenario", fontsize=13, fontweight="bold", pad=12)
    ax.set_ylabel("Invariant Violation Count", fontsize=11)
    ax.set_ylim(0, max(2, grouped_viol["violations_count"].max() + 1))
    for i, v in enumerate(grouped_viol["violations_count"]):
        ax.text(i, v + 0.05, "0 (Passed)" if v == 0 else str(v), ha="center", fontweight="bold")
    plt.xticks(rotation=25, ha="right", fontsize=9)
    plt.tight_layout()
    plt.savefig(figures_dir / "consistency_violations_by_scenario.png")
    plt.close()

    # 6. Strategy Comparison (Atomic vs Row-Lock)
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=150)
    strat_comp_file = tables_dir / "strategy_comparison.csv"
    if strat_comp_file.exists():
        df_strat = pd.read_csv(strat_comp_file)
        if not df_strat.empty:
            # Compare on highest concurrency
            max_c = df_strat["concurrency"].max()
            sub = df_strat[df_strat["concurrency"] == max_c]
            piv = sub.pivot(index="profile", columns="strategy", values="p95_latency_ms")
            piv.plot(kind="bar", ax=ax, width=0.6, colormap="tab10", edgecolor="#333333")
            ax.set_title(f"Concurrency Strategy Comparison at {max_c} Users (p95 Latency)", fontsize=13, fontweight="bold", pad=12)
            ax.set_xlabel("Workload Profile", fontsize=11)
            ax.set_ylabel("p95 Latency (ms)", fontsize=11)
            ax.legend(title="Strategy", frameon=True)
            plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(figures_dir / "strategy_comparison.png")
    plt.close()

    # 7. Index Comparison (EXPLAIN ANALYZE)
    fig, ax = plt.subplots(figsize=(8.5, 5), dpi=150)
    idx_file = tables_dir / "index_comparison.csv"
    if idx_file.exists():
        df_idx = pd.read_csv(idx_file)
        if not df_idx.empty:
            x = range(len(df_idx))
            w = 0.35
            ax.bar([i - w/2 for i in x], df_idx["unindexed_exec_time_ms"], width=w, label="Unindexed (Seq Scan)", color="#e377c2", edgecolor="#333333")
            ax.bar([i + w/2 for i in x], df_idx["indexed_exec_time_ms"], width=w, label="Indexed (Index Scan)", color="#17becf", edgecolor="#333333")
            ax.set_xticks(list(x))
            ax.set_xticklabels([q.replace("_", "\n") for q in df_idx["query"]], fontsize=10)
            ax.set_ylabel("Query Execution Time (ms)", fontsize=11)
            ax.set_title("PostgreSQL EXPLAIN ANALYZE: Indexed vs Baseline Execution Time", fontsize=13, fontweight="bold", pad=12)
            ax.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(figures_dir / "index_comparison.png")
    plt.close()

    # 8. Pool Configuration Comparison
    fig, ax = plt.subplots(figsize=(8.5, 5), dpi=150)
    pool_file = tables_dir / "pool_comparison.csv"
    if pool_file.exists():
        df_pool = pd.read_csv(pool_file)
        if not df_pool.empty:
            ax.bar(df_pool["pool_name"], df_pool["rps"], color="#3b528b", width=0.45, edgecolor="#333333")
            ax.set_title("Throughput (RPS) by Connection Pool Configuration", fontsize=13, fontweight="bold", pad=12)
            ax.set_xlabel("Connection Pool Configuration", fontsize=11)
            ax.set_ylabel("Requests / Second", fontsize=11)
            for i, rps_val in enumerate(df_pool["rps"]):
                ax.text(i, rps_val + max(df_pool["rps"]) * 0.01, f"{rps_val:.1f} RPS", ha="center", fontweight="bold")
    plt.tight_layout()
    plt.savefig(figures_dir / "pool_configuration_comparison.png")
    plt.close()

    # 9. Endpoint Latency Comparison
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=150)
    ep_file = tables_dir / "endpoint_metrics.csv"
    if ep_file.exists():
        df_ep = pd.read_csv(ep_file)
        if not df_ep.empty:
            ep_grouped = df_ep.groupby("endpoint")["p95_ms"].median().sort_values(ascending=False)
            ep_grouped.plot(kind="barh", ax=ax, color="#5ec962", edgecolor="#333333")
            ax.set_title("Endpoint-Level Median p95 Latency", fontsize=13, fontweight="bold", pad=12)
            ax.set_xlabel("p95 Latency (ms)", fontsize=11)
            ax.set_ylabel("API Endpoint", fontsize=11)
    plt.tight_layout()
    plt.savefig(figures_dir / "endpoint_latency_comparison.png")
    plt.close()

    logger.info("All 9 figures successfully generated in %s", figures_dir)


if __name__ == "__main__":
    generate_all_plots()

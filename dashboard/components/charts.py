from typing import Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dashboard.utils.formatting import STRATEGY_COLORS


def plot_latency_vs_concurrency(df: pd.DataFrame) -> Optional[go.Figure]:
    """Plot p50, p95, p99 response times against concurrency level."""
    if df is None or df.empty or "concurrency" not in df.columns:
        st.info("No data available for Latency vs Concurrency plot.")
        return None

    fig = go.Figure()

    # Aggregate by concurrency across selection
    grouped = df.groupby("concurrency").agg({
        "p50_latency_ms": "mean",
        "p95_latency_ms": "mean",
        "p99_latency_ms": "mean",
    }).reset_index().sort_values("concurrency")

    if "p50_latency_ms" in grouped.columns:
        fig.add_trace(go.Scatter(
            x=grouped["concurrency"],
            y=grouped["p50_latency_ms"],
            mode="lines+markers",
            name="p50 (Median)",
            line=dict(color="#1f77b4", width=2),
        ))

    if "p95_latency_ms" in grouped.columns:
        fig.add_trace(go.Scatter(
            x=grouped["concurrency"],
            y=grouped["p95_latency_ms"],
            mode="lines+markers",
            name="p95 Latency",
            line=dict(color="#ff7f0e", width=2.5),
        ))

    if "p99_latency_ms" in grouped.columns:
        fig.add_trace(go.Scatter(
            x=grouped["concurrency"],
            y=grouped["p99_latency_ms"],
            mode="lines+markers",
            name="p99 (Tail)",
            line=dict(color="#d62728", width=2, dash="dot"),
        ))

    fig.update_layout(
        title="Latency Percentiles vs Concurrency",
        xaxis_title="Concurrent Users",
        yaxis_title="Response Time (ms)",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def plot_throughput_vs_concurrency(df: pd.DataFrame) -> Optional[go.Figure]:
    """Plot throughput (RPS) against concurrency level."""
    if df is None or df.empty or "concurrency" not in df.columns or "rps" not in df.columns:
        st.info("No data available for Throughput plot.")
        return None

    grouped = df.groupby(["concurrency", "strategy"]).agg({"rps": "mean"}).reset_index()

    fig = px.line(
        grouped,
        x="concurrency",
        y="rps",
        color="strategy",
        markers=True,
        title="Throughput (Requests / Second) vs Concurrency",
        labels={"concurrency": "Concurrent Users", "rps": "Throughput (RPS)", "strategy": "Strategy"},
        color_discrete_map=STRATEGY_COLORS,
        template="plotly_white",
    )
    fig.update_layout(hovermode="x unified")
    return fig


def plot_strategy_bar_comparison(df: pd.DataFrame) -> Optional[go.Figure]:
    """Side-by-side bar chart of strategies across p50, p95, p99 and RPS."""
    if df is None or df.empty or "strategy" not in df.columns:
        return None

    grouped = df.groupby("strategy").agg({
        "p50_latency_ms": "mean",
        "p95_latency_ms": "mean",
        "p99_latency_ms": "mean",
        "rps": "mean",
    }).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=grouped["strategy"],
        y=grouped["p50_latency_ms"],
        name="p50 (ms)",
        marker_color="#1f77b4",
    ))
    fig.add_trace(go.Bar(
        x=grouped["strategy"],
        y=grouped["p95_latency_ms"],
        name="p95 (ms)",
        marker_color="#ff7f0e",
    ))
    fig.add_trace(go.Bar(
        x=grouped["strategy"],
        y=grouped["p99_latency_ms"],
        name="p99 (ms)",
        marker_color="#d62728",
    ))

    fig.update_layout(
        title="Strategy Latency Comparison Across Percentiles",
        xaxis_title="Concurrency Strategy",
        yaxis_title="Response Time (ms)",
        barmode="group",
        template="plotly_white",
    )
    return fig


def plot_pool_comparison(df: pd.DataFrame) -> Optional[go.Figure]:
    """Bar chart comparing connection pool throughput and latency."""
    if df is None or df.empty or "pool_name" not in df.columns:
        return None

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["pool_name"],
        y=df["rps"],
        name="Throughput (RPS)",
        marker_color="#2ca02c",
        yaxis="y",
    ))
    fig.add_trace(go.Bar(
        x=df["pool_name"],
        y=df["p95_latency_ms"],
        name="p95 Latency (ms)",
        marker_color="#9467bd",
        yaxis="y2",
    ))

    fig.update_layout(
        title="Connection Pool Configuration Comparison",
        xaxis_title="Connection Pool Preset",
        yaxis=dict(title="Throughput (RPS)"),
        yaxis2=dict(title="p95 Latency (ms)", overlaying="y", side="right"),
        barmode="group",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def plot_endpoint_breakdown(df: pd.DataFrame) -> Optional[go.Figure]:
    """Plot endpoint-level response times."""
    if df is None or df.empty or "endpoint" not in df.columns or "p95_latency_ms" not in df.columns:
        return None

    fig = px.bar(
        df,
        x="endpoint",
        y=["p50_latency_ms", "p95_latency_ms", "p99_latency_ms"],
        title="Endpoint-Level Latency Breakdown",
        labels={"value": "Latency (ms)", "endpoint": "API Endpoint", "variable": "Percentile"},
        barmode="group",
        template="plotly_white",
    )
    return fig

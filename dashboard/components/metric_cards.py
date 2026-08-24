from typing import Any, Dict, Optional
import streamlit as st
from dashboard.utils.formatting import format_int, format_ms, format_percentage, format_rps


def render_metric_cards(
    total_requests: Optional[int] = None,
    rps: Optional[float] = None,
    p50: Optional[float] = None,
    p95: Optional[float] = None,
    p99: Optional[float] = None,
    failure_rate: Optional[float] = None,
    consistent: Optional[bool] = None,
):
    """Render a clean grid of performance & consistency metric cards."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Requests",
            value=format_int(total_requests) if total_requests is not None else "N/A",
        )
        st.metric(
            label="Throughput",
            value=format_rps(rps) if rps is not None else "N/A",
        )

    with col2:
        st.metric(
            label="Median (p50)",
            value=format_ms(p50) if p50 is not None else "N/A",
        )
        st.metric(
            label="p95 Latency",
            value=format_ms(p95) if p95 is not None else "N/A",
        )

    with col3:
        st.metric(
            label="Tail (p99)",
            value=format_ms(p99) if p99 is not None else "N/A",
        )
        st.metric(
            label="Failure Rate",
            value=format_percentage(failure_rate) if failure_rate is not None else "0.00%",
        )

    with col4:
        status_str = "100% Valid" if consistent is True else ("Violated" if consistent is False else "N/A")
        st.metric(
            label="Consistency Invariants",
            value=status_str,
            delta="0 Anomalies" if consistent is True else ("Anomalies Detected" if consistent is False else None),
            delta_color="normal" if consistent is True else "inverse",
        )

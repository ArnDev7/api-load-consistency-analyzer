import streamlit as st


def render_project_disclosure():
    """Render prominent academic & synthetic system disclosure."""
    st.info(
        "ℹ️ **System & Educational Disclosure**: This project uses a simulated inventory-reservation system "
        "and controlled local workloads for educational and portfolio purposes. Results must not be interpreted as "
        "production-capacity guarantees."
    )


def render_hardware_warning():
    """Render hardware co-location disclosure."""
    st.warning(
        "⚠️ **Hardware Co-Location Notice**: The load generator (Locust), web application (FastAPI), and database (PostgreSQL) "
        "share the same local host resources. Measurements reflect local loopback dynamics and should not be directly generalized "
        "to multi-region cloud production environments."
    )

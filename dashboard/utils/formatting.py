from typing import Any, Optional


def format_ms(val: Optional[float], decimals: int = 2) -> str:
    """Format milliseconds value."""
    if val is None or (isinstance(val, float) and (val != val or val < 0)):
        return "N/A"
    return f"{val:.{decimals}f} ms"


def format_rps(val: Optional[float], decimals: int = 1) -> str:
    """Format requests per second."""
    if val is None or (isinstance(val, float) and (val != val or val < 0)):
        return "N/A"
    return f"{val:.{decimals}f} req/s"


def format_percentage(val: Optional[float], decimals: int = 2) -> str:
    """Format percentage value."""
    if val is None or (isinstance(val, float) and val != val):
        return "N/A"
    return f"{val:.{decimals}f}%"


def format_int(val: Optional[Any]) -> str:
    """Format integer with thousands separator."""
    if val is None:
        return "0"
    try:
        return f"{int(val):,}"
    except (ValueError, TypeError):
        return str(val)


# Color palette constants
STRATEGY_COLORS = {
    "atomic_update": "#1f77b4",  # Dark Blue
    "pessimistic_lock": "#ff7f0e",  # Orange
    "naive": "#d62728",  # Red / Unsafe
    "baseline": "#7f7f7f",  # Gray
    "indexed": "#2ca02c",  # Green
    "pool_tuned": "#9467bd",  # Purple
}

STATUS_COLORS = {
    "passed": "#2ca02c",
    "failed": "#d62728",
    "expected_rejection": "#ffbb78",
    "system_failure": "#d62728",
}

"""Test dataframe and metric validation utilities."""
import pandas as pd
from dashboard.utils.validation import validate_dataframe, clean_dataframe
from dashboard.utils.formatting import format_ms, format_rps, format_percentage, format_int


def test_dataframe_column_validation():
    """Verify validation of required DataFrame columns."""
    df = pd.DataFrame({"concurrency": [5, 10], "rps": [100.0, 200.0], "p95_latency_ms": [15.0, 25.0]})

    valid, missing = validate_dataframe(df, ["concurrency", "rps"])
    assert valid is True
    assert len(missing) == 0

    valid_false, missing_cols = validate_dataframe(df, ["concurrency", "non_existent_column"])
    assert valid_false is False
    assert missing_cols == ["non_existent_column"]

    # Empty / None df handling
    assert validate_dataframe(None, ["a", "b"])[0] is False
    assert validate_dataframe(pd.DataFrame(), ["a", "b"])[0] is False


def test_clean_dataframe():
    """Verify safe sanitization of NaN and null values."""
    df_with_nans = pd.DataFrame({
        "num": [1.0, None, 3.0],
        "text": ["a", None, "c"],
    })
    cleaned = clean_dataframe(df_with_nans)
    assert not cleaned.isnull().values.any()


def test_formatting_helpers():
    """Verify formatting functions format metrics cleanly."""
    assert format_ms(12.3456) == "12.35 ms"
    assert format_ms(None) == "N/A"
    assert format_rps(333.28) == "333.3 req/s"
    assert format_percentage(0.0) == "0.00%"
    assert format_int(213185) == "213,185"

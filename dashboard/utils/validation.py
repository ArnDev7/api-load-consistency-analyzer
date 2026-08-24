from typing import List, Tuple
import pandas as pd


def validate_dataframe(df: pd.DataFrame, required_columns: List[str]) -> Tuple[bool, List[str]]:
    """Check if DataFrame contains all required columns."""
    if df is None or df.empty:
        return False, required_columns
    missing = [col for col in required_columns if col not in df.columns]
    return len(missing) == 0, missing


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Safely sanitize DataFrame for UI rendering."""
    if df is None:
        return pd.DataFrame()
    return df.copy().fillna({
        col: 0 if df[col].dtype.kind in "biufc" else "" for col in df.columns
    })

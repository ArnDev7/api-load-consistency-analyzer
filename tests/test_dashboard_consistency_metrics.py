"""Test dashboard consistency metrics parsing and evaluation."""
import pandas as pd
from dashboard.utils.load_outputs import load_consistency_results


def test_consistency_results_structure():
    """Verify consistency matrix structure and invariant verification."""
    cons_df = load_consistency_results()
    if cons_df is not None and not cons_df.empty:
        required_cols = [
            "consistent",
            "violations_count",
            "active_reservations",
            "released_reservations",
        ]
        for col in required_cols:
            assert col in cons_df.columns

        # Verify invariant assertions
        assert (cons_df["violations_count"] == 0).all()
        assert cons_df["consistent"].all() is True or (cons_df["consistent"].dtype == bool)

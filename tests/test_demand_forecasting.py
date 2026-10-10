
import pandas as pd

from src.forecasting.demand_forecasting import (
    MIN_SELLING_DAYS,
    make_daily_series,
)


def test_minimum_selling_days_threshold():
    """The forecasting threshold should require 30 selling days."""
    assert MIN_SELLING_DAYS == 30


def test_daily_series_fills_missing_dates_with_zero():
    """Dates without transactions should have zero recorded sales."""
    data = pd.DataFrame(
        {
            "order_date": pd.to_datetime(
                ["2024-01-01", "2024-01-03"]
            ),
            "stock_code": pd.Series(["P001", "P001"], dtype="string"),
            "units_sold": [5, 8],
        }
    )

    result = make_daily_series(
        data,
        "P001",
        pd.Timestamp("2024-01-01"),
        pd.Timestamp("2024-01-03"),
    )

    assert len(result) == 3
    assert result.loc[pd.Timestamp("2024-01-01")] == 5
    assert result.loc[pd.Timestamp("2024-01-02")] == 0
    assert result.loc[pd.Timestamp("2024-01-03")] == 8


def test_daily_series_keeps_products_separate():
    """Sales for different products must not be mixed."""
    data = pd.DataFrame(
        {
            "order_date": pd.to_datetime(
                ["2024-01-01", "2024-01-01"]
            ),
            "stock_code": pd.Series(["P001", "P002"], dtype="string"),
            "units_sold": [5, 20],
        }
    )

    result = make_daily_series(
        data,
        "P001",
        pd.Timestamp("2024-01-01"),
        pd.Timestamp("2024-01-01"),
    )

    assert result.iloc[0] == 5

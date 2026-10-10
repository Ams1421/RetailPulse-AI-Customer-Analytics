
import pandas as pd
import pytest

from src.inventory.inventory_optimization import (
    calculate_inventory_recommendations,
)


def make_forecasts(stock_code, daily_demand, days=14):
    return pd.DataFrame(
        {
            "stock_code": [stock_code] * days,
            "forecast_date": pd.date_range(
                "2024-01-01", periods=days
            ),
            "predicted_units": [daily_demand] * days,
        }
    )


def test_inventory_formula_for_constant_demand():
    forecasts = make_forecasts("P001", 10)

    result = calculate_inventory_recommendations(forecasts)
    product = result.set_index("stock_code").loc["P001"]

    assert product["average_daily_forecast"] == 10
    assert product["lead_time_demand"] == 70
    assert product["safety_stock"] == 30
    assert product["reorder_point"] == 100
    assert product["assumed_stock_on_hand"] == 70
    assert product["suggested_replenishment_units"] == 30
    assert product["planning_status"] == "Reorder suggested"


def test_zero_demand_has_zero_replenishment():
    forecasts = make_forecasts("P001", 0)

    result = calculate_inventory_recommendations(forecasts)
    product = result.set_index("stock_code").loc["P001"]

    assert product["suggested_replenishment_units"] == 0


def test_inventory_products_are_calculated_separately():
    forecasts = pd.concat(
        [
            make_forecasts("P001", 10),
            make_forecasts("P002", 20),
        ],
        ignore_index=True,
    )

    result = calculate_inventory_recommendations(forecasts)
    result = result.set_index("stock_code")

    assert result.loc["P001", "average_daily_forecast"] == 10
    assert result.loc["P002", "average_daily_forecast"] == 20
    assert result.loc["P001", "suggested_replenishment_units"] == 30
    assert result.loc["P002", "suggested_replenishment_units"] == 60


def test_negative_forecast_is_rejected():
    forecasts = make_forecasts("P001", 10)
    forecasts.loc[0, "predicted_units"] = -1

    with pytest.raises(ValueError, match="Negative forecast demand"):
        calculate_inventory_recommendations(forecasts)


def test_missing_required_columns_are_rejected():
    forecasts = pd.DataFrame({"stock_code": ["P001"]})

    with pytest.raises(ValueError, match="missing required columns"):
        calculate_inventory_recommendations(forecasts)

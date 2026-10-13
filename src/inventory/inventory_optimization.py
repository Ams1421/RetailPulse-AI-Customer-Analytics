
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FORECAST_FILE = ROOT / "data" / "demand_forecasts.csv"
OUTPUT_DIR = ROOT / "data"
REPORT_DIR = ROOT / "reports"

# Planning assumptions; actual stock and supplier data are unavailable.
LEAD_TIME_DAYS = 7
SAFETY_STOCK_DAYS = 3
ASSUMED_STOCK_COVER_DAYS = 7


def calculate_inventory_recommendations(
    forecasts: pd.DataFrame,
    lead_time_days: int = LEAD_TIME_DAYS,
    safety_stock_days: int = SAFETY_STOCK_DAYS,
    assumed_stock_cover_days: int = ASSUMED_STOCK_COVER_DAYS,
) -> pd.DataFrame:
    """Calculate inventory recommendations from product-level forecasts."""

    required_columns = {
        "stock_code",
        "forecast_date",
        "predicted_units",
    }
    missing_columns = required_columns.difference(forecasts.columns)

    if missing_columns:
        raise ValueError(
            "Forecast data is missing required columns: "
            f"{', '.join(sorted(missing_columns))}"
        )

    if min(
        lead_time_days,
        safety_stock_days,
        assumed_stock_cover_days,
    ) < 0:
        raise ValueError(
            "Inventory planning assumptions cannot be negative."
        )

    data = forecasts.copy()

    data["predicted_units"] = pd.to_numeric(
        data["predicted_units"], errors="coerce"
    )
    data["forecast_date"] = pd.to_datetime(
        data["forecast_date"], errors="coerce"
    )

    data = data.dropna(
        subset=["stock_code", "forecast_date", "predicted_units"]
    )

    if data.empty:
        raise ValueError("Forecast data contains no valid forecast rows.")

    if (data["predicted_units"] < 0).any():
        raise ValueError("Negative forecast demand found.")

    product_demand = data.groupby("stock_code").agg(
        average_daily_forecast=("predicted_units", "mean"),
        total_forecast_demand=("predicted_units", "sum"),
        forecast_days=("forecast_date", "nunique"),
    )

    product_demand["lead_time_demand"] = (
        product_demand["average_daily_forecast"] * lead_time_days
    )

    product_demand["safety_stock"] = (
        product_demand["average_daily_forecast"] * safety_stock_days
    )

    product_demand["reorder_point"] = (
        product_demand["lead_time_demand"]
        + product_demand["safety_stock"]
    )

    product_demand["assumed_stock_on_hand"] = (
        product_demand["average_daily_forecast"]
        * assumed_stock_cover_days
    )

    product_demand["suggested_replenishment_units"] = np.ceil(
        (
            product_demand["reorder_point"]
            - product_demand["assumed_stock_on_hand"]
        ).clip(lower=0)
    ).astype(int)

    product_demand["planning_status"] = np.where(
        product_demand["assumed_stock_on_hand"]
        <= product_demand["reorder_point"],
        "Reorder suggested",
        "Stock above reorder point",
    )

    return product_demand.round(2).reset_index()


def main():
    if not FORECAST_FILE.exists():
        raise FileNotFoundError(
            f"Missing {FORECAST_FILE}. Run demand_forecasting.py first."
        )

    forecasts = pd.read_csv(
        FORECAST_FILE,
        parse_dates=["forecast_date"],
        dtype={"stock_code": "string"},
    )

    recommendations = calculate_inventory_recommendations(forecasts)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = OUTPUT_DIR / "inventory_recommendations.csv"
    recommendations.to_csv(output_file, index=False)

    reorder_count = int(
        (
            recommendations["planning_status"]
            == "Reorder suggested"
        ).sum()
    )

    report = [
        "RETAILPULSE - INVENTORY PLANNING",
        "=" * 45,
        f"Products analyzed: {len(recommendations):,}",
        (
            "Forecast horizon in input: "
            f"{int(recommendations['forecast_days'].max())} days"
        ),
        f"Assumed supplier lead time: {LEAD_TIME_DAYS} days",
        (
            "Assumed safety-stock buffer: "
            f"{SAFETY_STOCK_DAYS} days of average forecast demand"
        ),
        (
            "Assumed starting stock: "
            f"{ASSUMED_STOCK_COVER_DAYS} days of average forecast demand"
        ),
        f"Products flagged for reorder: {reorder_count:,}",
        "",
        "INVENTORY RECOMMENDATIONS",
        "-" * 45,
        recommendations.to_string(index=False),
        "",
        "IMPORTANT LIMITATIONS",
        "-" * 45,
        "Actual stock-on-hand and supplier lead-time records were unavailable.",
        "Starting stock is assumed to equal seven days of average forecast demand.",
        "Recommendations are planning estimates, not confirmed purchase orders.",
    ]

    report_file = REPORT_DIR / "inventory_planning_summary.txt"
    report_file.write_text("\n".join(report) + "\n", encoding="utf-8")

    print("Inventory planning completed successfully.")
    print(f"Products analyzed: {len(recommendations):,}")
    print(f"Products flagged for reorder: {reorder_count:,}")
    print(f"Recommendations saved to: {output_file}")
    print(f"Summary saved to: {report_file}")
    print()
    print(recommendations.to_string(index=False))


if __name__ == "__main__":
    main()

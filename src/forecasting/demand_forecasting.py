
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = ROOT / "data" / "processed" / "daily_product_sales.csv"
OUTPUT_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"
FIGURES_DIR = REPORT_DIR / "figures"

TEST_DAYS = 28
FORECAST_DAYS = 14
TOP_PRODUCTS = 10
MIN_SELLING_DAYS = 30


def make_daily_series(data, product_code, start_date, end_date):
    product_data = data[data["stock_code"] == product_code]
    daily = product_data.groupby("order_date")["units_sold"].sum()

    calendar = pd.date_range(start_date, end_date, freq="D")
    daily.index = pd.to_datetime(daily.index)

    # Missing transaction dates represent zero recorded sales.
    return daily.reindex(calendar, fill_value=0).astype(float)


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing {INPUT_FILE}. Run build_features.py first."
        )

    print("Loading daily product sales...")
    df = pd.read_csv(
        INPUT_FILE,
        parse_dates=["order_date"],
        dtype={"stock_code": "string"},
        low_memory=False,
    )

    df["units_sold"] = pd.to_numeric(df["units_sold"], errors="coerce")
    df = df.dropna(subset=["order_date", "stock_code", "units_sold"])
    df["order_date"] = df["order_date"].dt.normalize()

    # Select high-volume products only when sufficient sales history exists.
    positive_sales = df[df["units_sold"] > 0].copy()

    product_activity = (
        positive_sales.groupby("stock_code")
        .agg(
            total_units=("units_sold", "sum"),
            selling_days=("order_date", "nunique"),
        )
        .sort_values("total_units", ascending=False)
    )

    eligible_products = product_activity[
        product_activity["selling_days"] >= MIN_SELLING_DAYS
    ]

    excluded_products = product_activity[
        product_activity["selling_days"] < MIN_SELLING_DAYS
    ]

    print(
        f"Products excluded for fewer than {MIN_SELLING_DAYS} selling days: "
        f"{len(excluded_products)}"
    )

    if not excluded_products.empty:
        print("Examples of excluded products:")
        print(excluded_products.head(10).to_string())

    top_products = eligible_products.head(TOP_PRODUCTS).index.tolist()

    if not top_products:
        raise ValueError(
            "No products have sufficient sales history. "
            "Review the dataset before reducing MIN_SELLING_DAYS."
        )

    last_date = df["order_date"].max().normalize()
    first_date = df["order_date"].min().normalize()
    test_start = last_date - pd.Timedelta(days=TEST_DAYS - 1)

    forecast_rows = []
    metric_rows = []
    chart_products = set(top_products[:5])

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    for product_code in top_products:
        series = make_daily_series(
            df, product_code, first_date, last_date
        )

        train = series[series.index < test_start]
        test = series[series.index >= test_start]

        if len(train) < 14 or len(test) != TEST_DAYS:
            print(f"Skipping {product_code}: insufficient history.")
            continue

        # Baseline A: same weekday from the preceding week.
        seasonal_predictions = np.array(
            [
                series.loc[date - pd.Timedelta(days=7)]
                for date in test.index
            ],
            dtype=float,
        )

        # Baseline B: average demand across the last 7 training days.
        rolling_mean_value = float(train.tail(7).mean())
        mean_predictions = np.full(len(test), rolling_mean_value)
        actual = test.to_numpy(dtype=float)

        seasonal_mae = mean_absolute_error(actual, seasonal_predictions)
        seasonal_rmse = np.sqrt(
            mean_squared_error(actual, seasonal_predictions)
        )
        mean_mae = mean_absolute_error(actual, mean_predictions)
        mean_rmse = np.sqrt(
            mean_squared_error(actual, mean_predictions)
        )

        selected_name = (
            "7-day seasonal naive"
            if seasonal_mae <= mean_mae
            else "7-day average"
        )

        metric_rows.extend([
            {
                "stock_code": str(product_code),
                "baseline": "7-day seasonal naive",
                "mae": seasonal_mae,
                "rmse": seasonal_rmse,
            },
            {
                "stock_code": str(product_code),
                "baseline": "7-day average",
                "mae": mean_mae,
                "rmse": mean_rmse,
            },
        ])

        # Generate future forecasts recursively.
        history = series.copy()

        for future_date in pd.date_range(
            last_date + pd.Timedelta(days=1),
            last_date + pd.Timedelta(days=FORECAST_DAYS),
            freq="D",
        ):
            if selected_name == "7-day seasonal naive":
                source_date = future_date - pd.Timedelta(days=7)
                predicted_demand = float(history.loc[source_date])
            else:
                predicted_demand = float(history.tail(7).mean())

            predicted_demand = max(0.0, predicted_demand)

            forecast_rows.append({
                "stock_code": str(product_code),
                "forecast_date": future_date,
                "predicted_units": predicted_demand,
                "selected_baseline": selected_name,
            })

            history.loc[future_date] = predicted_demand

        if product_code in chart_products:
            plt.figure(figsize=(10, 4))
            series.tail(60).plot(label="Recorded units")
            plt.axvline(
                test_start,
                linestyle="--",
                label="Test period start",
            )
            plt.title(f"Demand History - Product {product_code}")
            plt.xlabel("Date")
            plt.ylabel("Units sold")
            plt.legend()
            plt.tight_layout()

            safe_code = "".join(
                char if char.isalnum() or char in "-_" else "_"
                for char in str(product_code)
            )
            plt.savefig(
                FIGURES_DIR / f"demand_history_{safe_code}.png",
                dpi=130,
            )
            plt.close()

    if not metric_rows or not forecast_rows:
        raise ValueError(
            "No products completed forecasting. Check data coverage and settings."
        )

    metrics = pd.DataFrame(metric_rows)
    forecasts = pd.DataFrame(forecast_rows)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    metrics.to_csv(OUTPUT_DIR / "forecast_evaluation.csv", index=False)
    forecasts.to_csv(OUTPUT_DIR / "demand_forecasts.csv", index=False)

    excluded_file = OUTPUT_DIR / "forecast_excluded_products.csv"
    excluded_products.reset_index().to_csv(excluded_file, index=False)

    summary = metrics.groupby("baseline")[["mae", "rmse"]].mean().round(3)

    report_lines = [
        "RETAILPULSE - DEMAND FORECASTING",
        "=" * 45,
        f"Observed data range: {first_date.date()} to {last_date.date()}",
        f"Evaluation period: {test_start.date()} to {last_date.date()}",
        f"Forecast horizon: {FORECAST_DAYS} days",
        f"Minimum distinct selling days required: {MIN_SELLING_DAYS}",
        f"Eligible products: {len(eligible_products):,}",
        f"Products excluded for insufficient selling days: {len(excluded_products):,}",
        f"Products evaluated: {metrics['stock_code'].nunique()}",
        "",
        "AVERAGE EVALUATION METRICS ACROSS PRODUCTS",
        "-" * 45,
        summary.to_string(),
        "",
        "PER-PRODUCT METRICS",
        "-" * 45,
        metrics.to_string(index=False),
        "",
        "SELECTED FORECAST METHODS",
        "-" * 45,
        forecasts.groupby(
            ["stock_code", "selected_baseline"]
        ).size().to_string(),
        "",
        "OUTPUTS",
        "-" * 45,
        str(OUTPUT_DIR / "forecast_evaluation.csv"),
        str(OUTPUT_DIR / "demand_forecasts.csv"),
        str(excluded_file),
        str(REPORT_DIR / "demand_forecasting_summary.txt"),
        "",
        "LIMITATIONS",
        "-" * 45,
        "These are baseline forecasts, not a tuned production model.",
        "The minimum selling-day threshold is a screening rule, not proof of forecast reliability.",
        "Zero recorded sales does not prove the product was available but unsold.",
        "Returns, stock availability, promotions, and holidays are not modeled separately.",
        "The evaluation period is used to select the better baseline per product.",
        "Evaluation results are model-selection results, not an untouched final test.",
    ]

    report_text = "\n".join(report_lines)
    (REPORT_DIR / "demand_forecasting_summary.txt").write_text(
        report_text, encoding="utf-8"
    )
    print(report_text)


if __name__ == "__main__":
    main()

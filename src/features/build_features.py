from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = ROOT / "data" / "retail_transactions_cleaned.csv.gz"
OUTPUT_DIR = ROOT / "data"
REPORT_FILE = ROOT / "reports" / "feature_engineering_summary.txt"


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing {INPUT_FILE}. Run src/data/clean_dataset.py first."
        )

    print("Loading cleaned transactions...")
    df = pd.read_csv(INPUT_FILE, compression="gzip", low_memory=False)
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")

    # Keep standard positive sales for these initial business features.
    sales = df[
        df["customer_id"].notna()
        & (~df["is_cancellation_invoice"].astype(bool))
        & (df["quantity"] > 0)
        & (df["unit_price"] > 0)
        & (df["line_revenue"] > 0)
        & df["invoice_date"].notna()
    ].copy()

    sales["customer_id"] = sales["customer_id"].astype("int64")
    sales["order_date"] = sales["invoice_date"].dt.normalize()
    sales["month"] = sales["invoice_date"].dt.to_period("M").astype(str)
    sales["day_of_week"] = sales["invoice_date"].dt.dayofweek
    sales["hour"] = sales["invoice_date"].dt.hour

    # Customer-level features
    reference_date = sales["invoice_date"].max().normalize() + pd.Timedelta(days=1)

    customer_features = sales.groupby("customer_id").agg(
        first_purchase=("invoice_date", "min"),
        last_purchase=("invoice_date", "max"),
        invoice_count=("invoice", "nunique"),
        total_items=("quantity", "sum"),
        total_spend=("line_revenue", "sum"),
        average_line_value=("line_revenue", "mean"),
        distinct_products=("stock_code", "nunique"),
        distinct_countries=("country", "nunique"),
    )

    customer_features["recency_days"] = (
        reference_date - customer_features["last_purchase"].dt.normalize()
    ).dt.days

    customer_features["customer_lifetime_days"] = (
        customer_features["last_purchase"].dt.normalize()
        - customer_features["first_purchase"].dt.normalize()
    ).dt.days

    customer_features["average_order_value"] = (
        customer_features["total_spend"]
        / customer_features["invoice_count"].clip(lower=1)
    )

    customer_features["spend_per_item"] = (
        customer_features["total_spend"]
        / customer_features["total_items"].replace(0, pd.NA)
    )


    customer_features = customer_features.reset_index()

    # ---------------------------------------------------------
    # RetailPulse custom features created from customer history
    # ---------------------------------------------------------

    # 1. Season of the customer's most recent purchase.
    # These seasons use meteorological calendar months.
    last_purchase_month = pd.to_datetime(
        customer_features["last_purchase"]
    ).dt.month

    customer_features["RP_Purchase_Season"] = last_purchase_month.map(
        {
            12: "Winter",
            1: "Winter",
            2: "Winter",
            3: "Spring",
            4: "Spring",
            5: "Spring",
            6: "Summer",
            7: "Summer",
            8: "Summer",
            9: "Autumn",
            10: "Autumn",
            11: "Autumn",
        }
    )

    # 2. Group customers by how recently they purchased.
    customer_features["RP_Purchase_Recency_Band"] = pd.cut(
        customer_features["recency_days"],
        bins=[-1, 30, 90, 180, float("inf")],
        labels=["Recent", "Warm", "Cooling", "Dormant"],
    ).astype("string")

    # 3. Group customers by total historical spending.
    # Quartile boundaries are calculated from this customer dataset.
    customer_features["RP_Customer_Value_Band"] = pd.qcut(
        customer_features["total_spend"].rank(method="first"),
        q=4,
        labels=["Low", "Medium", "High", "Very High"],
    ).astype("string")

    # 4. Group customers by the number of distinct products purchased.
    customer_features["RP_Product_Diversity_Band"] = pd.qcut(
        customer_features["distinct_products"].rank(method="first"),
        q=4,
        labels=["Low", "Medium", "High", "Very High"],
    ).astype("string")

    # 5. A bounded loyalty index using purchase frequency
    # and the number of days between the first and last purchase.
    # A one-day minimum avoids division by zero.
    active_lifetime = customer_features[
        "customer_lifetime_days"
    ].clip(lower=1)

    purchase_rate = (
        customer_features["invoice_count"] / active_lifetime
    )

    customer_features["RP_Customer_Loyalty_Index"] = (
        100
        * purchase_rate
        / (purchase_rate + purchase_rate.median())
    ).round(2)

    # Save the reference date used to calculate recency.
    customer_features["reference_date"] = reference_date


    customer_features["reference_date"] = reference_date

    # Daily product demand features for forecasting.
    daily_product_sales = sales.groupby(
        ["order_date", "stock_code"], as_index=False
    ).agg(
        units_sold=("quantity", "sum"),
        sales_revenue=("line_revenue", "sum"),
        invoice_count=("invoice", "nunique"),
    )

    daily_product_sales = daily_product_sales.sort_values(
        ["stock_code", "order_date"]
    )

    # Calendar features are known in advance and useful for forecasting.
    daily_product_sales["day_of_week"] = (
        daily_product_sales["order_date"].dt.dayofweek
    )
    daily_product_sales["month"] = daily_product_sales["order_date"].dt.month
    daily_product_sales["year"] = daily_product_sales["order_date"].dt.year
    daily_product_sales["is_weekend"] = (
        daily_product_sales["day_of_week"] >= 5
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    customer_file = OUTPUT_DIR / "customer_features.csv"
    demand_file = OUTPUT_DIR / "daily_product_sales.csv"

    customer_features.to_csv(customer_file, index=False)
    daily_product_sales.to_csv(demand_file, index=False)

    summary = [
        "RETAILPULSE - FEATURE ENGINEERING SUMMARY",
        "=" * 45,
        f"Reference date: {reference_date.date()}",
        f"Eligible sales transaction rows: {len(sales):,}",
        f"Customer feature rows: {len(customer_features):,}",
        f"Customer feature columns: {len(customer_features.columns):,}",
        f"Daily product records: {len(daily_product_sales):,}",
        f"Distinct products in demand table: {daily_product_sales['stock_code'].nunique():,}",
        f"First demand date: {daily_product_sales['order_date'].min()}",
        f"Last demand date: {daily_product_sales['order_date'].max()}",
        "",
        "Customer features:",
        ", ".join(customer_features.columns),
        "",
        "Daily product features:",
        ", ".join(daily_product_sales.columns),
        "",
        "Outputs:",
        str(customer_file),
        str(demand_file),
        "",
        "Notes:",
        "Features use positive, identifiable-customer sales only.",
        "The reference date is one day after the latest eligible transaction.",
        "Churn labels and forecasting targets have not been created yet.",
    ]

    REPORT_FILE.write_text("\n".join(summary), encoding="utf-8")
    print("\n".join(summary))


if __name__ == "__main__":
    main()

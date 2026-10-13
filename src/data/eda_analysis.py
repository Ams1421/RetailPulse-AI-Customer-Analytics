from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = ROOT / "data" / "retail_transactions_cleaned.csv.gz"
FIGURES_DIR = ROOT / "reports" / "figures"
REPORT_FILE = ROOT / "reports" / "eda_summary.txt"


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Cleaned dataset not found: {DATA_FILE}. Run clean_dataset.py first."
        )

    print("Loading cleaned transactions...")
    df = pd.read_csv(
        DATA_FILE,
        compression="gzip",
        parse_dates=["invoice_date"],
        low_memory=False,
    )

    # Revenue KPIs should exclude cancellation invoices, returns, and
    # non-positive prices. These rules are for EDA only; raw data is retained.
    sales = df[
        (~df["is_cancellation_invoice"])
        & (df["quantity"] > 0)
        & (df["unit_price"] > 0)
    ].copy()

    sales["month"] = sales["invoice_date"].dt.to_period("M").astype(str)

    monthly_revenue = sales.groupby("month")["line_revenue"].sum()
    country_revenue = (
        sales.groupby("country")["line_revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )
    product_revenue = (
        sales.groupby("description")["line_revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )
    customer_revenue = (
        sales.dropna(subset=["customer_id"])
        .groupby("customer_id")["line_revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # Monthly revenue chart
    plt.figure(figsize=(12, 5))
    monthly_revenue.plot()
    plt.title("RetailPulse - Monthly Revenue")
    plt.xlabel("Month")
    plt.ylabel("Revenue")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "monthly_revenue.png", dpi=150)
    plt.close()

    # Top countries chart
    plt.figure(figsize=(10, 6))
    country_revenue.sort_values().plot(kind="barh")
    plt.title("Top 10 Countries by Sales Revenue")
    plt.xlabel("Revenue")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "top_countries_revenue.png", dpi=150)
    plt.close()

    # Top products chart
    plt.figure(figsize=(10, 6))
    product_revenue.sort_values().plot(kind="barh")
    plt.title("Top 10 Products by Sales Revenue")
    plt.xlabel("Revenue")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "top_products_revenue.png", dpi=150)
    plt.close()

    report = [
        "RETAILPULSE - EXPLORATORY DATA ANALYSIS",
        "=" * 45,
        f"Cleaned transaction rows: {len(df):,}",
        f"Rows used for standard sales analysis: {len(sales):,}",
        f"Unique customers in sales subset: {sales['customer_id'].nunique():,}",
        f"Unique products in sales subset: {sales['stock_code'].nunique():,}",
        f"Countries in sales subset: {sales['country'].nunique():,}",
        f"Total standard sales revenue: {sales['line_revenue'].sum():,.2f}",
        f"Invoice count in sales subset: {sales['invoice'].nunique():,}",
        "",
        "MONTHLY REVENUE",
        "-" * 45,
        monthly_revenue.to_string(),
        "",
        "TOP 10 COUNTRIES BY REVENUE",
        "-" * 45,
        country_revenue.to_string(),
        "",
        "TOP 10 PRODUCTS BY REVENUE",
        "-" * 45,
        product_revenue.to_string(),
        "",
        "TOP 10 CUSTOMERS BY REVENUE",
        "-" * 45,
        customer_revenue.to_string(),
        "",
        "Charts saved in reports/figures/.",
        "Revenue excludes cancellation invoices, negative quantities, and non-positive prices.",
        "These are preliminary business-analysis rules and should be documented.",
    ]

    REPORT_FILE.write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))
    print(f"\nEDA report saved to: {REPORT_FILE}")


if __name__ == "__main__":
    main()

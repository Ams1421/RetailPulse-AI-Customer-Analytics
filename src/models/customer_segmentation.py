from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = ROOT / "data" / "processed" / "retail_transactions_cleaned.csv.gz"
OUTPUT_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"
FIGURES_DIR = REPORT_DIR / "figures"


def main():
    print("Loading transactions...")
    df = pd.read_csv(DATA_FILE, compression="gzip", low_memory=False)
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")

    # Use only identifiable customers and ordinary positive sales.
    sales = df[
        df["customer_id"].notna()
        & (~df["is_cancellation_invoice"].astype(bool))
        & (df["quantity"] > 0)
        & (df["unit_price"] > 0)
        & (df["line_revenue"] > 0)
        & df["invoice_date"].notna()
    ].copy()

    if sales.empty:
        raise ValueError("No eligible sales rows found for customer segmentation.")

    # Make customer IDs consistent and monetary values numeric.
    sales["customer_id"] = sales["customer_id"].astype("int64")
    sales["line_revenue"] = pd.to_numeric(
        sales["line_revenue"], errors="coerce"
    )
    sales = sales.dropna(subset=["line_revenue"])

    # Reference date is one day after the latest transaction.
    reference_date = sales["invoice_date"].max().normalize() + pd.Timedelta(days=1)

    rfm = sales.groupby("customer_id").agg(
        last_purchase=("invoice_date", "max"),
        frequency=("invoice", "nunique"),
        monetary=("line_revenue", "sum"),
    )

    rfm["recency"] = (
        reference_date - rfm["last_purchase"].dt.normalize()
    ).dt.days

    rfm = rfm[["recency", "frequency", "monetary"]].copy()
    rfm = rfm.replace([np.inf, -np.inf], np.nan).dropna()
    rfm = rfm[
        (rfm["frequency"] > 0)
        & (rfm["monetary"] > 0)
        & (rfm["recency"] >= 0)
    ].copy()

    if len(rfm) < 4:
        raise ValueError("At least four eligible customers are required.")

    # RFM scores: higher recency score means a more recent purchase.
    rfm["R_score"] = pd.qcut(
        rfm["recency"].rank(method="first"),
        q=5,
        labels=[5, 4, 3, 2, 1],
    ).astype(int)

    rfm["F_score"] = pd.qcut(
        rfm["frequency"].rank(method="first"),
        q=5,
        labels=[1, 2, 3, 4, 5],
    ).astype(int)

    rfm["M_score"] = pd.qcut(
        rfm["monetary"].rank(method="first"),
        q=5,
        labels=[1, 2, 3, 4, 5],
    ).astype(int)

    # Log-transform skewed monetary/frequency features before scaling.
    model_features = pd.DataFrame(index=rfm.index)
    model_features["recency"] = np.log1p(rfm["recency"])
    model_features["frequency"] = np.log1p(rfm["frequency"])
    model_features["monetary"] = np.log1p(rfm["monetary"])

    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(model_features)

    model = KMeans(n_clusters=4, random_state=42, n_init=10)
    rfm["cluster"] = model.fit_predict(scaled_features)

    # Cluster numbers are arbitrary; inspect the profile before naming groups.
    cluster_summary = rfm.groupby("cluster").agg(
        customers=("recency", "size"),
        avg_recency_days=("recency", "mean"),
        avg_invoices=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
        median_monetary=("monetary", "median"),
    ).round(2)

    # Save results.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    rfm.to_csv(OUTPUT_DIR / "customer_rfm_segments.csv", index_label="customer_id")
    cluster_summary.to_csv(REPORT_DIR / "customer_cluster_summary.csv")

    plt.figure(figsize=(9, 5))
    cluster_summary["customers"].sort_index().plot(kind="bar")
    plt.title("RetailPulse - Customers per K-Means Cluster")
    plt.xlabel("Cluster ID")
    plt.ylabel("Number of Customers")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "customer_cluster_counts.png", dpi=150)
    plt.close()

    report = [
        "RETAILPULSE - CUSTOMER SEGMENTATION",
        "=" * 45,
        f"Reference date: {reference_date.date()}",
        f"Eligible transaction rows: {len(sales):,}",
        f"Customers segmented: {len(rfm):,}",
        f"K-Means clusters: {rfm['cluster'].nunique()}",
        f"K-Means inertia: {model.inertia_:.2f}",
        "",
        "RFM SCORE GUIDE",
        "-" * 45,
        "R_score: 5 means most recent; 1 means least recent.",
        "F_score: 5 means highest purchase frequency.",
        "M_score: 5 means highest monetary value.",
        "Cluster IDs are arbitrary; use the profile below to interpret them.",
        "",
        "CLUSTER PROFILES",
        "-" * 45,
        cluster_summary.to_string(),
        "",
        "Outputs:",
        "data/processed/customer_rfm_segments.csv",
        "reports/customer_cluster_summary.csv",
        "reports/figures/customer_cluster_counts.png",
    ]

    report_text = "\n".join(report)
    (REPORT_DIR / "customer_segmentation_summary.txt").write_text(
        report_text, encoding="utf-8"
    )
    print(report_text)


if __name__ == "__main__":
    main()

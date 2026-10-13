from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = PROJECT_ROOT / "data" / "online_retail_II.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "data"
OUTPUT_FILE = OUTPUT_DIR / "retail_transactions_cleaned.csv.gz"
REPORT_FILE = PROJECT_ROOT / "reports" / "cleaning_summary.txt"

SHEETS = ["Year 2009-2010", "Year 2010-2011"]

REQUIRED_COLUMNS = [
    "Invoice", "StockCode", "Description", "Quantity",
    "InvoiceDate", "Price", "Customer ID", "Country",
]


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

    frames = []
    for sheet in SHEETS:
        print(f"Loading {sheet}...")
        frames.append(pd.read_excel(DATA_FILE, sheet_name=sheet))

    df = pd.concat(frames, ignore_index=True)

    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in df.columns
    ]
    if missing_columns:
        raise ValueError(f"Missing expected columns: {missing_columns}")

    original_rows = len(df)

    # Remove exact duplicate transaction records before adding derived fields.
    duplicate_count = int(df.duplicated(subset=REQUIRED_COLUMNS).sum())
    df = df.drop_duplicates(subset=REQUIRED_COLUMNS).copy()

    # Standardize column names.
    df = df.rename(columns={
        "Invoice": "invoice",
        "StockCode": "stock_code",
        "Description": "description",
        "Quantity": "quantity",
        "InvoiceDate": "invoice_date",
        "Price": "unit_price",
        "Customer ID": "customer_id",
        "Country": "country",
    })

    # Convert data types.
    df["invoice"] = df["invoice"].astype("string").str.strip()
    df["stock_code"] = df["stock_code"].astype("string").str.strip()
    df["description"] = df["description"].astype("string").str.strip()
    df["country"] = df["country"].astype("string").str.strip()

    df["invoice_date"] = pd.to_datetime(
        df["invoice_date"], errors="coerce"
    )
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["customer_id"] = pd.to_numeric(
        df["customer_id"], errors="coerce"
    ).astype("Int64")

    # Normalize blank descriptions without discarding product codes.
    df["description"] = df["description"].replace("", pd.NA)
    missing_descriptions = int(df["description"].isna().sum())
    df["description"] = df["description"].fillna("Unknown")

    # Retain unusual transactions and label them for later analysis.
    df["is_cancellation_invoice"] = (
        df["invoice"].str.startswith("C", na=False)
    )
    df["is_return"] = df["quantity"] < 0
    df["is_negative_price"] = df["unit_price"] < 0
    df["is_zero_price"] = df["unit_price"] == 0
    df["has_customer_id"] = df["customer_id"].notna()

    # A transaction line's signed value; returns can have negative revenue.
    df["line_revenue"] = df["quantity"] * df["unit_price"]

    # Place key columns first for readability.
    ordered_columns = [
        "invoice", "invoice_date", "customer_id", "stock_code",
        "description", "quantity", "unit_price", "line_revenue",
        "country", "is_cancellation_invoice", "is_return",
        "is_negative_price", "is_zero_price", "has_customer_id",
    ]
    df = df[ordered_columns]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Compressed CSV keeps the large processed dataset manageable.
    df.to_csv(OUTPUT_FILE, index=False, compression="gzip")

    summary = [
        "RETAILPULSE - DATA CLEANING SUMMARY",
        "=" * 45,
        f"Source file: {DATA_FILE.name}",
        f"Original rows: {original_rows:,}",
        f"Exact duplicate rows removed: {duplicate_count:,}",
        f"Rows after duplicate removal: {len(df):,}",
        f"Rows with missing customer IDs: {df['customer_id'].isna().sum():,}",
        f"Missing descriptions filled as Unknown: {missing_descriptions:,}",
        f"Invalid dates after conversion: {df['invoice_date'].isna().sum():,}",
        f"Missing quantities after conversion: {df['quantity'].isna().sum():,}",
        f"Missing unit prices after conversion: {df['unit_price'].isna().sum():,}",
        f"Cancellation invoice rows flagged: {df['is_cancellation_invoice'].sum():,}",
        f"Negative quantity rows flagged: {df['is_return'].sum():,}",
        f"Negative price rows flagged: {df['is_negative_price'].sum():,}",
        f"Zero price rows flagged: {df['is_zero_price'].sum():,}",
        f"Rows with missing customer IDs retained: {(~df['has_customer_id']).sum():,}",
        f"Total signed line revenue: {df['line_revenue'].sum():,.2f}",
        f"Processed columns: {len(df.columns)}",
        "",
        "Output file:",
        str(OUTPUT_FILE),
        "",
        "POLICY",
        "-" * 45,
        "Only exact duplicate rows were removed.",
        "Returns, cancellation invoices, and unusual prices were retained and flagged.",
        "Revenue is quantity multiplied by unit price; it is not yet a finalized sales KPI.",
        "Missing customer IDs remain in the dataset for aggregate analysis.",
    ]

    REPORT_FILE.write_text("\n".join(summary), encoding="utf-8")
    print("\n".join(summary))
    print(f"\nSummary saved to: {REPORT_FILE}")


if __name__ == "__main__":
    main()

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
SOURCE_FILE_GZ = DATA_DIR / "Online_Retail_II_with_5_RetailPulse_Columns.csv.gz"
SOURCE_FILE_CSV = DATA_DIR / "Online_Retail_II_with_5_RetailPulse_Columns.csv"
OUTPUT_FILE = DATA_DIR / "retail_transactions_cleaned.csv.gz"
REPORT_FILE = PROJECT_ROOT / "reports" / "cleaning_summary.txt"

SOURCE_COLUMNS = [
    "Invoice", "StockCode", "Description", "Quantity",
    "InvoiceDate", "Price", "Customer ID", "Country",
]
ENGINEERED_COLUMNS = [
    "TotalPrice", "InvoiceYear", "InvoiceMonth", "DayOfWeek", "TransactionType",
]


def main():
    source_file = SOURCE_FILE_GZ if SOURCE_FILE_GZ.exists() else SOURCE_FILE_CSV
    if not source_file.exists():
        raise FileNotFoundError(
            "Enhanced source dataset not found. Expected one of these files:\n"
            f"  {SOURCE_FILE_GZ}\n  {SOURCE_FILE_CSV}\n"
            "Check the filename and extension in the data folder."
        )

    print(f"Loading enhanced source dataset: {source_file.name}")
    df = pd.read_csv(source_file, compression="infer", low_memory=False)

    missing = [column for column in SOURCE_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Source dataset is missing original columns: {missing}")

    original_rows = len(df)

    # Keep original field names available while checking the new engineered columns.
    missing_engineered = [column for column in ENGINEERED_COLUMNS if column not in df.columns]
    if missing_engineered:
        print(f"Some engineered columns are missing and will be regenerated: {missing_engineered}")

    # Remove exact duplicate source transaction rows only.
    duplicate_count = int(df.duplicated(subset=SOURCE_COLUMNS).sum())
    df = df.drop_duplicates(subset=SOURCE_COLUMNS).copy()

    # Normalize source column names to match the existing RetailPulse pipeline.
    df = df.rename(columns={
        "Invoice": "invoice",
        "StockCode": "stock_code",
        "Description": "description",
        "Quantity": "quantity",
        "InvoiceDate": "invoice_date",
        "Price": "unit_price",
        "Customer ID": "customer_id",
        "Country": "country",
        "TotalPrice": "total_price",
        "InvoiceYear": "invoice_year",
        "InvoiceMonth": "invoice_month",
        "DayOfWeek": "day_of_week",
        "TransactionType": "transaction_type",
    })

    # Standardize text columns and parse numerical/date fields.
    for column in ["invoice", "stock_code", "description", "country"]:
        df[column] = df[column].astype("string").str.strip()

    df["invoice_date"] = pd.to_datetime(
    df["invoice_date"], format="mixed", errors="coerce"
)
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["customer_id"] = pd.to_numeric(df["customer_id"], errors="coerce").astype("Int64")

    # Fill blank product descriptions while preserving product codes.
    df["description"] = df["description"].replace("", pd.NA)
    missing_descriptions = int(df["description"].isna().sum())
    df["description"] = df["description"].fillna("Unknown")

    # Recalculate engineered columns from parsed source fields to ensure consistent types.
    df["total_price"] = df["quantity"] * df["unit_price"]
    df["invoice_year"] = df["invoice_date"].dt.year.astype("Int64")
    df["invoice_month"] = df["invoice_date"].dt.month.astype("Int64")
    df["day_of_week"] = df["invoice_date"].dt.day_name().astype("string")

    cancellation = df["invoice"].str.startswith("C", na=False)
    returned = df["quantity"] < 0
    zero_price = df["unit_price"] == 0
    negative_price = df["unit_price"] < 0

    # Explicit, mutually exclusive transaction classification.
    df["transaction_type"] = "Sale"
    df.loc[zero_price | negative_price, "transaction_type"] = "Zero/No-charge or invalid price"
    df.loc[returned, "transaction_type"] = "Return"
    df.loc[cancellation, "transaction_type"] = "Cancellation"

    # Preserve the original project's fields so downstream scripts remain compatible.
    df["is_cancellation_invoice"] = cancellation
    df["is_return"] = returned
    df["is_negative_price"] = negative_price
    df["is_zero_price"] = zero_price
    df["has_customer_id"] = df["customer_id"].notna()
    df["line_revenue"] = df["total_price"]

    ordered_columns = [
        "invoice", "invoice_date", "customer_id", "stock_code", "description",
        "quantity", "unit_price", "line_revenue", "country",
        "total_price", "invoice_year", "invoice_month", "day_of_week",
        "transaction_type", "is_cancellation_invoice", "is_return",
        "is_negative_price", "is_zero_price", "has_customer_id",
    ]
    df = df[ordered_columns]

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Write to a temporary file first so an interrupted run does not overwrite
    # the last good cleaned dataset.
    temp_output = OUTPUT_FILE.with_suffix(OUTPUT_FILE.suffix + ".tmp")
    df.to_csv(temp_output, index=False, compression="gzip")
    temp_output.replace(OUTPUT_FILE)

    summary = [
        "RETAILPULSE - DATA CLEANING SUMMARY",
        "=" * 45,
        f"Source file: {source_file.name}",
        f"Original rows: {original_rows:,}",
        f"Exact duplicate rows removed: {duplicate_count:,}",
        f"Rows after duplicate removal: {len(df):,}",
        f"Rows with missing customer IDs: {df['customer_id'].isna().sum():,}",
        f"Missing descriptions filled as Unknown: {missing_descriptions:,}",
        f"Invalid dates after conversion: {df['invoice_date'].isna().sum():,}",
        f"Missing quantities after conversion: {df['quantity'].isna().sum():,}",
        f"Missing unit prices after conversion: {df['unit_price'].isna().sum():,}",
        f"Cancellation invoice rows flagged: {int(cancellation.sum()):,}",
        f"Negative quantity rows flagged: {int(returned.sum()):,}",
        f"Negative price rows flagged: {int(negative_price.sum()):,}",
        f"Zero price rows flagged: {int(zero_price.sum()):,}",
        f"Processed columns: {len(df.columns)}",
        "Engineered columns retained: total_price, invoice_year, invoice_month, day_of_week, transaction_type",
        f"Total signed line revenue: {df['line_revenue'].sum():,.2f}",
        "",
        "Output file:",
        str(OUTPUT_FILE),
        "",
        "POLICY",
        "-" * 45,
        "Only exact duplicate source transaction rows were removed.",
        "Returns, cancellations, and unusual prices were retained and flagged.",
        "Total price is quantity multiplied by unit price; it is not profit.",
        "The original Excel workbook is not modified.",
    ]
    REPORT_FILE.write_text("\n".join(summary), encoding="utf-8")
    print("\n".join(summary))
    print(f"\nCleaned dataset saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = PROJECT_ROOT / "data" / "raw" / "online_retail_II.xlsx"
REPORT_FILE = PROJECT_ROOT / "reports" / "dataset_profile.txt"

SHEETS = ["Year 2009-2010", "Year 2010-2011"]


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

    frames = []

    for sheet in SHEETS:
        print(f"Loading worksheet: {sheet}")
        frame = pd.read_excel(DATA_FILE, sheet_name=sheet)
        frame["SourceSheet"] = sheet
        frames.append(frame)

    df = pd.concat(frames, ignore_index=True)

    required_columns = [
        "Invoice", "StockCode", "Description", "Quantity",
        "InvoiceDate", "Price", "Customer ID", "Country"
    ]

    missing_columns = [
        column for column in required_columns if column not in df.columns
    ]
    if missing_columns:
        raise ValueError(f"Unexpected dataset columns: {missing_columns}")

    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")

    lines = [
        "RETAILPULSE - RAW DATASET PROFILE",
        "=" * 45,
        f"Source file: {DATA_FILE.name}",
        f"Worksheets: {', '.join(SHEETS)}",
        f"Total rows: {len(df):,}",
        f"Total columns including source sheet: {len(df.columns):,}",
        "",
        "ROWS PER WORKSHEET",
        "-" * 45,
        df["SourceSheet"].value_counts().to_string(),
        "",
        "COLUMN DATA TYPES",
        "-" * 45,
        df.dtypes.to_string(),
        "",
        "MISSING VALUES",
        "-" * 45,
        df.isna().sum().to_string(),
        "",
        f"Exact duplicate rows: {df.duplicated(subset=required_columns).sum():,}",
        f"Unique invoices: {df['Invoice'].nunique(dropna=True):,}",
        f"Unique products: {df['StockCode'].nunique(dropna=True):,}",
        f"Unique customers: {df['Customer ID'].nunique(dropna=True):,}",
        f"Unique countries: {df['Country'].nunique(dropna=True):,}",
        f"Rows with negative quantity: {(df['Quantity'] < 0).sum():,}",
        f"Rows with zero quantity: {(df['Quantity'] == 0).sum():,}",
        f"Rows with negative price: {(df['Price'] < 0).sum():,}",
        f"Rows with zero price: {(df['Price'] == 0).sum():,}",
        f"Invoices starting with C: {df['Invoice'].astype('string').str.startswith('C', na=False).sum():,}",
        f"Invalid invoice dates: {df['InvoiceDate'].isna().sum():,}",
        "",
        "DATE RANGE",
        "-" * 45,
        f"First transaction: {df['InvoiceDate'].min()}",
        f"Last transaction: {df['InvoiceDate'].max()}",
        "",
        "TOP 10 COUNTRIES BY ROW COUNT",
        "-" * 45,
        df["Country"].value_counts().head(10).to_string(),
        "",
        "NOTE",
        "-" * 45,
        "This report profiles raw data only. No rows have been removed or modified.",
    ]

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")

    print("\n".join(lines))
    print(f"\nProfile report saved to: {REPORT_FILE}")


if __name__ == "__main__":
    main()

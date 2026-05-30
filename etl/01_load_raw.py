"""
etl/01_load_raw.py

Purpose:
- Load all raw Olist CSV files with pandas
- Confirm that Python can find and read each file
- Print row counts, column names, missing values, and duplicate key checks

This script does NOT clean or load data into PostgreSQL yet.
It is the first validation step in the ETL workflow.
"""

from pathlib import Path
import pandas as pd


# Find the project root automatically
# __file__ = etl/01_load_raw.py
# parents[1] = main project folder
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"


# All expected raw CSV files
FILES = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "product_category_translation": "product_category_name_translation.csv",
}


# Expected primary keys or key combinations
PRIMARY_KEYS = {
    "customers": ["customer_id"],
    "orders": ["order_id"],
    "order_items": ["order_id", "order_item_id"],
    "order_payments": ["order_id", "payment_sequential"],
    "order_reviews": ["review_id"],
    "products": ["product_id"],
    "sellers": ["seller_id"],
    "product_category_translation": ["product_category_name"],
}


def load_csv(table_name: str, filename: str) -> pd.DataFrame:
    """Load one CSV file and return a pandas DataFrame."""
    file_path = RAW_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Missing file: {file_path}")

    df = pd.read_csv(file_path)

    print("\n" + "=" * 80)
    print(f"Table: {table_name}")
    print(f"File: {filename}")
    print(f"Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")

    return df


def summarize_columns(df: pd.DataFrame) -> None:
    """Print column names and data types."""
    print("\nColumns and data types:")
    print(df.dtypes)


def summarize_missing_values(df: pd.DataFrame) -> None:
    """Print columns that contain missing values."""
    missing = df.isna().sum()
    missing = missing[missing > 0].sort_values(ascending=False)

    if missing.empty:
        print("\nMissing values: None")
    else:
        print("\nMissing values:")
        print(missing)


def check_duplicate_keys(df: pd.DataFrame, table_name: str) -> None:
    """Check duplicate primary keys if key information is available."""
    if table_name not in PRIMARY_KEYS:
        print("\nPrimary key check: skipped")
        return

    key_cols = PRIMARY_KEYS[table_name]

    missing_key_cols = [col for col in key_cols if col not in df.columns]
    if missing_key_cols:
        print(f"\nWARNING: Missing expected key columns: {missing_key_cols}")
        return

    duplicate_count = df.duplicated(subset=key_cols).sum()

    print(f"\nPrimary key check: {key_cols}")
    print(f"Duplicate key rows: {duplicate_count:,}")


def main() -> None:
    """Run raw data validation for all CSV files."""
    print("Starting raw data validation...")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Raw data folder: {RAW_DIR}")

    loaded_tables = {}

    for table_name, filename in FILES.items():
        df = load_csv(table_name, filename)
        summarize_columns(df)
        summarize_missing_values(df)
        check_duplicate_keys(df, table_name)

        loaded_tables[table_name] = df

    print("\n" + "=" * 80)
    print("Raw data validation complete.")
    print(f"Successfully loaded {len(loaded_tables)} CSV files.")


if __name__ == "__main__":
    main()
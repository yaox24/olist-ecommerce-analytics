"""
etl/02_clean_orders.py

Purpose:
- Clean the raw orders table
- Parse timestamp columns
- Standardize order status
- Keep missing delivery dates because canceled/unavailable orders may not be delivered
- Validate order_id
- Save cleaned data to data/processed/orders_clean.csv
"""

from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

INPUT_FILE = RAW_DIR / "olist_orders_dataset.csv"
OUTPUT_FILE = PROCESSED_DIR / "orders_clean.csv"

TIMESTAMP_COLUMNS = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the orders dataset."""

    df = df.copy()

    # Standardize status text
    df["order_status"] = df["order_status"].str.strip().str.lower()

    # Convert timestamp columns from string to datetime
    for col in TIMESTAMP_COLUMNS:
        df[col] = pd.to_datetime(df[col], errors="coerce")
        missing_count = df[col].isna().sum()
        print(f"Missing values after datetime parsing - {col}: {missing_count:,}")

    # Remove duplicate order_id rows if any
    before = len(df)
    df = df.drop_duplicates(subset=["order_id"])
    after = len(df)

    print(f"Rows before duplicate removal: {before:,}")
    print(f"Rows after duplicate removal: {after:,}")
    print(f"Duplicate rows removed: {before - after:,}")

    null_order_ids = df["order_id"].isna().sum()
    duplicate_order_ids = df["order_id"].duplicated().sum()

    if null_order_ids > 0:
        raise ValueError(f"order_id has {null_order_ids} missing values.")

    if duplicate_order_ids > 0:
        raise ValueError(f"order_id has {duplicate_order_ids} duplicate values.")

    print("order_id validation passed.")

    # Check for impossible delivery dates
    bad_delivery_dates = (
        df["order_delivered_customer_date"].notna()
        & (df["order_delivered_customer_date"] < df["order_purchase_timestamp"])
    )

    bad_count = bad_delivery_dates.sum()

    if bad_count > 0:
        print(f"Found {bad_count:,} impossible delivery dates. Setting them to missing.")
        df.loc[bad_delivery_dates, "order_delivered_customer_date"] = pd.NaT
    else:
        print("No impossible delivery dates found.")

    print("\nOrder status distribution:")
    print(df["order_status"].value_counts())

    return df


def main() -> None:
    """Load, clean, and save orders data."""

    print("Cleaning orders data...")
    print(f"Input file: {INPUT_FILE}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    df_raw = pd.read_csv(INPUT_FILE)
    print(f"Raw shape: {df_raw.shape[0]:,} rows × {df_raw.shape[1]} columns")

    df_clean = clean_orders(df_raw)
    print(f"Clean shape: {df_clean.shape[0]:,} rows × {df_clean.shape[1]} columns")

    df_clean.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved cleaned file to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
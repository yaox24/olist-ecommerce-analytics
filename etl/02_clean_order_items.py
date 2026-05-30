"""
etl/02_clean_order_items.py

Purpose:
- Clean the raw order items table
- Parse shipping_limit_date
- Validate composite key: order_id + order_item_id
- Validate price and freight_value
- Save cleaned data to data/processed/order_items_clean.csv
"""

from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

INPUT_FILE = RAW_DIR / "olist_order_items_dataset.csv"
OUTPUT_FILE = PROCESSED_DIR / "order_items_clean.csv"


def clean_order_items(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the order items dataset."""

    df = df.copy()

    df["shipping_limit_date"] = pd.to_datetime(df["shipping_limit_date"], errors="coerce")

    before = len(df)
    df = df.drop_duplicates(subset=["order_id", "order_item_id"])
    after = len(df)

    print(f"Rows before duplicate removal: {before:,}")
    print(f"Rows after duplicate removal: {after:,}")
    print(f"Duplicate rows removed: {before - after:,}")

    duplicate_keys = df.duplicated(subset=["order_id", "order_item_id"]).sum()
    null_order_ids = df["order_id"].isna().sum()
    null_order_item_ids = df["order_item_id"].isna().sum()

    if duplicate_keys > 0:
        raise ValueError(f"order_id + order_item_id has {duplicate_keys} duplicate values.")

    if null_order_ids > 0:
        raise ValueError(f"order_id has {null_order_ids} missing values.")

    if null_order_item_ids > 0:
        raise ValueError(f"order_item_id has {null_order_item_ids} missing values.")

    print("Composite key validation passed: order_id + order_item_id")

    negative_prices = (df["price"] < 0).sum()
    negative_freight = (df["freight_value"] < 0).sum()

    if negative_prices > 0:
        raise ValueError(f"Found {negative_prices} negative prices.")

    if negative_freight > 0:
        raise ValueError(f"Found {negative_freight} negative freight values.")

    print("Price and freight validation passed.")

    # Useful derived column for later analysis
    df["total_item_value"] = df["price"] + df["freight_value"]

    return df


def main() -> None:
    """Load, clean, and save order items data."""

    print("Cleaning order items data...")
    print(f"Input file: {INPUT_FILE}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    df_raw = pd.read_csv(INPUT_FILE)
    print(f"Raw shape: {df_raw.shape[0]:,} rows × {df_raw.shape[1]} columns")

    df_clean = clean_order_items(df_raw)
    print(f"Clean shape: {df_clean.shape[0]:,} rows × {df_clean.shape[1]} columns")

    df_clean.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved cleaned file to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
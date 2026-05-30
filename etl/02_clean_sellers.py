"""
etl/02_clean_sellers.py

Purpose:
- Clean the raw sellers table
- Standardize city/state text
- Validate seller_id
- Save cleaned data to data/processed/sellers_clean.csv
"""

from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

INPUT_FILE = RAW_DIR / "olist_sellers_dataset.csv"
OUTPUT_FILE = PROCESSED_DIR / "sellers_clean.csv"


def clean_sellers(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the sellers dataset."""

    df = df.copy()

    df["seller_city"] = df["seller_city"].str.strip().str.lower()
    df["seller_state"] = df["seller_state"].str.strip().str.upper()

    before = len(df)
    df = df.drop_duplicates(subset=["seller_id"])
    after = len(df)

    print(f"Rows before duplicate removal: {before:,}")
    print(f"Rows after duplicate removal: {after:,}")
    print(f"Duplicate rows removed: {before - after:,}")

    null_seller_ids = df["seller_id"].isna().sum()
    duplicate_seller_ids = df["seller_id"].duplicated().sum()

    if null_seller_ids > 0:
        raise ValueError(f"seller_id has {null_seller_ids} missing values.")

    if duplicate_seller_ids > 0:
        raise ValueError(f"seller_id has {duplicate_seller_ids} duplicate values.")

    print("seller_id validation passed.")

    return df


def main() -> None:
    """Load, clean, and save sellers data."""

    print("Cleaning sellers data...")
    print(f"Input file: {INPUT_FILE}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    df_raw = pd.read_csv(INPUT_FILE)
    print(f"Raw shape: {df_raw.shape[0]:,} rows × {df_raw.shape[1]} columns")

    df_clean = clean_sellers(df_raw)
    print(f"Clean shape: {df_clean.shape[0]:,} rows × {df_clean.shape[1]} columns")

    df_clean.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved cleaned file to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
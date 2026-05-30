"""
etl/02_clean_products.py

Purpose:
- Clean the raw products table
- Standardize product category names
- Keep missing product attributes instead of deleting rows
- Validate product_id
- Save cleaned data to data/processed/products_clean.csv
"""

from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

INPUT_FILE = RAW_DIR / "olist_products_dataset.csv"
OUTPUT_FILE = PROCESSED_DIR / "products_clean.csv"


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the products dataset."""

    df = df.copy()

    # Standardize category names
    df["product_category_name"] = (
        df["product_category_name"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    # Replace missing category with Unknown for easier analysis later
    df["product_category_name"] = df["product_category_name"].fillna("unknown")

    before = len(df)
    df = df.drop_duplicates(subset=["product_id"])
    after = len(df)

    print(f"Rows before duplicate removal: {before:,}")
    print(f"Rows after duplicate removal: {after:,}")
    print(f"Duplicate rows removed: {before - after:,}")

    null_product_ids = df["product_id"].isna().sum()
    duplicate_product_ids = df["product_id"].duplicated().sum()

    if null_product_ids > 0:
        raise ValueError(f"product_id has {null_product_ids} missing values.")

    if duplicate_product_ids > 0:
        raise ValueError(f"product_id has {duplicate_product_ids} duplicate values.")

    print("product_id validation passed.")

    missing_after_cleaning = df.isna().sum()
    missing_after_cleaning = missing_after_cleaning[missing_after_cleaning > 0]

    if not missing_after_cleaning.empty:
        print("\nRemaining missing values kept intentionally:")
        print(missing_after_cleaning)

    return df


def main() -> None:
    """Load, clean, and save products data."""

    print("Cleaning products data...")
    print(f"Input file: {INPUT_FILE}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    df_raw = pd.read_csv(INPUT_FILE)
    print(f"Raw shape: {df_raw.shape[0]:,} rows × {df_raw.shape[1]} columns")

    df_clean = clean_products(df_raw)
    print(f"Clean shape: {df_clean.shape[0]:,} rows × {df_clean.shape[1]} columns")

    df_clean.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved cleaned file to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
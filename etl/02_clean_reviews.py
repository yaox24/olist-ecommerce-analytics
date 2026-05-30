"""
etl/02_clean_reviews.py

Purpose:
- Clean the raw order reviews table
- Parse review timestamps
- Validate review scores
- Handle duplicate review_id values carefully
- Save cleaned data to data/processed/order_reviews_clean.csv
"""

from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

INPUT_FILE = RAW_DIR / "olist_order_reviews_dataset.csv"
OUTPUT_FILE = PROCESSED_DIR / "order_reviews_clean.csv"


def clean_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the order reviews dataset."""

    df = df.copy()

    df["review_creation_date"] = pd.to_datetime(df["review_creation_date"], errors="coerce")
    df["review_answer_timestamp"] = pd.to_datetime(df["review_answer_timestamp"], errors="coerce")

    # Missing comments are normal. Keep them.
    df["review_comment_title"] = df["review_comment_title"].fillna("")
    df["review_comment_message"] = df["review_comment_message"].fillna("")

    invalid_scores = ~df["review_score"].between(1, 5)

    invalid_score_count = invalid_scores.sum()
    if invalid_score_count > 0:
        raise ValueError(f"Found {invalid_score_count} review scores outside 1-5.")

    print("Review score validation passed.")

    # The raw dataset has duplicate review_id values.
    # We only remove exact duplicate rows, not all duplicate review_id rows.
    before = len(df)
    df = df.drop_duplicates()
    after = len(df)

    print(f"Rows before exact duplicate removal: {before:,}")
    print(f"Rows after exact duplicate removal: {after:,}")
    print(f"Exact duplicate rows removed: {before - after:,}")

    duplicate_review_ids = df["review_id"].duplicated().sum()
    print(f"Remaining duplicate review_id rows: {duplicate_review_ids:,}")
    print("Note: review_id is not used as a primary key in our schema.")

    null_order_ids = df["order_id"].isna().sum()
    if null_order_ids > 0:
        raise ValueError(f"order_id has {null_order_ids} missing values.")

    print("order_id validation passed.")

    return df


def main() -> None:
    """Load, clean, and save review data."""

    print("Cleaning order reviews data...")
    print(f"Input file: {INPUT_FILE}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    df_raw = pd.read_csv(INPUT_FILE)
    print(f"Raw shape: {df_raw.shape[0]:,} rows × {df_raw.shape[1]} columns")

    df_clean = clean_reviews(df_raw)
    print(f"Clean shape: {df_clean.shape[0]:,} rows × {df_clean.shape[1]} columns")

    df_clean.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved cleaned file to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
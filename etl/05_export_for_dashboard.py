"""
etl/05_export_for_dashboard.py

Exports analysis-ready CSV files for Power BI dashboard building.

This script connects to the PostgreSQL database, pulls cleaned/joined
business tables, and saves dashboard-ready CSV files into outputs/exports/.

Exports created:
1. orders_fact.csv
2. monthly_revenue.csv
3. revenue_by_state.csv
4. revenue_by_category.csv
5. delivery_review_summary.csv

Note:
RFM exports are already created in analysis/04_rfm_segmentation.ipynb:
- rfm_segments.csv
- rfm_segment_summary.csv
"""

from pathlib import Path
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL


# ============================================================
# 1. Project paths and database connection
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
EXPORTS_DIR = PROJECT_ROOT / "outputs" / "exports"

EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(ENV_PATH, override=True)

db_url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    database=os.getenv("DB_NAME"),
)

engine = create_engine(db_url)

print("Connected successfully")
print(f"Export directory: {EXPORTS_DIR}")


# ============================================================
# Helper function
# ============================================================

def export_query(query: str, filename: str) -> pd.DataFrame:
    """
    Run a SQL query, export the result to CSV, and return the DataFrame.
    """
    print(f"\nExporting {filename}...")

    df = pd.read_sql(query, engine)

    output_path = EXPORTS_DIR / filename
    df.to_csv(output_path, index=False)

    print(f"Saved {filename}: {len(df):,} rows")
    return df


# ============================================================
# 2. Export orders_fact.csv
# ============================================================
# Grain: one row per order item
#
# This is the main fact table for Power BI.
# It joins order, customer, product, seller, and review data.
# Each row represents one product item inside a delivered order.
# ============================================================

orders_fact_query = """
SELECT
    o.order_id,
    o.order_purchase_timestamp,
    DATE_TRUNC('month', o.order_purchase_timestamp) AS order_month,
    o.order_status,

    c.customer_id,
    c.customer_unique_id,
    c.customer_city,
    c.customer_state,

    oi.order_item_id,
    oi.product_id,
    oi.seller_id,
    oi.price,
    oi.freight_value,
    oi.price + oi.freight_value AS total_value,

    COALESCE(
        t.product_category_name_english,
        p.product_category_name,
        'unknown'
    ) AS category_name_english,

    s.seller_city,
    s.seller_state,

    r.review_score,

    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,

    EXTRACT(
        DAY FROM o.order_delivered_customer_date - o.order_purchase_timestamp
    ) AS delivery_days,

    EXTRACT(
        DAY FROM o.order_delivered_customer_date - o.order_estimated_delivery_date
    ) AS delivery_delay_days,

    CASE
        WHEN o.order_delivered_customer_date IS NULL
            OR o.order_estimated_delivery_date IS NULL
            THEN 'Unknown'
        WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date
            THEN 'On Time'
        ELSE 'Late'
    END AS delivery_status

FROM orders o
JOIN customers c
    ON o.customer_id = c.customer_id
JOIN order_items oi
    ON o.order_id = oi.order_id
LEFT JOIN products p
    ON oi.product_id = p.product_id
LEFT JOIN product_category_translation t
    ON p.product_category_name = t.product_category_name
LEFT JOIN sellers s
    ON oi.seller_id = s.seller_id
LEFT JOIN order_reviews r
    ON o.order_id = r.order_id

WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp < '2018-09-01'

ORDER BY o.order_purchase_timestamp;
"""

orders_fact = export_query(orders_fact_query, "orders_fact.csv")


# ============================================================
# 3. Export monthly_revenue.csv
# ============================================================
# Grain: one row per month
#
# Used for revenue trend visuals and KPI growth calculations.
# ============================================================

monthly_revenue_query = """
SELECT
    DATE_TRUNC('month', o.order_purchase_timestamp) AS order_month,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT c.customer_unique_id) AS total_customers,
    ROUND(SUM(oi.price + oi.freight_value)::NUMERIC, 2) AS total_revenue,
    ROUND(AVG(oi.price + oi.freight_value)::NUMERIC, 2) AS avg_item_value
FROM orders o
JOIN customers c
    ON o.customer_id = c.customer_id
JOIN order_items oi
    ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp < '2018-09-01'
GROUP BY 1
ORDER BY 1;
"""

monthly_revenue = export_query(monthly_revenue_query, "monthly_revenue.csv")


# ============================================================
# 4. Export revenue_by_state.csv
# ============================================================
# Grain: one row per customer state
#
# Used for geographic sales visuals.
# ============================================================

revenue_by_state_query = """
SELECT
    c.customer_state,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT c.customer_unique_id) AS total_customers,
    ROUND(SUM(oi.price + oi.freight_value)::NUMERIC, 2) AS total_revenue,
    ROUND(AVG(oi.price + oi.freight_value)::NUMERIC, 2) AS avg_item_value
FROM orders o
JOIN customers c
    ON o.customer_id = c.customer_id
JOIN order_items oi
    ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp < '2018-09-01'
GROUP BY c.customer_state
ORDER BY total_revenue DESC;
"""

revenue_by_state = export_query(revenue_by_state_query, "revenue_by_state.csv")


# ============================================================
# 5. Export revenue_by_category.csv
# ============================================================
# Grain: one row per product category
#
# Used for top category revenue visuals.
# ============================================================

revenue_by_category_query = """
SELECT
    COALESCE(
        t.product_category_name_english,
        p.product_category_name,
        'unknown'
    ) AS category_name_english,

    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT oi.product_id) AS total_products,
    ROUND(SUM(oi.price + oi.freight_value)::NUMERIC, 2) AS total_revenue,
    ROUND(AVG(oi.price + oi.freight_value)::NUMERIC, 2) AS avg_item_value,
    ROUND(AVG(r.review_score)::NUMERIC, 2) AS avg_review_score

FROM orders o
JOIN order_items oi
    ON o.order_id = oi.order_id
LEFT JOIN products p
    ON oi.product_id = p.product_id
LEFT JOIN product_category_translation t
    ON p.product_category_name = t.product_category_name
LEFT JOIN order_reviews r
    ON o.order_id = r.order_id

WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp < '2018-09-01'

GROUP BY 1
ORDER BY total_revenue DESC;
"""

revenue_by_category = export_query(
    revenue_by_category_query,
    "revenue_by_category.csv"
)


# ============================================================
# 6. Export delivery_review_summary.csv
# ============================================================
# Grain: one row per delivery status
#
# Used to show the relationship between delivery performance
# and customer review score.
# ============================================================

delivery_review_summary_query = """
SELECT
    CASE
        WHEN o.order_delivered_customer_date IS NULL
            OR o.order_estimated_delivery_date IS NULL
            THEN 'Unknown'
        WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date
            THEN 'On Time'
        ELSE 'Late'
    END AS delivery_status,

    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(AVG(r.review_score)::NUMERIC, 2) AS avg_review_score,
    ROUND(
        AVG(
            EXTRACT(
                DAY FROM o.order_delivered_customer_date - o.order_purchase_timestamp
            )
        )::NUMERIC,
        2
    ) AS avg_delivery_days,

    ROUND(
        SUM(oi.price + oi.freight_value)::NUMERIC,
        2
    ) AS total_revenue

FROM orders o
JOIN order_items oi
    ON o.order_id = oi.order_id
LEFT JOIN order_reviews r
    ON o.order_id = r.order_id

WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp < '2018-09-01'

GROUP BY 1
ORDER BY total_orders DESC;
"""

delivery_review_summary = export_query(
    delivery_review_summary_query,
    "delivery_review_summary.csv"
)


# ============================================================
# 7. Export KPI summary
# ============================================================
# Grain: one row
#
# Useful for quick validation and dashboard KPI cards.
# ============================================================

kpi_summary_query = """
WITH customer_orders AS (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS total_orders
    FROM customers c
    JOIN orders o
        ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp >= '2017-01-01'
      AND o.order_purchase_timestamp < '2018-09-01'
    GROUP BY c.customer_unique_id
),

delivery AS (
    SELECT
        o.order_id,
        CASE
            WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date
                THEN 1
            ELSE 0
        END AS is_on_time
    FROM orders o
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
      AND o.order_estimated_delivery_date IS NOT NULL
      AND o.order_purchase_timestamp >= '2017-01-01'
      AND o.order_purchase_timestamp < '2018-09-01'
)

SELECT
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT c.customer_unique_id) AS total_customers,
    ROUND(SUM(oi.price + oi.freight_value)::NUMERIC, 2) AS total_revenue,
    ROUND(
        SUM(oi.price + oi.freight_value)::NUMERIC
        / NULLIF(COUNT(DISTINCT o.order_id), 0),
        2
    ) AS average_order_value,

    ROUND(AVG(r.review_score)::NUMERIC, 2) AS avg_review_score,

    ROUND(
        (
            SELECT SUM(is_on_time) * 100.0 / COUNT(*)
            FROM delivery
        )::NUMERIC,
        2
    ) AS on_time_delivery_rate_pct,

    ROUND(
        (
            SELECT
                SUM(CASE WHEN total_orders >= 2 THEN 1 ELSE 0 END) * 100.0
                / COUNT(*)
            FROM customer_orders
        )::NUMERIC,
        2
    ) AS repeat_purchase_rate_pct

FROM orders o
JOIN customers c
    ON o.customer_id = c.customer_id
JOIN order_items oi
    ON o.order_id = oi.order_id
LEFT JOIN order_reviews r
    ON o.order_id = r.order_id

WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp < '2018-09-01';
"""

kpi_summary = export_query(kpi_summary_query, "kpi_summary.csv")


# ============================================================
# 8. Final validation summary
# ============================================================

print("\nDashboard export complete.")
print("=" * 50)

print(f"orders_fact rows: {len(orders_fact):,}")
print(f"monthly_revenue rows: {len(monthly_revenue):,}")
print(f"revenue_by_state rows: {len(revenue_by_state):,}")
print(f"revenue_by_category rows: {len(revenue_by_category):,}")
print(f"delivery_review_summary rows: {len(delivery_review_summary):,}")
print(f"kpi_summary rows: {len(kpi_summary):,}")

print("\nFiles saved to:")
print(EXPORTS_DIR)

print("\nNext step:")
print("Open Power BI and import the CSV files from outputs/exports/.")
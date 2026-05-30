import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DB_URL = (
    f"postgresql+psycopg2://"
    f"{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:"
    f"{os.getenv('DB_PORT')}/"
    f"{os.getenv('DB_NAME')}"
)

engine = create_engine(DB_URL)

PROCESSED_DIR = "data/processed"
RAW_DIR = "data/raw"

#create herlper function
def load_table(df, table_name):
    print(f"Loading {table_name} ({len(df):,} rows)...")

    df.to_sql(
        table_name,
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=5000
    )

    print(f"Finished {table_name}")


#load costumers
customers = pd.read_csv(
    f"{PROCESSED_DIR}/customers_clean.csv"
)

load_table(customers, "customers")

#load sellers
sellers = pd.read_csv(
    f"{PROCESSED_DIR}/sellers_clean.csv"
)

load_table(sellers, "sellers")

#load sellers
products = pd.read_csv(
    f"{PROCESSED_DIR}/products_clean.csv"
)

load_table(products, "products")

#Load Product Category Translation
translation = pd.read_csv(
    f"{RAW_DIR}/product_category_name_translation.csv"
)

translation["product_category_name"] = (
    translation["product_category_name"]
    .str.strip()
    .str.lower()
)

load_table(
    translation,
    "product_category_translation"
)

#Load Geolocation, Standardize city names before loading
geo = pd.read_csv(
    f"{RAW_DIR}/olist_geolocation_dataset.csv"
)

geo["geolocation_city"] = (
    geo["geolocation_city"]
    .str.strip()
    .str.lower()
)

geo["geolocation_state"] = (
    geo["geolocation_state"]
    .str.upper()
)

load_table(
    geo,
    "geolocation"
)

#load orders

orders = pd.read_csv(               #Datetime parsing
    f"{PROCESSED_DIR}/orders_clean.csv"
)

date_cols = [                       #Datetime columns
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date"
]

for col in date_cols:
    orders[col] = pd.to_datetime(
        orders[col],
        errors="coerce"
    )

load_table(                         #Load
    orders,
    "orders"
)

#Load Order Items
items = pd.read_csv(
    f"{PROCESSED_DIR}/order_items_clean.csv"
)

items["shipping_limit_date"] = pd.to_datetime(
    items["shipping_limit_date"],
    errors="coerce"
)
if "total_item_value" in items.columns:
    items = items.drop(
        columns=["total_item_value"]
    )

load_table(
    items,
    "order_items"
)

#Load Order Payments, no cleaning, load directly
payments = pd.read_csv(
    f"{RAW_DIR}/olist_order_payments_dataset.csv"
)

load_table(
    payments,
    "order_payments"
)
reviews = pd.read_csv(
    f"{PROCESSED_DIR}/order_reviews_clean.csv"
)
reviews["review_creation_date"] = pd.to_datetime(       #Date columns
    reviews["review_creation_date"],
    errors="coerce"
)

reviews["review_answer_timestamp"] = pd.to_datetime(
    reviews["review_answer_timestamp"],
    errors="coerce"
)

load_table(
    reviews,
    "order_reviews"
)



print("All tables loaded successfully.")
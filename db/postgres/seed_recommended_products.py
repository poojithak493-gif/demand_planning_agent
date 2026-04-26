"""
db/postgres/seed_recommended_products.py
Fixed SonarQube Issues:
1. Reduced Cognitive Complexity
2. Removed unnecessary f-strings
"""

import os
import sys
import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv()

EXCEL_FILE = "sample_data/30_Recommended_New_Products.xlsx"
SHEET_NAME = "3. Recommendation Mapping"


# ── DB Connection ──────────────────────────────────────────────
def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5433)),
        dbname=os.getenv("POSTGRES_DB", "demand_planning"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    )


# ── Table Creation ─────────────────────────────────────────────
def create_table(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS recommended_products (
            id SERIAL PRIMARY KEY,
            distributor_id VARCHAR(20) NOT NULL,
            product_name TEXT NOT NULL,
            reason TEXT,
            priority_rank INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_recommended_products_distributor
        ON recommended_products (distributor_id, priority_rank);
    """)

    print("recommended_products table ready")


# ── Helpers ───────────────────────────────────────────────────
def get_distributor_id(value, current_id):
    if pd.notna(value) and str(value).strip():
        return str(value).strip().split()[0].strip()
    return current_id


def get_product_name(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def is_valid_product(product_name):
    invalid_headers = {"recommended sku", "product name", "sku name"}
    return product_name and product_name.lower() not in invalid_headers


def build_record(row, distributor_id):
    rank = int(row["rank"]) if pd.notna(row["rank"]) else 99
    reason = str(row["reason"]).strip() if pd.notna(row["reason"]) else ""

    return {
        "distributor_id": distributor_id,
        "product_name": row["product_name"].strip(),
        "reason": reason,
        "priority_rank": rank,
    }


# ── Excel Loader ──────────────────────────────────────────────
def load_from_excel(file_path):
    df = pd.read_excel(file_path, sheet_name=SHEET_NAME, header=None)

    df = df.iloc[3:].reset_index(drop=True)
    df.columns = ["distributor_raw", "rank", "product_name", "reason"]

    records = []
    current_distributor_id = None

    for _, row in df.iterrows():
        current_distributor_id = get_distributor_id(
            row["distributor_raw"],
            current_distributor_id
        )

        if not current_distributor_id:
            continue

        product_name = get_product_name(row["product_name"])

        if not is_valid_product(product_name):
            continue

        row["product_name"] = product_name
        records.append(build_record(row, current_distributor_id))

    return records


# ── Seed Data ─────────────────────────────────────────────────
def seed(records, cur):
    cur.execute("DELETE FROM recommended_products;")
    print("Cleared existing rows")

    for rec in records:
        cur.execute("""
            INSERT INTO recommended_products
            (distributor_id, product_name, reason, priority_rank)
            VALUES (%s, %s, %s, %s);
        """, (
            rec["distributor_id"],
            rec["product_name"],
            rec["reason"],
            rec["priority_rank"]
        ))

    print("Inserted {} recommended rows".format(len(records)))


# ── Verify ────────────────────────────────────────────────────
def verify(cur):
    cur.execute("""
        SELECT distributor_id, COUNT(*)
        FROM recommended_products
        GROUP BY distributor_id
        ORDER BY distributor_id;
    """)

    rows = cur.fetchall()

    print("\nVerification")
    for dist_id, count in rows:
        print("  {}: {} products".format(dist_id, count))


# ── Main ──────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("Seeding recommended_products table")
    print("=" * 55)

    if not os.path.exists(EXCEL_FILE):
        print("File not found:", EXCEL_FILE)
        sys.exit(1)

    print("\nReading:", EXCEL_FILE)
    records = load_from_excel(EXCEL_FILE)

    print("Parsed {} records".format(len(records)))

    conn = get_connection()
    cur = conn.cursor()

    create_table(cur)
    seed(records, cur)
    verify(cur)

    conn.commit()
    cur.close()
    conn.close()

    print("\nDone successfully")


if __name__ == "__main__":
    main()
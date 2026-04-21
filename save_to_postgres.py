import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

RECOMMENDATION_FILE = r"sample_data\30_Recommended_New_Products.xlsx"


def get_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS distributor_demand (
            id SERIAL PRIMARY KEY,
            distributor_email TEXT,
            product_name TEXT,
            quantity INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS distributor_replies (
            id SERIAL PRIMARY KEY,
            distributor_id TEXT,
            distributor_email TEXT,
            subject TEXT,
            raw_body TEXT,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommended_products (
            id SERIAL PRIMARY KEY,
            distributor_id TEXT,
            product_name TEXT,
            priority_rank INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()


def save_demand(distributor_email, product_name, quantity):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO distributor_demand (distributor_email, product_name, quantity)
        VALUES (%s, %s, %s)
    """, (distributor_email, product_name, quantity))

    conn.commit()
    cursor.close()
    conn.close()


def save_raw_reply(distributor_id, distributor_email, subject, raw_body):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO distributor_replies (distributor_id, distributor_email, subject, raw_body)
        VALUES (%s, %s, %s, %s)
    """, (distributor_id, distributor_email, subject, raw_body))

    conn.commit()
    cursor.close()
    conn.close()


def load_recommendations_from_excel():
    df = pd.read_excel(
        RECOMMENDATION_FILE,
        sheet_name="3. Recommendation Mapping",
        header=2
    )

    print("Excel loaded successfully.")
    print("Columns found:", df.columns.tolist())

    return df


def normalize_recommendation_columns(df):
    df = df.rename(columns={
        "Distributor": "distributor_raw",
        "#": "priority_rank",
        "Recommended SKU": "product_name",
        "Recommendation Reason": "recommendation_reason"
    })

    required_columns = ["distributor_raw", "priority_rank", "product_name"]
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"Missing required columns in Excel: {missing_columns}")

    df = df[required_columns].copy()

    df["distributor_raw"] = df["distributor_raw"].ffill()
    df["distributor_id"] = df["distributor_raw"].astype(str).str.extract(r"(D\d+)", expand=False)
    df["product_name"] = df["product_name"].astype(str).str.strip()
    df["priority_rank"] = pd.to_numeric(df["priority_rank"], errors="coerce")

    df = df.dropna(subset=["distributor_id", "product_name", "priority_rank"])
    df["priority_rank"] = df["priority_rank"].astype(int)

    df = df[["distributor_id", "product_name", "priority_rank"]]

    return df


def insert_recommendations(df):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM recommended_products")

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO recommended_products (distributor_id, product_name, priority_rank)
            VALUES (%s, %s, %s)
        """, (
            row["distributor_id"],
            row["product_name"],
            row["priority_rank"]
        ))

    conn.commit()
    cursor.close()
    conn.close()


def verify_recommendations(distributor_id="D04"):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT distributor_id, product_name, priority_rank
        FROM recommended_products
        WHERE distributor_id = %s
        ORDER BY priority_rank ASC
    """, (distributor_id,))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    print(f"\nRecommendations for {distributor_id}:")
    if rows:
        for row in rows:
            print(row)
    else:
        print("No recommendations found.")


if __name__ == "__main__":
    create_tables()

    df = load_recommendations_from_excel()
    df = normalize_recommendation_columns(df)
    insert_recommendations(df)
    verify_recommendations("D04")

    print("\nData saved to PostgreSQL successfully.")
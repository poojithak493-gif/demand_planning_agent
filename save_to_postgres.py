import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")


def get_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


def create_table():
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


if __name__ == "__main__":
    create_table()
    save_demand("distributor1@gmail.com", "Product A", 100)
    print("Demand data saved to PostgreSQL successfully.")
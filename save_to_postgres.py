import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_DB = os.getenv("POSTGRES_DB", "demand_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")


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
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        sku_id VARCHAR(100) PRIMARY KEY,
        sku_name TEXT,
        sku_description TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS valid_replies (
        id SERIAL PRIMARY KEY,
        distributor_id VARCHAR(50),
        sku_id VARCHAR(100),
        product_description TEXT,
        quantity INTEGER,
        from_email VARCHAR(255),
        message_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS invalid_replies (
        id SERIAL PRIMARY KEY,
        distributor_id VARCHAR(50),
        sku_id VARCHAR(100),
        product_description TEXT,
        quantity TEXT,
        from_email VARCHAR(255),
        message_id TEXT,
        issue_type VARCHAR(100),
        issue_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    cur.close()
    conn.close()


def clear_latest_run_data():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM valid_replies;")
    cur.execute("DELETE FROM invalid_replies;")

    conn.commit()
    cur.close()
    conn.close()


def upsert_product(sku_id, sku_name, sku_description):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO products (sku_id, sku_name, sku_description)
    VALUES (%s, %s, %s)
    ON CONFLICT (sku_id)
    DO UPDATE SET
        sku_name = EXCLUDED.sku_name,
        sku_description = EXCLUDED.sku_description;
    """, (sku_id, sku_name, sku_description))

    conn.commit()
    cur.close()
    conn.close()


def save_valid_reply(distributor_id, sku_id, product_description, quantity, from_email, message_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO valid_replies (
        distributor_id,
        sku_id,
        product_description,
        quantity,
        from_email,
        message_id
    )
    VALUES (%s, %s, %s, %s, %s, %s);
    """, (distributor_id, sku_id, product_description, quantity, from_email, message_id))

    conn.commit()
    cur.close()
    conn.close()


def save_invalid_reply(distributor_id, sku_id, product_description, quantity, from_email, message_id, issue_type, issue_message):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO invalid_replies (
        distributor_id,
        sku_id,
        product_description,
        quantity,
        from_email,
        message_id,
        issue_type,
        issue_message
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """, (
        distributor_id,
        sku_id,
        product_description,
        quantity,
        from_email,
        message_id,
        issue_type,
        issue_message
    ))

    conn.commit()
    cur.close()
    conn.close()


def get_all_valid_replies():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT distributor_id, sku_id, product_description, quantity
    FROM valid_replies
    ORDER BY distributor_id, sku_id;
    """)
    rows = cur.fetchall()

    cur.close()
    conn.close()
    return rows


def get_all_invalid_replies():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT distributor_id, sku_id, product_description, quantity, issue_type, issue_message
    FROM invalid_replies
    ORDER BY distributor_id, id;
    """)
    rows = cur.fetchall()

    cur.close()
    conn.close()
    return rows
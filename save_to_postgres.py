import json
import os
from typing import Dict, Any

import psycopg2
from dotenv import load_dotenv

load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")


# =========================
# DB CONNECTION
# =========================
def get_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


# =========================
# TABLE CREATION
# =========================
def create_tables_if_not_exist():
    create_replies_table = """
    CREATE TABLE IF NOT EXISTS parsed_replies (
        id SERIAL PRIMARY KEY,
        message_id VARCHAR(255),
        from_email VARCHAR(255),
        subject TEXT,
        distributor_id VARCHAR(50),
        reply_type VARCHAR(50),
        confidence NUMERIC(5,2),
        notes TEXT,
        needs_followup BOOLEAN,
        raw_body TEXT,
        cleaned_body TEXT,
        parsed_json JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    create_items_table = """
    CREATE TABLE IF NOT EXISTS parsed_reply_items (
        id SERIAL PRIMARY KEY,
        parsed_reply_id INTEGER REFERENCES parsed_replies(id) ON DELETE CASCADE,
        sku_id VARCHAR(100),
        sku_name TEXT,
        quantity INTEGER,
        unit VARCHAR(50),
        matched_text TEXT,
        match_score INTEGER,
        source TEXT,
        sheet_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(create_replies_table)
    cur.execute(create_items_table)

    conn.commit()
    cur.close()
    conn.close()


# =========================
# SAVE FUNCTION
# =========================
def save_parsed_reply(raw_email: Dict[str, Any], parsed_data: Dict[str, Any]):
    create_tables_if_not_exist()

    conn = get_connection()
    cur = conn.cursor()

    # ---------- Insert main reply ----------
    insert_reply_sql = """
    INSERT INTO parsed_replies (
        message_id,
        from_email,
        subject,
        distributor_id,
        reply_type,
        confidence,
        notes,
        needs_followup,
        raw_body,
        cleaned_body,
        parsed_json
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id;
    """

    cur.execute(
        insert_reply_sql,
        (
            raw_email.get("message_id"),
            raw_email.get("from_email"),
            raw_email.get("subject"),
            parsed_data.get("distributor_id"),
            parsed_data.get("reply_type"),
            parsed_data.get("confidence"),
            parsed_data.get("notes"),
            parsed_data.get("needs_followup"),
            parsed_data.get("raw_body"),
            parsed_data.get("cleaned_body"),
            json.dumps(parsed_data),
        )
    )

    parsed_reply_id = cur.fetchone()[0]

    # ---------- Insert items ----------
    insert_item_sql = """
    INSERT INTO parsed_reply_items (
        parsed_reply_id,
        sku_id,
        sku_name,
        quantity,
        unit,
        matched_text,
        match_score,
        source,
        sheet_name
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    for item in parsed_data.get("items", []):
        cur.execute(
            insert_item_sql,
            (
                parsed_reply_id,
                item.get("sku_id"),
                item.get("sku_name"),
                item.get("quantity"),
                item.get("unit"),
                item.get("matched_text"),
                item.get("match_score"),
                item.get("source", "email_body"),   # default source
                item.get("sheet_name"),             # None if not Excel
            )
        )

    conn.commit()
    cur.close()
    conn.close()

    print(f"Saved parsed reply successfully → ID: {parsed_reply_id}")
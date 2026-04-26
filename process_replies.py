from pprint import pprint
import os
from email.utils import parseaddr

import psycopg2
from dotenv import load_dotenv

from read_replies import read_unseen_replies
from save_to_postgres import save_parsed_reply

from app.services.reply_parser_service import parse_reply
from app.services.attachment_parser_service import (
    parse_excel_file,
    is_excel_attachment,
)
from app.data.sku_data import load_sku_data


load_dotenv()

PRIMARY_SALES_FILE = "sample_data/Primary_Sales.xlsx"
RECOMMENDED_PRODUCTS_FILE = "sample_data/30_Recommended_New_Products.xlsx"


DISTRIBUTOR_EMAIL_MAP = {
    "revanbejagam@gmail.com": "D01",
    "rishithareddyc2002@gmail.com": "D02",
    "saherwardi.mustafa@gmail.com": "D03",
    "lingaphani21@gmail.com": "D04",
    "poojithak493@gmail.com": "D05",
}


def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", 5432),
        dbname=os.getenv("POSTGRES_DB", "postgres"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    )


def clean_email(from_email):
    if not from_email:
        return ""

    _, email = parseaddr(from_email)
    return email.strip().lower()


def get_distributor_id_from_email(from_email):
    email = clean_email(from_email)
    return DISTRIBUTOR_EMAIL_MAP.get(email, "UNKNOWN")


def ensure_confirmed_demands_table():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS confirmed_demands (
            id SERIAL PRIMARY KEY,
            parsed_reply_id INTEGER,
            distributor_id VARCHAR(50),
            distributor_mail VARCHAR(255),
            sku_id VARCHAR(100),
            sku_name TEXT,
            sku_description TEXT,
            quantity INTEGER,
            source VARCHAR(50),
            cycle_date DATE DEFAULT CURRENT_DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        ALTER TABLE confirmed_demands
        ADD COLUMN IF NOT EXISTS parsed_reply_id INTEGER;
    """)

    cur.execute("""
        ALTER TABLE confirmed_demands
        ADD COLUMN IF NOT EXISTS distributor_id VARCHAR(50);
    """)

    cur.execute("""
        ALTER TABLE confirmed_demands
        ADD COLUMN IF NOT EXISTS distributor_mail VARCHAR(255);
    """)

    cur.execute("""
        ALTER TABLE confirmed_demands
        ADD COLUMN IF NOT EXISTS sku_id VARCHAR(100);
    """)

    cur.execute("""
        ALTER TABLE confirmed_demands
        ADD COLUMN IF NOT EXISTS sku_name TEXT;
    """)

    cur.execute("""
        ALTER TABLE confirmed_demands
        ADD COLUMN IF NOT EXISTS sku_description TEXT;
    """)

    cur.execute("""
        ALTER TABLE confirmed_demands
        ADD COLUMN IF NOT EXISTS quantity INTEGER;
    """)

    cur.execute("""
        ALTER TABLE confirmed_demands
        ADD COLUMN IF NOT EXISTS source VARCHAR(50);
    """)

    cur.execute("""
        ALTER TABLE confirmed_demands
        ADD COLUMN IF NOT EXISTS cycle_date DATE DEFAULT CURRENT_DATE;
    """)

    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'confirmed_demands_distributor_id_sku_id_cycle_date_key'
            ) THEN
                ALTER TABLE confirmed_demands
                ADD CONSTRAINT confirmed_demands_distributor_id_sku_id_cycle_date_key
                UNIQUE (distributor_id, sku_id, cycle_date);
            END IF;
        END
        $$;
    """)

    conn.commit()
    cur.close()
    conn.close()


def get_product_details(sku_id=None, sku_name=None):
    product = {
        "sku_id": sku_id,
        "sku_name": sku_name,
        "sku_description": None,
    }

    conn = get_connection()
    cur = conn.cursor()

    try:
        if sku_id:
            cur.execute("""
                SELECT 
                    sku_id,
                    sku_name,
                    sku_description
                FROM products
                WHERE LOWER(sku_id) = LOWER(%s)
                LIMIT 1;
            """, (sku_id,))

            row = cur.fetchone()

            if row:
                product["sku_id"] = row[0]
                product["sku_name"] = row[1]
                product["sku_description"] = row[2]
                return product

        if sku_name:
            cur.execute("""
                SELECT 
                    sku_id,
                    sku_name,
                    sku_description
                FROM products
                WHERE LOWER(sku_name) = LOWER(%s)
                   OR LOWER(sku_name) LIKE LOWER(%s)
                LIMIT 1;
            """, (sku_name, f"%{sku_name}%"))

            row = cur.fetchone()

            if row:
                product["sku_id"] = row[0]
                product["sku_name"] = row[1]
                product["sku_description"] = row[2]
                return product

    except Exception as exc:
        print(f"Product lookup skipped: {exc}")

    finally:
        cur.close()
        conn.close()

    return product


def save_confirmed_demands(parsed_reply_id, raw_email, parsed_data):
    ensure_confirmed_demands_table()

    if parsed_data.get("reply_type") != "demand":
        print("Not a demand reply. Skipping confirmed_demands.")
        return

    distributor_mail = clean_email(raw_email.get("from_email"))

    distributor_id = parsed_data.get("distributor_id")

    if not distributor_id or distributor_id.upper() == "UNKNOWN":
        distributor_id = get_distributor_id_from_email(distributor_mail)

    items = parsed_data.get("items", [])

    if not items:
        print("No items found. Skipping confirmed_demands.")
        return

    conn = get_connection()
    cur = conn.cursor()

    saved_count = 0

    for item in items:
        quantity = item.get("quantity")

        if quantity is None:
            continue

        try:
            quantity = int(quantity)
        except Exception:
            continue

        if quantity <= 0:
            continue

        sku_id = item.get("sku_id")
        sku_name = item.get("sku_name")

        if not sku_id and not sku_name:
            continue

        product = get_product_details(
            sku_id=sku_id,
            sku_name=sku_name
        )

        final_sku_id = product.get("sku_id") or sku_id
        final_sku_name = product.get("sku_name") or sku_name

        final_sku_description = (
            product.get("sku_description")
            or item.get("sku_description")
            or item.get("matched_text")
            or final_sku_name
        )

        cur.execute("""
            INSERT INTO confirmed_demands (
                parsed_reply_id,
                distributor_id,
                distributor_mail,
                sku_id,
                sku_name,
                sku_description,
                quantity,
                source,
                cycle_date
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE)
            ON CONFLICT (distributor_id, sku_id, cycle_date)
            DO UPDATE SET
                parsed_reply_id = EXCLUDED.parsed_reply_id,
                distributor_mail = EXCLUDED.distributor_mail,
                sku_name = EXCLUDED.sku_name,
                sku_description = EXCLUDED.sku_description,
                quantity = EXCLUDED.quantity,
                source = EXCLUDED.source;
        """, (
            parsed_reply_id,
            distributor_id,
            distributor_mail,
            final_sku_id,
            final_sku_name,
            final_sku_description,
            quantity,
            item.get("source", "email_body"),
        ))

        saved_count += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"Saved/updated {saved_count} item(s) into confirmed_demands.")


def merge_attachment_items(parsed_data, attachment_items):
    if not attachment_items:
        return parsed_data

    text_items = parsed_data.get("items", []) or []
    final_items = []
    excel_sku_ids = set()

    for item in attachment_items:
        final_items.append(item)

        if item.get("sku_id"):
            excel_sku_ids.add(item["sku_id"])

    for item in text_items:
        sku_id = item.get("sku_id")

        if sku_id and sku_id not in excel_sku_ids:
            final_items.append(item)

    parsed_data["items"] = final_items
    parsed_data["reply_type"] = "demand"
    parsed_data["needs_followup"] = False
    parsed_data["notes"] = "Excel attachment used as primary source."

    if parsed_data.get("confidence", 0) < 0.95:
        parsed_data["confidence"] = 0.95

    return parsed_data


def keep_latest_email_per_distributor(emails):
    latest_emails = {}

    for email in emails:
        from_email = email.get("from_email")
        distributor_id = get_distributor_id_from_email(from_email)

        if distributor_id == "UNKNOWN":
            distributor_id = clean_email(from_email)

        if distributor_id not in latest_emails:
            latest_emails[distributor_id] = email

    return list(latest_emails.values())


def process_all_replies():
    print("Loading SKU master data...")

    load_sku_data(
        primary_sales_file=PRIMARY_SALES_FILE,
        recommended_products_file=RECOMMENDED_PRODUCTS_FILE
    )

    print("SKU data loaded successfully")

    emails = read_unseen_replies()

    if not emails:
        print("No unread replies found.")
        return

    print(f"Found {len(emails)} email(s)")

    emails = keep_latest_email_per_distributor(emails)

    print(f"Processing only latest {len(emails)} email(s), one per distributor")

    for index, item in enumerate(emails, start=1):
        print("=" * 80)
        print(f"Processing Email #{index}")
        print("Message ID:", item["message_id"])
        print("From:", item["from_email"])
        print("Subject:", item["subject"])
        print("Body:")
        print(item["body"])
        print("Attachments:", item.get("attachment_paths", []))
        print("-" * 80)

        from_email = item.get("from_email")

        parsed = parse_reply(
            from_email=from_email,
            body=item["body"]
        )

        distributor_id = parsed.get("distributor_id")

        if not distributor_id or distributor_id.upper() == "UNKNOWN":
            distributor_id = get_distributor_id_from_email(from_email)

        parsed["distributor_id"] = distributor_id

        attachment_items = []

        for attachment_path in item.get("attachment_paths", []):
            if is_excel_attachment(attachment_path):
                print(f"Parsing attachment: {attachment_path}")

                try:
                    excel_items = parse_excel_file(attachment_path)
                    print(f"Parsed {len(excel_items)} items from Excel")
                    attachment_items.extend(excel_items)

                except Exception as exc:
                    print(f"Error parsing Excel: {exc}")

        parsed = merge_attachment_items(parsed, attachment_items)

        if not parsed.get("distributor_id") or parsed.get("distributor_id").upper() == "UNKNOWN":
            parsed["distributor_id"] = get_distributor_id_from_email(from_email)

        print("Final Parsed Output:")
        pprint(parsed)

        saved_id = save_parsed_reply(
            raw_email=item,
            parsed_data=parsed
        )

        if saved_id is not None:
            save_confirmed_demands(
                parsed_reply_id=saved_id,
                raw_email=item,
                parsed_data=parsed
            )
        else:
            print("Email already saved in parsed_replies. Skipping confirmed_demands update.")

        if parsed.get("needs_followup"):
            print("Follow-up required for this reply.")

        print("=" * 80)


if __name__ == "__main__":
    process_all_replies()
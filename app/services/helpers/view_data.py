import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def view_runtime_data() -> None:
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    demand_id,
                    distributor_id,
                    sku_id,
                    cycle_id,
                    confirmed_qty,
                    week1_qty,
                    week2_qty,
                    week3_qty,
                    week4_qty,
                    validation_status,
                    reply_received_at
                FROM demand_records
                ORDER BY reply_received_at DESC
                LIMIT 20
                """
            )
            demand_rows = cur.fetchall()

            print("\nLATEST DEMAND RECORDS:\n")
            for row in demand_rows:
                print(row)

            cur.execute(
                """
                SELECT
                    id,
                    distributor_code,
                    from_email,
                    subject,
                    received_at,
                    processing_status,
                    parse_status,
                    notes
                FROM inbound_mail_responses
                ORDER BY received_at DESC
                LIMIT 20
                """
            )
            mail_rows = cur.fetchall()

            print("\nLATEST INBOUND MAIL RESPONSES:\n")
            for row in mail_rows:
                print(row)
    finally:
        conn.close()


if __name__ == "__main__":
    view_runtime_data()

import os
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import logging
from datetime import date

load_dotenv(override=False)

logger = logging.getLogger(__name__)

# ── Connection config ──────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "")
    db_host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    db_port = os.getenv("POSTGRES_PORT", "5433")
    db_name = os.getenv("POSTGRES_DB", "demand_planning")

    DATABASE_URL = (
        f"postgresql://{db_user}:{db_password}"
        f"@{db_host}:{db_port}/{db_name}"
    )

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5433")
POSTGRES_DB = os.getenv("POSTGRES_DB", "demand_planning")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

# ── SQLAlchemy setup ───────────────────────────────────────────────────────────
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_connection():
    """
    Raw psycopg2 connection.
    """
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )


def ensure_confirmed_demands_table():
    ddl = """
        CREATE TABLE IF NOT EXISTS confirmed_demands (
            id SERIAL PRIMARY KEY,
            distributor_id VARCHAR(20) NOT NULL,
            sku_id VARCHAR(50) NOT NULL,
            confirmed_30d_qty INTEGER NOT NULL DEFAULT 0,
            week1_qty INTEGER NOT NULL DEFAULT 0,
            week2_qty INTEGER NOT NULL DEFAULT 0,
            week3_qty INTEGER NOT NULL DEFAULT 0,
            week4_qty INTEGER NOT NULL DEFAULT 0,
            demand_status_locked BOOLEAN NOT NULL DEFAULT FALSE,
            reply_latency_days INTEGER,
            validation_status VARCHAR(20) NOT NULL DEFAULT 'valid',
            cycle_date DATE NOT NULL DEFAULT CURRENT_DATE,
            parsed_reply_id INTEGER REFERENCES parsed_replies(id),
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            UNIQUE (distributor_id, sku_id, cycle_date)
        );
    """

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(ddl)
    finally:
        conn.close()


def write_confirmed_qty(
    distributor_id: str,
    sku_id: str,
    confirmed_30d_qty: int,
    week1_qty: int,
    week2_qty: int,
    week3_qty: int,
    week4_qty: int,
    reply_latency_days: int | None,
    validation_status: str,
    parsed_reply_id: int | None,
    cycle_date: date | None = None,
) -> int:
    cycle_date = cycle_date or date.today()

    sql = """
        INSERT INTO confirmed_demands (
            distributor_id,
            sku_id,
            confirmed_30d_qty,
            week1_qty,
            week2_qty,
            week3_qty,
            week4_qty,
            demand_status_locked,
            reply_latency_days,
            validation_status,
            parsed_reply_id,
            cycle_date,
            updated_at
        )
        VALUES (
            %(distributor_id)s,
            %(sku_id)s,
            %(confirmed_30d_qty)s,
            %(week1_qty)s,
            %(week2_qty)s,
            %(week3_qty)s,
            %(week4_qty)s,
            TRUE,
            %(reply_latency_days)s,
            %(validation_status)s,
            %(parsed_reply_id)s,
            %(cycle_date)s,
            NOW()
        )
        ON CONFLICT (distributor_id, sku_id, cycle_date)
        DO UPDATE SET
            confirmed_30d_qty = EXCLUDED.confirmed_30d_qty,
            week1_qty = EXCLUDED.week1_qty,
            week2_qty = EXCLUDED.week2_qty,
            week3_qty = EXCLUDED.week3_qty,
            week4_qty = EXCLUDED.week4_qty,
            demand_status_locked = TRUE,
            reply_latency_days = EXCLUDED.reply_latency_days,
            validation_status = EXCLUDED.validation_status,
            updated_at = NOW()
        RETURNING id;
    """

    params = {
        "distributor_id": distributor_id,
        "sku_id": sku_id,
        "confirmed_30d_qty": confirmed_30d_qty,
        "week1_qty": week1_qty,
        "week2_qty": week2_qty,
        "week3_qty": week3_qty,
        "week4_qty": week4_qty,
        "reply_latency_days": reply_latency_days,
        "validation_status": validation_status,
        "parsed_reply_id": parsed_reply_id,
        "cycle_date": cycle_date,
    }

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchone()[0]
    finally:
        conn.close()
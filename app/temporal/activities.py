import psycopg2
from temporalio import activity
from app.core.database import get_connection, write_confirmed_qty

BASE = "http://localhost:8000"


@activity.defn
async def fetch_context_activity(distributor_id: str) -> dict:
    return {"distributor_id": distributor_id, "status": "skipped"}


@activity.defn
async def validate_reply_activity(parsed_reply_id: int) -> dict:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, distributor_id, reply_type, confidence
                FROM parsed_replies WHERE id = %s
            """, (parsed_reply_id,))
            reply = cur.fetchone()

            if not reply:
                return {"status": "invalid", "reason": "Reply not found", "total_confirmed_qty": 0}

            reply_id, distributor_id, reply_type, confidence = reply

            if reply_type != "demand":
                return {"status": "invalid", "reason": f"Type is {reply_type}", "total_confirmed_qty": 0}

            cur.execute("""
                SELECT sku_id, sku_name, quantity
                FROM parsed_reply_items WHERE parsed_reply_id = %s
            """, (reply_id,))
            items = cur.fetchall()

            if not items:
                return {"status": "invalid", "reason": "No items", "total_confirmed_qty": 0}

            total_qty = sum(i[2] for i in items if i[2])

            return {
                "status": "valid",
                "distributor_id": distributor_id,
                "total_confirmed_qty": total_qty,
                "items": [{"sku_id": i[0], "sku_name": i[1], "quantity": i[2]} for i in items]
            }
    finally:
        conn.close()


@activity.defn
async def write_confirmed_qty_activity(distributor_id: str, validated: dict):
    items = validated.get("items", [])
    for item in items:
        qty = item.get("quantity", 0) or 0
        write_confirmed_qty(
            distributor_id=distributor_id,
            sku_id=item.get("sku_id", "UNKNOWN"),
            confirmed_30d_qty=qty,
            week1_qty=qty // 4,
            week2_qty=qty // 4,
            week3_qty=qty // 4,
            week4_qty=qty - (qty // 4) * 3,
            reply_latency_days=None,
            validation_status="valid",
            parsed_reply_id=None,
        )


@activity.defn
async def emit_demand_confirmed_activity(distributor_id: str, confirmed_qty: int):
    from app.events.producers import emit_demand_confirmed
    emit_demand_confirmed(distributor_id, confirmed_qty)
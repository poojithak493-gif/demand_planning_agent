import psycopg2
from temporalio import activity
from app.core.database import get_connection, write_confirmed_qty


@activity.defn
async def fetch_context_activity(distributor_id: str) -> dict:
    return {"distributor_id": distributor_id, "status": "fetched"}


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
                return {"status": "invalid", "reason": f"Type is '{reply_type}' — not a demand reply", "total_confirmed_qty": 0}

            cur.execute("""
                SELECT sku_id, sku_name, quantity
                FROM parsed_reply_items WHERE parsed_reply_id = %s
            """, (reply_id,))
            items = cur.fetchall()

            if not items:
                return {"status": "invalid", "reason": "No items found in reply", "total_confirmed_qty": 0}

            total_qty = sum(i[2] for i in items if i[2])

            return {
                "status":             "valid",
                "distributor_id":     distributor_id,
                "total_confirmed_qty": total_qty,
                "items": [
                    {"sku_id": i[0], "sku_name": i[1], "quantity": i[2]}
                    for i in items
                ]
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
async def send_confirmation_email_activity(distributor_id: str, validated: dict):
    """
    Sends a confirmation email back to the distributor after their
    demand reply has been validated and written to the database.
    This is Fix 9 — the missing demand confirmation email.
    """
    from app.services.send_demand_email_service import send_email
    from app.data.distributor_data import DISTRIBUTORS

    # Find distributor email from the static map
    dist = next((d for d in DISTRIBUTORS if d["id"] == distributor_id), None)
    if not dist:
        return {"status": "error", "message": f"Distributor {distributor_id} not found"}

    items = validated.get("items", [])

    if items:
        lines = "\n".join(
            f"  {i + 1}. {item.get('sku_name', item.get('sku_id', 'Unknown'))}: "
            f"{item.get('quantity', 0)} units"
            for i, item in enumerate(items)
        )
    else:
        lines = "  No items recorded."

    total_qty = validated.get("total_confirmed_qty", 0)

    body = f"""Dear Distributor,

Thank you for sharing your demand for the upcoming month.

We have successfully recorded your confirmed demand:

{lines}

Total Confirmed Quantity: {total_qty} units

Your demand is now locked for this planning cycle. Our production
and logistics teams will use this to schedule deliveries.

If you need to make any changes, please contact us immediately.

Regards,
Lipton Enterprises - Demand Planning Team
"""

    result = send_email(
        to_email=dist["email"],
        subject="Demand Confirmation — Lipton Enterprises",
        body=body
    )

    print(f"[Confirmation] Email sent to {dist['email']} → {result}")
    return result


@activity.defn
async def emit_demand_confirmed_activity(distributor_id: str, confirmed_qty: int):
    from app.events.producers import emit_demand_confirmed
    emit_demand_confirmed(distributor_id, confirmed_qty)
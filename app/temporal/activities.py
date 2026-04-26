import psycopg2
from temporalio import activity

from app.core.database import get_connection, write_confirmed_qty

BASE = "http://localhost:8000"


@activity.defn
async def fetch_context_activity(distributor_id: str) -> dict:
<<<<<<< Updated upstream
    return {"distributor_id": distributor_id, "status": "skipped"}
=======
    return {
        "distributor_id": distributor_id,
        "status": "fetched",
    }
>>>>>>> Stashed changes


@activity.defn
async def validate_reply_activity(parsed_reply_id: int) -> dict:
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, distributor_id, reply_type, confidence
                FROM parsed_replies
                WHERE id = %s
                """,
                (parsed_reply_id,),
            )
            reply = cur.fetchone()

            if not reply:
                return {
                    "status": "invalid",
                    "reason": "Reply not found",
                    "total_confirmed_qty": 0,
                }

            reply_id, distributor_id, reply_type, _ = reply

            if reply_type != "demand":
<<<<<<< Updated upstream
                return {"status": "invalid", "reason": f"Type is {reply_type}", "total_confirmed_qty": 0}
=======
                return {
                    "status": "invalid",
                    "reason": f"Type is '{reply_type}' - not a demand reply",
                    "total_confirmed_qty": 0,
                }
>>>>>>> Stashed changes

            cur.execute(
                """
                SELECT sku_id, sku_name, quantity
                FROM parsed_reply_items
                WHERE parsed_reply_id = %s
                """,
                (reply_id,),
            )
            items = cur.fetchall()

            if not items:
<<<<<<< Updated upstream
                return {"status": "invalid", "reason": "No items", "total_confirmed_qty": 0}
=======
                return {
                    "status": "invalid",
                    "reason": "No items found in reply",
                    "total_confirmed_qty": 0,
                }
>>>>>>> Stashed changes

            total_qty = sum(item[2] for item in items if item[2])

            return {
                "status": "valid",
                "distributor_id": distributor_id,
                "total_confirmed_qty": total_qty,
<<<<<<< Updated upstream
                "items": [{"sku_id": i[0], "sku_name": i[1], "quantity": i[2]} for i in items]
=======
                "items": [
                    {
                        "sku_id": item[0],
                        "sku_name": item[1],
                        "quantity": item[2],
                    }
                    for item in items
                ],
>>>>>>> Stashed changes
            }

    finally:
        conn.close()


@activity.defn
async def write_confirmed_qty_activity(
    distributor_id: str,
    validated: dict,
) -> dict:
    items = validated.get("items", [])

    for item in items:
        qty = item.get("quantity", 0) or 0
        weekly_qty = qty // 4

        write_confirmed_qty(
            distributor_id=distributor_id,
            sku_id=item.get("sku_id", "UNKNOWN"),
            confirmed_30d_qty=qty,
            week1_qty=weekly_qty,
            week2_qty=weekly_qty,
            week3_qty=weekly_qty,
            week4_qty=qty - (weekly_qty * 3),
            reply_latency_days=None,
            validation_status="valid",
            parsed_reply_id=None,
        )

    return {
        "status": "success",
        "rows_written": len(items),
    }


@activity.defn
<<<<<<< Updated upstream
async def emit_demand_confirmed_activity(distributor_id: str, confirmed_qty: int):
=======
async def send_confirmation_email_activity(
    distributor_id: str,
    validated: dict,
) -> dict:
    from app.data.distributor_data import DISTRIBUTORS
    from app.services.send_demand_email_service import send_email

    distributor = next(
        (item for item in DISTRIBUTORS if item["id"] == distributor_id),
        None,
    )

    if not distributor:
        return {
            "status": "error",
            "message": f"Distributor {distributor_id} not found",
        }

    items = validated.get("items", [])

    if items:
        lines = "\n".join(
            (
                f"{index + 1}. "
                f"{item.get('sku_name', item.get('sku_id', 'Unknown'))}: "
                f"{item.get('quantity', 0)} units"
            )
            for index, item in enumerate(items)
        )
    else:
        lines = "No items recorded."

    total_qty = validated.get("total_confirmed_qty", 0)

    body = f"""Dear Distributor,

Thank you for sharing your demand for the upcoming month.

We have successfully recorded your confirmed demand:

{lines}

Total Confirmed Quantity: {total_qty} units

Your demand is now locked for this planning cycle.
Our production and logistics teams will use this
to schedule deliveries.

If you need to make any changes, please contact us immediately.

Regards,
Lipton Enterprises - Demand Planning Team
"""

    return send_email(
        to_email=distributor["email"],
        subject="Demand Confirmation - Lipton Enterprises",
        body=body,
    )


@activity.defn
async def emit_demand_confirmed_activity(
    distributor_id: str,
    confirmed_qty: int,
) -> dict:
>>>>>>> Stashed changes
    from app.events.producers import emit_demand_confirmed

    emit_demand_confirmed(distributor_id, confirmed_qty)

    return {
        "status": "success",
        "distributor_id": distributor_id,
        "confirmed_qty": confirmed_qty,
    }
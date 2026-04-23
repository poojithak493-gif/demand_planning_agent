import httpx
from temporalio import activity

BASE = "http://localhost:8000"

@activity.defn
async def fetch_context_activity(distributor_id: str) -> dict:
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/distributor/{distributor_id}/context")
        return r.json()

@activity.defn
async def send_email_activity(distributor_id: str) -> str:
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE}/email/send", json={"distributor_id": distributor_id})
        return r.json()["status"]

@activity.defn
async def validate_reply_activity(parsed_reply_id: int) -> dict:
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE}/validate", json={"parsed_reply_id": parsed_reply_id})
        return r.json()

@activity.defn
async def write_confirmed_qty_activity(distributor_id: str, validated: dict):
    async with httpx.AsyncClient() as c:
        await c.post(f"{BASE}/demand/write", json={
            "distributor_id": distributor_id, **validated
        })

@activity.defn
async def emit_demand_confirmed_activity(distributor_id: str, confirmed_qty: int):
    from app.events.producers import emit_demand_confirmed
    emit_demand_confirmed(distributor_id, confirmed_qty)
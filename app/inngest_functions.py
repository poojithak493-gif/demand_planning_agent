"""
app/inngest_functions.py

Inngest functions for the Demand Planning Agent.
Two functions:
  1. demand_cycle_monthly  - fires on 1st of every month at 9 AM
  2. demand_cycle_manual   - fires on demand/cycle.start event (manual trigger)
"""

import inngest
import httpx
import os

# ── Inngest client ─────────────────────────────────────────────────────────────
# No signing key needed for local dev mode
inngest_client = inngest.Inngest(
    app_id="demand-planning-agent",
    is_production=False,
)

FASTAPI_BASE = os.getenv("FASTAPI_BASE_URL", "http://fastapi:8000")


# ── Function 1: Monthly cron trigger ──────────────────────────────────────────
@inngest_client.create_function(
    fn_id="demand-cycle-monthly",
    trigger=inngest.TriggerCron(cron="0 9 1 * *"),
)
async def demand_cycle_monthly(ctx: inngest.Context, step: inngest.Step):
    """
    Automatically fires on the 1st of every month at 9 AM.
    Calls /send-bulk to send demand emails to all distributors.
    """
    result = await step.run("send-bulk-emails", send_bulk)
    return {"status": "triggered", "result": result}


# ── Function 2: Manual event trigger ──────────────────────────────────────────
@inngest_client.create_function(
    fn_id="demand-cycle-manual",
    trigger=inngest.TriggerEvent(event="demand/cycle.start"),
)
async def demand_cycle_manual(ctx: inngest.Context, step: inngest.Step):
    """
    Fires when demand/cycle.start event is sent manually from the dashboard.
    Useful for testing or triggering mid-month cycles.
    """
    result = await step.run("send-bulk-emails", send_bulk)
    return {"status": "triggered", "result": result}


# ── Shared step ────────────────────────────────────────────────────────────────
async def send_bulk():
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(f"{FASTAPI_BASE}/send-bulk")
        response.raise_for_status()
        return response.json()


# ── Export ─────────────────────────────────────────────────────────────────────
inngest_functions = [demand_cycle_monthly, demand_cycle_manual]
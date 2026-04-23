import asyncio
from temporalio.worker import Worker
from app.temporal.client import get_temporal_client
from app.temporal.workflow import DemandPlanningWorkflow
from app.temporal.activities import (
    fetch_context_activity, send_email_activity,
    validate_reply_activity, write_confirmed_qty_activity,
    emit_demand_confirmed_activity
)

async def main():
    client = await get_temporal_client()
    worker = Worker(
        client,
        task_queue="demand-planning-queue",
        workflows=[DemandPlanningWorkflow],
        activities=[
            fetch_context_activity, send_email_activity,
            validate_reply_activity, write_confirmed_qty_activity,
            emit_demand_confirmed_activity,
        ],
    )
    print("Worker started on queue: demand-planning-queue")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
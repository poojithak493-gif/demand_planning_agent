import asyncio
import os

from temporalio.client import Client
from temporalio.worker import Worker

from app.workflows.demand_cycle_workflow import DemandCycleWorkflow
from app.workflows.activities import (
    fetch_distributor_context_activity,
    graph_recommendation_activity,
    build_email_activity,
    send_email_activity,
)


async def main():
    client = await Client.connect(os.getenv("TEMPORAL_SERVER", "localhost:7233"))

    worker = Worker(
        client,
        task_queue=os.getenv("TEMPORAL_TASK_QUEUE", "demand-planning-queue"),
        workflows=[DemandCycleWorkflow],
        activities=[
            fetch_distributor_context_activity,
            graph_recommendation_activity,
            build_email_activity,
            send_email_activity,
        ],
    )

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
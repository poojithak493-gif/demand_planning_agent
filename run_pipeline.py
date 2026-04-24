import time
import threading
import asyncio

from process_replies import process_all_replies
from app.events.consumers import consume_reply_received
from app.temporal.client import get_temporal_client
from app.temporal.workflow import DemandPlanningWorkflow

POLL_INTERVAL_SECONDS = 300  # 5 minutes


async def handle_reply_async(distributor_id: str, parsed_reply_id: int):
    client = await get_temporal_client()
    workflow_id = f"demand-{distributor_id}-{parsed_reply_id}"
    try:
        handle = await client.start_workflow(
            DemandPlanningWorkflow.run,
            distributor_id,
            id=workflow_id,
            task_queue="demand-planning-queue",
        )
        print(f"Temporal workflow started → distributor={distributor_id} reply_id={parsed_reply_id}")
    except Exception:
        handle = client.get_workflow_handle(workflow_id)
        print(f"Workflow already exists → {workflow_id}")

    await handle.signal(
        DemandPlanningWorkflow.reply_received,
        {"parsed_reply_id": parsed_reply_id, "distributor_id": distributor_id}
    )
    print(f"Signal sent → workflow={workflow_id}")


def handle_reply(distributor_id: str, parsed_reply_id: int):
    """Called by RedPanda consumer for each ReplyReceived event."""
    asyncio.run(handle_reply_async(distributor_id, parsed_reply_id))


def start_consumer():
    """Runs in background thread — listens to RedPanda forever."""
    print("RedPanda consumer started — waiting for ReplyReceived events...")
    consume_reply_received(handle_reply)


def start_poller():
    """Polls Gmail every 5 minutes in main thread."""
    while True:
        print("\n--- Polling Gmail for new replies ---")
        try:
            process_all_replies()
        except Exception as e:
            print(f"Poller error: {e}")
        print(f"Next poll in {POLL_INTERVAL_SECONDS // 60} minutes...")
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    print("Starting automated demand planning pipeline...")

    # Start RedPanda consumer in background thread
    consumer_thread = threading.Thread(target=start_consumer, daemon=True)
    consumer_thread.start()

    # Small delay to let consumer connect before polling starts
    time.sleep(2)

    # Start Gmail poller in main thread (runs forever)
    start_poller()
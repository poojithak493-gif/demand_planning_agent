"""
run_pipeline_service.py
"""

import os
import time
import threading
import asyncio
from pprint import pprint
from dotenv import load_dotenv

load_dotenv()

from read_replies import read_unseen_replies
from save_to_postgres import save_parsed_reply
from app.services.reply_parser_service import parse_reply
from app.services.attachment_parser_service import (
    parse_excel_file,
    is_excel_attachment,
)
from app.data.sku_data import load_sku_data
from app.events.producers import emit_reply_received
from app.events.consumers import consume_reply_received
from app.temporal.client import get_temporal_client
from app.temporal.workflow import DemandPlanningWorkflow

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))

PRIMARY_SALES_FILE = "sample_data/Primary_Sales.xlsx"
RECOMMENDED_PRODUCTS_FILE = "sample_data/30_Recommended_New_Products.xlsx"
WORKFLOW_ID_TEMPLATE = "demand-{}-cycle"



def get_workflow_id(distributor_id: str) -> str:
    return WORKFLOW_ID_TEMPLATE.format(distributor_id)


async def start_or_get_workflow(client, distributor_id: str):
    workflow_id = get_workflow_id(distributor_id)

    try:
        await client.start_workflow(
            DemandPlanningWorkflow.run,
            distributor_id,
            id=workflow_id,
            task_queue="demand-planning-queue",
        )
        print(f"[Temporal] Workflow started → {workflow_id}")
    except RuntimeError:
        print(f"[Temporal] Workflow already running → {workflow_id}")

    return client.get_workflow_handle(workflow_id)


async def signal_temporal_async(distributor_id: str, parsed_reply_id: int):
    client = await get_temporal_client()

    handle = await start_or_get_workflow(client, distributor_id)

    await handle.signal(
        DemandPlanningWorkflow.reply_received,
        {
            "parsed_reply_id": parsed_reply_id,
            "distributor_id": distributor_id,
        },
    )

    print(f"[Temporal] Signal sent → {parsed_reply_id}")


def signal_temporal(distributor_id: str, parsed_reply_id: int):
    asyncio.run(signal_temporal_async(distributor_id, parsed_reply_id))




def on_reply_received(distributor_id: str, parsed_reply_id: int):
    print(
        "[RedPanda] ReplyReceived → "
        f"distributor={distributor_id}, reply_id={parsed_reply_id}"
    )
    signal_temporal(distributor_id, parsed_reply_id)


def start_redpanda_consumer():
    try:
        consume_reply_received(on_reply_received)
    except RuntimeError as exc:
        print(f"[RedPanda] Consumer failed: {exc}")




def merge_attachment_items(parsed_data: dict, attachment_items: list) -> dict:
    if not attachment_items:
        return parsed_data

    text_items = parsed_data.get("items", [])
    excel_ids = {item["sku_id"] for item in attachment_items if item.get("sku_id")}

    final_items = list(attachment_items)

    for item in text_items:
        sku_id = item.get("sku_id")

        if sku_id and sku_id not in excel_ids:
            final_items.append(item)

    parsed_data["items"] = final_items
    parsed_data["reply_type"] = "demand"
    parsed_data["needs_followup"] = False
    parsed_data["notes"] = "Excel attachment used as primary source."
    parsed_data["confidence"] = max(parsed_data.get("confidence", 0), 0.95)

    return parsed_data




def parse_attachments(item: dict) -> list:
    attachment_items = []

    for path in item.get("attachment_paths", []):
        if not is_excel_attachment(path):
            continue

        try:
            print(f"[Poller] Parsing attachment: {path}")
            rows = parse_excel_file(path)
            attachment_items.extend(rows)
        except ValueError as exc:
            print(f"[Poller] Attachment parse failed: {exc}")

    return attachment_items


def emit_pipeline_event(parsed: dict, saved_id: int):
    try:
        emit_reply_received(
            distributor_id=parsed["distributor_id"],
            parsed_reply_id=saved_id,
        )
        print("[Poller] RedPanda event emitted ✓")

    except RuntimeError as exc:
        print(f"[Poller] Event emit failed: {exc}")
        signal_temporal(parsed["distributor_id"], saved_id)


def should_emit_event(parsed: dict, saved_id):
    return saved_id is not None and parsed.get("reply_type") == "demand"


def process_email(index: int, item: dict):
    print(f"\n--- Email #{index} ---")
    print(f"From: {item['from_email']}")
    print(f"Subject: {item['subject']}")

    parsed = parse_reply(
        from_email=item["from_email"],
        body=item["body"],
    )

    attachment_items = parse_attachments(item)
    parsed = merge_attachment_items(parsed, attachment_items)

    pprint(parsed)

    saved_id = save_parsed_reply(raw_email=item, parsed_data=parsed)

    if saved_id is None:
        print("[Poller] Already processed")
        return

    if should_emit_event(parsed, saved_id):
        emit_pipeline_event(parsed, saved_id)




def load_master_data():
    load_sku_data(
        primary_sales_file=PRIMARY_SALES_FILE,
        recommended_products_file=RECOMMENDED_PRODUCTS_FILE,
    )


def fetch_emails():
    load_master_data()
    return read_unseen_replies()


def run_one_poll_cycle():
    print("=" * 70)

    try:
        emails = fetch_emails()
    except RuntimeError as exc:
        print(f"[Poller] Startup failed: {exc}")
        return

    if not emails:
        print("[Poller] No replies found")
        return

    for index, item in enumerate(emails, start=1):
        process_email(index, item)


def start_consumer_thread():
    consumer_thread = threading.Thread(
        target=start_redpanda_consumer,
        daemon=True,
    )
    consumer_thread.start()


def run_forever():
    while True:
        try:
            run_one_poll_cycle()
        except RuntimeError as exc:
            print(f"[Poller] Failed: {exc}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    print("Demand Planning Poller Started")

    start_consumer_thread()

    time.sleep(3)

    run_forever()
from pprint import pprint

from read_replies import read_unseen_replies
from save_to_postgres import save_parsed_reply

from app.services.reply_parser_service import parse_reply
from app.services.attachment_parser_service import (
    parse_excel_file,
    is_excel_attachment,
)
from app.data.sku_data import load_sku_data
from app.events.producers import emit_reply_received


PRIMARY_SALES_FILE = "sample_data/Primary_Sales.xlsx"
RECOMMENDED_PRODUCTS_FILE = "sample_data/30_Recommended_New_Products.xlsx"


def merge_attachment_items(parsed_data, attachment_items):
    if not attachment_items:
        return parsed_data

    text_items = parsed_data.get("items", [])
    final_items = list(attachment_items)
    excel_sku_ids = {
        item["sku_id"]
        for item in attachment_items
        if item.get("sku_id")
    }

    for item in text_items:
        sku_id = item.get("sku_id")
        if sku_id and sku_id not in excel_sku_ids:
            final_items.append(item)

    parsed_data["items"] = final_items
    parsed_data["reply_type"] = "demand"
    parsed_data["needs_followup"] = False
    parsed_data["notes"] = "Excel attachment used as primary source."
    parsed_data["confidence"] = max(parsed_data.get("confidence", 0), 0.95)

    return parsed_data


def load_master_data():
    print("Loading SKU master data...")
    load_sku_data(
        primary_sales_file=PRIMARY_SALES_FILE,
        recommended_products_file=RECOMMENDED_PRODUCTS_FILE
    )
    print("SKU data loaded successfully")


def parse_attachments(email):
    attachment_items = []

    for path in email.get("attachment_paths", []):
        if not is_excel_attachment(path):
            continue

        print(f"Parsing attachment: {path}")

        try:
            items = parse_excel_file(path)
            print(f"Parsed {len(items)} items from Excel")
            attachment_items.extend(items)
        except Exception as exc:
            print(f"Error parsing Excel: {exc}")

    return attachment_items


def emit_event(parsed, saved_id):
    print(
        f"Emitting ReplyReceived event → "
        f"distributor={parsed['distributor_id']} id={saved_id}"
    )

    try:
        emit_reply_received(
            distributor_id=parsed["distributor_id"],
            parsed_reply_id=saved_id
        )
        print("Event emitted to RedPanda ✓")
    except Exception as exc:
        print(f"RedPanda emit failed: {exc}")


def print_email(index, email):
    print("=" * 80)
    print(f"Processing Email #{index}")
    print("Message ID:", email["message_id"])
    print("From:", email["from_email"])
    print("Subject:", email["subject"])
    print("Body:")
    print(email["body"])
    print("Attachments:", email.get("attachment_paths", []))
    print("-" * 80)


def process_email(index, email):
    print_email(index, email)

    parsed = parse_reply(
        from_email=email["from_email"],
        body=email["body"]
    )

    attachment_items = parse_attachments(email)
    parsed = merge_attachment_items(parsed, attachment_items)

    print("Final Parsed Output:")
    pprint(parsed)

    saved_id = save_parsed_reply(
        raw_email=email,
        parsed_data=parsed
    )

    if saved_id is not None and parsed.get("reply_type") == "demand":
        emit_event(parsed, saved_id)

    if parsed.get("needs_followup"):
        print("Follow-up required for this reply.")

    print("=" * 80)


def process_all_replies():
    load_master_data()

    emails = read_unseen_replies()

    if not emails:
        print("No unread replies found.")
        return

    print(f"Found {len(emails)} email(s)")

    for index, email in enumerate(emails, start=1):
        process_email(index, email)


if __name__ == "__main__":
    process_all_replies()
from pprint import pprint

from read_replies import read_unseen_replies
from save_to_postgres import save_parsed_reply

from app.services.reply_parser_service import parse_reply
from app.services.attachment_parser_service import (
    parse_excel_file,
    is_excel_attachment,
)

from app.data.sku_data import load_sku_data


PRIMARY_SALES_FILE = "sample_data/Primary_Sales.xlsx"
RECOMMENDED_PRODUCTS_FILE = "sample_data/30_Recommended_New_Products.xlsx"


def merge_attachment_items(parsed_data, attachment_items):
    """
    Rules:
    1. If no attachment items -> keep text parsed result
    2. If attachment items exist -> Excel becomes primary source
    3. If text also has valid items, keep them only if SKU is not already in Excel
    """
    if not attachment_items:
        return parsed_data

    text_items = parsed_data.get("items", []) or []

    final_items = []
    excel_sku_ids = set()

    for item in attachment_items:
        final_items.append(item)
        if item.get("sku_id"):
            excel_sku_ids.add(item["sku_id"])

    for item in text_items:
        sku_id = item.get("sku_id")
        if sku_id and sku_id not in excel_sku_ids:
            final_items.append(item)

    parsed_data["items"] = final_items
    parsed_data["reply_type"] = "demand"
    parsed_data["needs_followup"] = False
    parsed_data["notes"] = "Excel attachment used as primary source."

    if parsed_data.get("confidence", 0) < 0.95:
        parsed_data["confidence"] = 0.95

    return parsed_data


def process_all_replies():
    print("Loading SKU master data...")

    load_sku_data(
        primary_sales_file=PRIMARY_SALES_FILE,
        recommended_products_file=RECOMMENDED_PRODUCTS_FILE
    )

    print("SKU data loaded successfully")

    emails = read_unseen_replies()

    if not emails:
        print("No unread replies found.")
        return

    print(f"Found {len(emails)} email(s)")

    for index, item in enumerate(emails, start=1):
        print("=" * 80)
        print(f"Processing Email #{index}")
        print("Message ID:", item["message_id"])
        print("From:", item["from_email"])
        print("Subject:", item["subject"])
        print("Body:")
        print(item["body"])
        print("Attachments:", item.get("attachment_paths", []))
        print("-" * 80)

        # Parse body text
        parsed = parse_reply(
            from_email=item["from_email"],
            body=item["body"]
        )

        # Parse Excel attachments
        attachment_items = []
        for attachment_path in item.get("attachment_paths", []):
            if is_excel_attachment(attachment_path):
                print(f"Parsing attachment: {attachment_path}")
                try:
                    excel_items = parse_excel_file(attachment_path)
                    print(f"Parsed {len(excel_items)} items from Excel")
                    attachment_items.extend(excel_items)
                except Exception as exc:
                    print(f"Error parsing Excel: {exc}")

        # Merge results
        parsed = merge_attachment_items(parsed, attachment_items)

        print("Final Parsed Output:")
        pprint(parsed)

        save_parsed_reply(
            raw_email=item,
            parsed_data=parsed
        )

        if parsed.get("needs_followup"):
            print("Follow-up required for this reply.")

        print("=" * 80)


if __name__ == "__main__":
    process_all_replies()
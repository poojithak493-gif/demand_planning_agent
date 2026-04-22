from read_replies import read_distributor_replies
from parse_replies import parse_reply_body
from save_to_postgres import create_table, save_demand


def process_email_replies():
    # Step 1: Ensure DB table exists
    create_table()

    # Step 2: Read distributor replies
    emails = read_distributor_replies()

    if not emails:
        print("No distributor replies to process.")
        return

    # Step 3: Process each email
    for mail in emails:
        distributor_id = mail["distributor_id"]
        distributor_email = mail["from_email"]
        body = mail["body"]

        print(f"\nProcessing email from {distributor_email} ({distributor_id})")

        # Step 4: Parse text body
        parsed_result = parse_reply_body(body)

        parsed_items = parsed_result["parsed_items"]
        unparsed_lines = parsed_result["unparsed_lines"]

        # Step 5: Save parsed items to DB
        for item in parsed_items:
            product_name = item["product_name"]
            quantity = item["quantity"]

            save_demand(
                distributor_email=distributor_email,
                product_name=product_name,
                quantity=quantity
            )

            print(f"✅ Saved: {product_name} - {quantity}")

        # Step 6: Show unparsed lines (for debugging)
        if unparsed_lines:
            print("⚠ Unparsed lines:")
            for line in unparsed_lines:
                print(f"- {line}")


if __name__ == "__main__":
    process_email_replies()
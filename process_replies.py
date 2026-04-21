import os
from read_replies import read_unseen_emails
from parse_text_reply import parse_text_demand
from parse_excel_reply import parse_excel_demand
from save_to_postgres import create_table, save_demand


def process_email_replies():
    create_table()

    emails = read_unseen_emails()

    for mail in emails:
        distributor_email = mail["from_email"]
        body = mail["body"]
        attachments = mail["attachments"]

        # Parse text body
        if body:
            parsed_text = parse_text_demand(body)
            for row in parsed_text:
                save_demand(
                    distributor_email=distributor_email,
                    product_name=row["product_name"],
                    quantity=row["quantity"]
                )
                print(f"Saved text reply data: {row}")

        # Parse Excel attachments
        for file_path in attachments:
            if file_path.lower().endswith(".xlsx"):
                df = parse_excel_demand(file_path)

                for _, row in df.iterrows():
                    product_name = str(row.get("Product_Name", "")).strip()
                    quantity = row.get("Expected_Demand", None)

                    if product_name and quantity is not None:
                        save_demand(
                            distributor_email=distributor_email,
                            product_name=product_name,
                            quantity=int(quantity)
                        )
                        print(f"Saved Excel reply data: {product_name} - {quantity}")


if __name__ == "__main__":
    process_email_replies()
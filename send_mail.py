import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

from app.services.sku_recommendation_service import get_recommended_products

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))

# Excel attachment path
DEMAND_ATTACHMENT_PATH = r"C:\Users\revan\Desktop\demand_planning_agent\DEMAND.xlsx"


def send_email(to_email, subject, body, attachment_path=None):
    if not EMAIL_ADDRESS:
        raise ValueError("EMAIL_ADDRESS is missing in .env file")

    if not EMAIL_APP_PASSWORD:
        raise ValueError("EMAIL_APP_PASSWORD is missing in .env file")

    msg = EmailMessage()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    if attachment_path:
        if not os.path.exists(attachment_path):
            raise FileNotFoundError(f"Attachment file not found: {attachment_path}")

        with open(attachment_path, "rb") as f:
            file_data = f.read()
            file_name = os.path.basename(attachment_path)

        # Proper MIME type for .xlsx
        msg.add_attachment(
            file_data,
            maintype="application",
            subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=file_name
        )

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        smtp.send_message(msg)

    print(f"✅ Email sent successfully to {to_email}")


def format_recommendations(recommended_products):
    if not recommended_products:
        return "No recommendations available."

    lines = []
    for index, product in enumerate(recommended_products, start=1):
        lines.append(f"{index}. {product}")

    return "\n".join(lines)


def build_email_body(distributor_id, recommended_products_text):
    return f"""Dear Distributor,

Greetings from Lipton Enterprises.

We are planning for the upcoming month and request you to share your expected product demand.

Your Distributor ID: {distributor_id}

Best Recommended Products:
{recommended_products_text}

Please provide the expected demand for the next month in any one of the following ways:

1. Reply directly in email text format:
Product Name - Quantity

Example:
Product A - 100
Product B - 250

2. Or fill in the attached Excel file and send it back as a reply.

Kindly ensure the details are accurate so that we can plan inventory and supply efficiently.

Thank you for your cooperation.

Best Regards,
Demand Planning Team
Lipton Enterprises
"""


if __name__ == "__main__":
    distributors = [
        {"id": "D01", "email": "revanbejagam@gmail.com"},
        {"id": "D02", "email": "rishithareddyc2002@gmail.com"},
        {"id": "D03", "email": "Saherwardi.mustafa@gmail.com"},
        {"id": "D04", "email": "lingaphani21@gmail.com"},
        {"id": "D05", "email": "poojithak493@gmail.com"},
    ]

    subject = "Demand Request for Upcoming Month"

    # Check attachment once before sending all emails
    if not os.path.exists(DEMAND_ATTACHMENT_PATH):
        raise FileNotFoundError(f"DEMAND.xlsx file not found at: {DEMAND_ATTACHMENT_PATH}")

    for distributor in distributors:
        distributor_id = distributor["id"]
        distributor_email = distributor["email"]

        try:
            recommended_products = get_recommended_products(
                distributor_id,
                graph_limit=5,
                excel_limit=5
            )
        except Exception as e:
            print(f"⚠ Could not fetch recommendations for {distributor_id}: {e}")
            recommended_products = []

        recommended_products_text = format_recommendations(recommended_products)
        body = build_email_body(distributor_id, recommended_products_text)

        try:
            send_email(
                to_email=distributor_email,
                subject=subject,
                body=body,
                attachment_path=DEMAND_ATTACHMENT_PATH
            )
        except Exception as e:
            print(f"❌ Failed to send email to {distributor_email}: {e}")
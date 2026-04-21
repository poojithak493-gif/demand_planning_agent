import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Import recommendation function from your service
# Make sure this function exists in app/services/sku_recommendation_service.py
from app.services.sku_recommendation_service import get_recommended_products

# Load .env values
load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))


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

    # Attach file only if provided
    if attachment_path:
        if not os.path.exists(attachment_path):
            raise FileNotFoundError(f"Attachment file not found: {attachment_path}")

        with open(attachment_path, "rb") as f:
            file_data = f.read()
            file_name = os.path.basename(attachment_path)

        msg.add_attachment(
            file_data,
            maintype="application",
            subtype="octet-stream",
            filename=file_name
        )

    # Send email using Gmail SMTP
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        smtp.send_message(msg)

    print(f"✅ Email sent successfully to {to_email}")


def format_recommendations(recommended_products):
    """
    Converts list of product names into numbered text for email body.
    Example:
    1. Product A
    2. Product B
    """
    if not recommended_products:
        return "No recommendations available."

    lines = []
    for index, product in enumerate(recommended_products, start=1):
        lines.append(f"{index}. {product}")

    return "\n".join(lines)


if __name__ == "__main__":

    distributors = [
        {"id": "D001", "email": "revanbejagam@gmail.com"},
        {"id": "D002", "email": "rishithareddyc2002@gmail.com"},
        {"id": "D003", "email": "Saherwardi.mustafa@gmail.com"},
        {"id": "D004", "email": "lingaphani21@gmail.com"},
        {"id": "D005", "email": "poojithak493@gmail.com"},
    ]

    # Constant subject
    subject = "Demand Request for Upcoming Month"

    for d in distributors:
        distributor_id = d["id"]
        distributor_email = d["email"]

        # Get recommended products for this distributor
        try:
            recommended_products = get_recommended_products(distributor_id)
        except Exception as e:
            print(f"⚠ Could not fetch recommendations for {distributor_id}: {e}")
            recommended_products = []

        recommended_products_text = format_recommendations(recommended_products)

        # Constant body + variable distributor ID + dynamic recommendations
        body = f"""
Dear Distributor,

Greetings from Lipton Enterprises.

We are planning for the upcoming month and request you to share your expected product demand.

Your Distributor ID: {distributor_id}

Best Recommended Products:
{recommended_products_text}

Please provide the expected demand for the next month in the following format:

Product Name - Quantity

Example:
Product A - 100
Product B - 250

Kindly ensure the details are accurate so that we can plan inventory and supply efficiently.

Thank you for your cooperation.

Best Regards,
Demand Planning Team
Lipton Enterprises
"""

        send_email(
            to_email=distributor_email,
            subject=subject,
            body=body,
            attachment_path=None
        )
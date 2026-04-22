import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))

ATTACHMENT_FILE = "DEMAND.xlsx"


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


def get_dummy_recommendations(distributor_id):
    demo_data = {
        "D01": ["Beng Beng Wafer", "Malkist Cheese", "Product A", "Product B", "Product C"],
        "D02": ["Malkist Cheese", "Product D", "Product E", "Product F", "Product G"],
        "D03": ["Beng Beng Wafer", "Product H", "Product I", "Product J", "Product K"],
        "D04": ["Product L", "Product M", "Product N", "Product O", "Product P"],
        "D05": ["Product Q", "Product R", "Product S", "Product T", "Product U"],
    }
    return demo_data.get(distributor_id, ["No recommendations available"])


def build_email_body(distributor_id, recommended_products_text):
    return f"""
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

You may also fill in the attached Excel file and reply back to this email.

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
    attachment_path = os.path.join(os.getcwd(), ATTACHMENT_FILE)

    for distributor in distributors:
        distributor_id = distributor["id"]
        distributor_email = distributor["email"]

        recommended_products = get_dummy_recommendations(distributor_id)
        recommended_products_text = format_recommendations(recommended_products)
        body = build_email_body(distributor_id, recommended_products_text)

        try:
            send_email(
                to_email=distributor_email,
                subject=subject,
                body=body,
                attachment_path=attachment_path
            )
        except Exception as e:
            print(f"❌ Failed to send email to {distributor_email}: {e}")
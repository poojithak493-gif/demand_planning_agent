import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings


def send_email(to_email: str, subject: str, body: str) -> dict:
    """
    Send a single email using Postal SMTP
    """

    try:
        # Create email
        msg = MIMEMultipart()
        msg["From"] = settings.POSTAL_FROM_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        # Connect to SMTP server
        with smtplib.SMTP(settings.POSTAL_SMTP_HOST, settings.POSTAL_SMTP_PORT) as server:
            server.login(settings.POSTAL_SMTP_USER, settings.POSTAL_SMTP_PASS)
            server.send_message(msg)

        return {
            "status": "success",
            "message": f"Email sent to {to_email}"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# 🚀 BONUS: Send to multiple distributors (for your project)
def send_bulk_emails(distributors: list) -> dict:
    """
    Send emails to multiple distributors
    """

    results = []

    for distributor in distributors:
        email = distributor.get("email")
        name = distributor.get("name", "Distributor")

        subject = "Demand Recommendation"

        body = f"""
Hello {name},

Based on your recent sales data, we recommend the following products:

- Product A
- Product B
- Product C

Please reply with your required quantity.

Regards,  
Demand Planning Agent
"""

        result = send_email(email, subject, body)
        results.append({
            "email": email,
            "status": result["status"]
        })

    return {
        "status": "completed",
        "results": results
    }
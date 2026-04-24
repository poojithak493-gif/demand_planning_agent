import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings


def send_email(to_email: str, subject: str, body: str) -> dict:
    try:
        msg = MIMEMultipart()
        msg["From"] = settings.EMAIL_ADDRESS
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT, context=context) as server:
            server.login(settings.EMAIL_ADDRESS, settings.EMAIL_APP_PASSWORD)
            server.send_message(msg)

        return {"status": "success", "message": f"Email sent to {to_email}"}

    except Exception as e:
        return {"status": "error", "message": str(e)}


def send_bulk_emails(distributors: list) -> dict:
    results = []
    for distributor in distributors:
        email = distributor.get("email")
        result = send_email(
            to_email=email,
            subject="Demand Request for Upcoming Month",
            body=f"Dear Distributor {distributor.get('id', '')},\n\nPlease share your demand for next month.\n\nRegards,\nDemand Planning Agent"
        )
        results.append({"email": email, "status": result["status"]})

    return {"status": "completed", "results": results}
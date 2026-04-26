import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings


def send_email(to_email: str, subject: str, body: str) -> dict:
    try:
        msg = MIMEMultipart()
        msg["From"] = settings.EMAIL_ADDRESS
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        context = ssl.create_default_context()
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED

        with smtplib.SMTP_SSL(
            host=settings.SMTP_SERVER,
            port=settings.SMTP_PORT,
            context=context
        ) as server:
            server.login(
                settings.EMAIL_ADDRESS,
                settings.EMAIL_APP_PASSWORD
            )
            server.send_message(msg)

        return {
            "status": "success",
            "message": f"Email sent to {to_email}"
        }

    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc)
        }


def send_bulk_emails(distributors: list) -> dict:
    results = []

    for distributor in distributors:
        email = distributor.get("email")

        result = send_email(
            to_email=email,
            subject="Demand Request for Upcoming Month",
            body=(
                f"Dear Distributor {distributor.get('id', '')},\n\n"
                "Please share your demand for next month.\n\n"
                "Regards,\nDemand Planning Agent"
            ),
        )

        results.append({
            "email": email,
            "status": result["status"]
        })

    return {
        "status": "completed",
        "results": results
    }
import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))


def send_email(
    to_email: str,
    subject: str,
    body: str,
    attachment_path: str | None = None,
) -> dict:
    if not EMAIL_ADDRESS:
        raise ValueError("EMAIL_ADDRESS is missing in environment configuration")
    if not EMAIL_APP_PASSWORD:
        raise ValueError("EMAIL_APP_PASSWORD is missing in environment configuration")
    if not to_email:
        raise ValueError("to_email is required")

    msg = EmailMessage()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    if attachment_path:
        if not os.path.exists(attachment_path):
            raise FileNotFoundError(f"Attachment file not found: {attachment_path}")

        with open(attachment_path, "rb") as attachment_file:
            file_data = attachment_file.read()
            file_name = os.path.basename(attachment_path)

        msg.add_attachment(
            file_data,
            maintype="application",
            subtype="octet-stream",
            filename=file_name,
        )

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        smtp.send_message(msg)

    return {
        "sent": True,
        "to_email": to_email,
        "subject": subject,
        "attachment_path": attachment_path,
    }


if __name__ == "__main__":
    # Test-only SMTP smoke path. This is not part of the FastAPI runtime flow.
    target_email = os.getenv("TEST_TO_EMAIL")
    test_subject = os.getenv("TEST_EMAIL_SUBJECT", "Demand Planning SMTP Test")
    test_body = os.getenv("TEST_EMAIL_BODY", "This is a test email from demand_planning_agent.")
    test_attachment = os.getenv("TEST_ATTACHMENT_PATH")

    if not target_email:
        raise ValueError("TEST_TO_EMAIL must be set for the send_mail.py smoke test")

    print(
        send_email(
            to_email=target_email,
            subject=test_subject,
            body=test_body,
            attachment_path=test_attachment,
        )
    )

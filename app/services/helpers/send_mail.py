import mimetypes
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
        _add_attachment(msg, attachment_path)

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        smtp.send_message(msg)

    return {
        "sent": True,
        "to_email": to_email,
        "subject": subject,
        "attachment_path": attachment_path,
    }


def _add_attachment(message: EmailMessage, attachment_path: str) -> None:
    if not os.path.exists(attachment_path):
        raise FileNotFoundError(f"Attachment file not found: {attachment_path}")

    with open(attachment_path, "rb") as attachment_file:
        file_data = attachment_file.read()

    mime_type, _ = mimetypes.guess_type(attachment_path)
    if mime_type:
        maintype, subtype = mime_type.split("/", maxsplit=1)
    else:
        maintype, subtype = "application", "octet-stream"

    message.add_attachment(
        file_data,
        maintype=maintype,
        subtype=subtype,
        filename=os.path.basename(attachment_path),
    )


if __name__ == "__main__":
    # Manual smoke test only. This block is not part of the application flow.
    manual_recipient = os.getenv("MANUAL_TEST_RECIPIENT")
    manual_subject = os.getenv("MANUAL_TEST_SUBJECT", "Manual SMTP Test")
    manual_body = os.getenv(
        "MANUAL_TEST_BODY",
        "This is a manual SMTP connectivity test from demand_planning_agent.",
    )
    manual_attachment = os.getenv("MANUAL_TEST_ATTACHMENT")

    if not manual_recipient:
        raise ValueError("Set MANUAL_TEST_RECIPIENT to run the manual SMTP test")

    result = send_email(
        to_email=manual_recipient,
        subject=manual_subject,
        body=manual_body,
        attachment_path=manual_attachment,
    )
    print(result)

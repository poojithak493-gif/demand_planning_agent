import os
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv

load_dotenv()

IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", 993))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")


def decode_mime_words(s):
    if not s:
        return ""
    decoded_parts = decode_header(s)
    parts = []
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            parts.append(part.decode(encoding or "utf-8", errors="ignore"))
        else:
            parts.append(part)
    return "".join(parts)


def extract_text_from_message(msg):
    body = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    body += payload.decode(errors="ignore")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            body += payload.decode(errors="ignore")

    return body.strip()


def clean_reply_body(body: str) -> str:
    if not body:
        return ""

    lines = body.splitlines()
    cleaned_lines = []

    stop_patterns = [
        "On ",
        "From:",
        "Subject:",
        "Sent:",
        "To:",
        "-----Original Message-----"
    ]

    for line in lines:
        stripped = line.strip()

        if any(stripped.startswith(pattern) for pattern in stop_patterns):
            break

        if stripped.startswith(">"):
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def read_unseen_replies():
    if not EMAIL_ADDRESS or not EMAIL_APP_PASSWORD:
        raise ValueError("EMAIL_ADDRESS or EMAIL_APP_PASSWORD missing in .env")

    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
    mail.select("inbox")

    status, messages = mail.search(None, '(SUBJECT "Demand Request")')

    if status != "OK":
        mail.logout()
        raise Exception("Failed to search inbox")

    email_data = []

    for num in messages[0].split():
        status, msg_data = mail.fetch(num, "(RFC822)")
        if status != "OK":
            continue

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        subject = decode_mime_words(msg.get("Subject", ""))
        from_email = decode_mime_words(msg.get("From", ""))
        raw_body = extract_text_from_message(msg)
        cleaned_body = clean_reply_body(raw_body)

        email_data.append({
            "message_id": num.decode(),
            "from_email": from_email,
            "subject": subject,
            "body": cleaned_body
        })

    mail.logout()
    return email_data


if __name__ == "__main__":
    emails = read_unseen_replies()

    if not emails:
        print("No unread replies found.")
    else:
        for index, item in enumerate(emails, start=1):
            print("=" * 60)
            print(f"Email #{index}")
            print("Message ID:", item["message_id"])
            print("From:", item["from_email"])
            print("Subject:", item["subject"])
            print("Body Preview:")
            print(item["body"][:500])
            print("=" * 60)
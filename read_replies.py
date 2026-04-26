import os
import re
import imaplib
import email
from email.header import decode_header
from email.utils import parseaddr
from dotenv import load_dotenv

load_dotenv()

IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", 993))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

ATTACHMENT_DIR = "attachments"
os.makedirs(ATTACHMENT_DIR, exist_ok=True)


def decode_mime_words(value: str) -> str:
    if not value:
        return ""

    parts = []

    for part, encoding in decode_header(value):
        if isinstance(part, bytes):
            parts.append(decode_bytes(part, encoding))
        else:
            parts.append(part)

    return "".join(parts)


def decode_bytes(part: bytes, encoding) -> str:
    try:
        return part.decode(encoding or "utf-8", errors="ignore")
    except UnicodeDecodeError:
        return part.decode("utf-8", errors="ignore")


def extract_sender_email(from_header: str) -> str:
    _, email_address = parseaddr(from_header)
    return (email_address or "").strip().lower()


def strip_html_tags(html: str) -> str:
    if not html:
        return ""

    text = html.replace("&nbsp;", " ").replace("&amp;", "&")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)

    return text.strip()


def decode_payload(payload, charset):
    try:
        return payload.decode(charset, errors="ignore")
    except UnicodeDecodeError:
        return payload.decode("utf-8", errors="ignore")


def extract_text_from_part(part):
    payload = part.get_payload(decode=True)

    if not payload:
        return ""

    charset = part.get_content_charset() or "utf-8"
    return decode_payload(payload, charset)


def append_content(part, plain_body, html_body):
    content = extract_text_from_part(part)

    if not content:
        return

    content_type = part.get_content_type()

    if content_type == "text/plain":
        plain_body.append(content)
    elif content_type == "text/html":
        html_body.append(content)


def extract_text_from_message(msg) -> str:
    plain_body = []
    html_body = []

    if msg.is_multipart():
        for part in msg.walk():
            disposition = str(part.get("Content-Disposition") or "").lower()

            if "attachment" in disposition:
                continue

            append_content(part, plain_body, html_body)

    else:
        append_content(msg, plain_body, html_body)

    plain_text = "\n".join(plain_body).strip()
    if plain_text:
        return plain_text

    html_text = "\n".join(html_body).strip()
    return strip_html_tags(html_text) if html_text else ""


def clean_reply_body(body: str) -> str:
    if not body:
        return ""

    stop_patterns = (
        "On ",
        "From:",
        "Subject:",
        "Sent:",
        "To:",
        "Cc:",
        "-----Original Message-----",
    )

    cleaned_lines = []

    for line in body.splitlines():
        stripped = line.strip()

        if stripped.startswith(stop_patterns):
            break

        if stripped.startswith(">"):
            continue

        cleaned_lines.append(line)

    cleaned_text = "\n".join(cleaned_lines).strip()
    return re.sub(r"\n{3,}", "\n\n", cleaned_text)


def save_attachments(msg, message_id: str):
    paths = []

    if not msg.is_multipart():
        return paths

    for part in msg.walk():
        disposition = str(part.get("Content-Disposition") or "").lower()

        if "attachment" not in disposition:
            continue

        filename = part.get_filename()
        if not filename:
            continue

        file_path = write_attachment(part, message_id, filename)

        if file_path:
            paths.append(file_path)

    return paths


def write_attachment(part, message_id, filename):
    decoded_filename = decode_mime_words(filename)
    safe_filename = f"{message_id}_{decoded_filename}"
    file_path = os.path.join(ATTACHMENT_DIR, safe_filename)

    payload = part.get_payload(decode=True)

    if not payload:
        return None

    with open(file_path, "wb") as file:
        file.write(payload)

    return file_path


def build_email_record(num, msg):
    message_id = num.decode()
    subject = decode_mime_words(msg.get("Subject", ""))
    from_header = decode_mime_words(msg.get("From", ""))
    from_email = extract_sender_email(from_header)

    raw_body = extract_text_from_message(msg)

    return {
        "message_id": message_id,
        "from_header": from_header,
        "from_email": from_email,
        "subject": subject,
        "raw_body": raw_body,
        "body": clean_reply_body(raw_body),
        "attachment_paths": save_attachments(msg, message_id),
    }


def fetch_messages(mail):
    status, messages = mail.search(None, '(SUBJECT "Re: Demand Request")')

    if status != "OK":
        raise RuntimeError("Failed to search inbox")

    return messages[0].split()


def read_unseen_replies():
    if not EMAIL_ADDRESS or not EMAIL_APP_PASSWORD:
        raise ValueError("EMAIL credentials missing in .env")

    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)

<<<<<<< Updated upstream
    status, messages = mail.search(None, '(SUBJECT "Demand Request")')
=======
    try:
        mail.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        mail.select("inbox")
>>>>>>> Stashed changes

        numbers = fetch_messages(mail)

        email_data = []

        for num in numbers:
            status, msg_data = mail.fetch(num, "(RFC822)")

            if status != "OK":
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            email_data.append(build_email_record(num, msg))

        return email_data

    finally:
        mail.logout()


if __name__ == "__main__":
    emails = read_unseen_replies()

    for index, item in enumerate(emails, start=1):
        print("=" * 60)
        print(f"Email #{index}")
        print("Message ID:", item["message_id"])
        print("From Email:", item["from_email"])
        print("Subject:", item["subject"])
        print("Body Preview:")
        print(item["body"][:500])
        print("Attachments:", item["attachment_paths"])
        print("=" * 60)
import email
import imaplib
import os
from email.header import decode_header
from email.utils import parsedate_to_datetime

from dotenv import load_dotenv

load_dotenv()

IMAP_HOST = os.getenv("IMAP_HOST")
IMAP_PORT = int(os.getenv("IMAP_PORT", 993))
IMAP_USERNAME = os.getenv("IMAP_USERNAME") or os.getenv("EMAIL_ADDRESS")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD") or os.getenv("EMAIL_APP_PASSWORD")
IMAP_FOLDER = os.getenv("IMAP_FOLDER", "INBOX")


def fetch_unseen_replies(
    limit: int = 10,
    simulated_messages: list[dict] | None = None,
) -> list[dict]:
    if simulated_messages is not None:
        return [_normalize_simulated_message(message) for message in simulated_messages[:limit]]

    if not IMAP_HOST or not IMAP_USERNAME or not IMAP_PASSWORD:
        return []

    mailbox = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    try:
        mailbox.login(IMAP_USERNAME, IMAP_PASSWORD)
        mailbox.select(IMAP_FOLDER)
        _, data = mailbox.search(None, "UNSEEN")
        message_ids = list(reversed(data[0].split()))[:limit]

        messages: list[dict] = []
        for message_id in message_ids:
            _, raw_message_data = mailbox.fetch(message_id, "(RFC822)")
            if not raw_message_data or raw_message_data[0] is None:
                continue

            raw_bytes = raw_message_data[0][1]
            parsed_message = email.message_from_bytes(raw_bytes)
            messages.append(
                {
                    "message_id": _decode_header_value(parsed_message.get("Message-ID")) or str(message_id),
                    "from_email": _extract_from_email(parsed_message.get("From")),
                    "subject": _decode_header_value(parsed_message.get("Subject")),
                    "raw_body": _extract_text_body(parsed_message),
                    "received_at": _parse_received_at(parsed_message.get("Date")),
                    "attachment_paths": [],
                }
            )
        return messages
    finally:
        try:
            mailbox.close()
        except Exception:
            pass
        mailbox.logout()


def _normalize_simulated_message(message: dict) -> dict:
    return {
        "message_id": message.get("message_id") or "simulated-message",
        "from_email": (message.get("from_email") or "").strip(),
        "subject": message.get("subject") or "",
        "raw_body": message.get("raw_body") or message.get("body") or "",
        "received_at": message.get("received_at"),
        "attachment_paths": message.get("attachment_paths", []),
        "distributor_code": message.get("distributor_code"),
    }


def _decode_header_value(value: str | None) -> str:
    if not value:
        return ""

    decoded_parts = decode_header(value)
    decoded_value_parts: list[str] = []
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            decoded_value_parts.append(part.decode(encoding or "utf-8", errors="ignore"))
        else:
            decoded_value_parts.append(part)
    return "".join(decoded_value_parts).strip()


def _extract_from_email(from_header: str | None) -> str:
    if not from_header:
        return ""
    if "<" in from_header and ">" in from_header:
        return from_header.split("<", maxsplit=1)[1].split(">", maxsplit=1)[0].strip()
    return from_header.strip()


def _extract_text_body(parsed_message: email.message.Message) -> str:
    if parsed_message.is_multipart():
        for part in parsed_message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition") or "")
            if content_type == "text/plain" and "attachment" not in content_disposition.lower():
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="ignore").strip()
        return ""

    payload = parsed_message.get_payload(decode=True) or b""
    charset = parsed_message.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="ignore").strip()


def _parse_received_at(date_header: str | None) -> str | None:
    if not date_header:
        return None

    try:
        return parsedate_to_datetime(date_header).isoformat()
    except Exception:
        return None

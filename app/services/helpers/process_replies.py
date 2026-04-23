import re
from datetime import datetime, timezone

from app.services.helpers.test_imap import fetch_unseen_replies

DISTRIBUTOR_CODE_PATTERN = re.compile(r"\bD\d{2,}\b", re.IGNORECASE)


def ingest_replies(
    simulated_messages: list[dict] | None = None,
    limit: int = 10,
) -> list[dict]:
    raw_messages = fetch_unseen_replies(limit=limit, simulated_messages=simulated_messages)
    return preprocess_replies(raw_messages)


def preprocess_replies(raw_messages: list[dict]) -> list[dict]:
    normalized_messages: list[dict] = []
    for raw_message in raw_messages:
        subject = (raw_message.get("subject") or "").strip()
        raw_body = (raw_message.get("raw_body") or raw_message.get("body") or "").strip()
        distributor_code = (
            raw_message.get("distributor_code")
            or _extract_distributor_code(subject)
            or _extract_distributor_code(raw_body)
        )

        normalized_messages.append(
            {
                "message_id": raw_message.get("message_id"),
                "distributor_code": distributor_code.upper() if distributor_code else None,
                "from_email": (raw_message.get("from_email") or "").strip(),
                "subject": subject,
                "raw_body": raw_body,
                "received_at": raw_message.get("received_at") or datetime.now(timezone.utc).isoformat(),
                "confirmed_by": raw_message.get("confirmed_by"),
                "notes": raw_message.get("notes"),
                "attachment_paths": raw_message.get("attachment_paths", []),
            }
        )

    return normalized_messages


def _extract_distributor_code(value: str) -> str | None:
    if not value:
        return None

    match = DISTRIBUTOR_CODE_PATTERN.search(value)
    return match.group(0) if match else None

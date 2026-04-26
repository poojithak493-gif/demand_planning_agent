from fastapi import APIRouter, HTTPException, Request, status
from confluent_kafka import Producer
from temporalio.client import Client
from json import JSONDecodeError
from typing import Optional, Dict, Any
import json
import os
import logging

from app.services.reply_parser_service import parse_reply

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Postal Webhook"])

# ==========================================================
# Configuration
# ==========================================================

REDPANDA_BROKER = os.getenv("REDPANDA_BROKER", "localhost:9092")
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")

producer = Producer({"bootstrap.servers": REDPANDA_BROKER})

EMAIL_TO_DISTRIBUTOR = {
    "revanbejagam@gmail.com": "D01",
    "rishithareddyc2002@gmail.com": "D02",
    "saherwardi.mustafa@gmail.com": "D03",
    "lingaphani21@gmail.com": "D04",
    "poojithak493@gmail.com": "D05",
}


# ==========================================================
# Helper Functions
# ==========================================================

def normalize_email(from_address: str) -> str:
    """
    Extract raw email if display name exists.
    Example:
        John <john@gmail.com> -> john@gmail.com
    """
    email = from_address.strip().lower()

    if "<" in email and ">" in email:
        email = email.split("<")[1].replace(">", "").strip()

    return email


def get_distributor_id(from_address: str) -> Optional[str]:
    email = normalize_email(from_address)
    return EMAIL_TO_DISTRIBUTOR.get(email)


def emit_reply_received(
    distributor_id: str,
    parsed_reply_id: int,
    from_address: str
) -> None:
    payload = {
        "distributor_id": distributor_id,
        "parsed_reply_id": parsed_reply_id,
        "from_address": from_address,
    }

    producer.produce(
        topic="ReplyReceived",
        key=distributor_id.encode(),
        value=json.dumps(payload).encode(),
    )

    producer.flush()

    logger.info(
        "ReplyReceived emitted for distributor %s",
        distributor_id
    )


async def signal_temporal_workflow(
    distributor_id: str,
    parsed_reply_id: int
) -> None:
    client = await Client.connect(TEMPORAL_HOST)

    workflow_id = f"demand-{distributor_id}"

    handle = client.get_workflow_handle(workflow_id)

    signal_payload = {
        "distributor_id": distributor_id,
        "parsed_reply_id": parsed_reply_id,
    }

    await handle.signal("reply_received", signal_payload)

    logger.info(
        "Temporal workflow signalled: %s",
        workflow_id
    )


def extract_payload_fields(
    payload: Dict[str, Any]
) -> Dict[str, Any]:
    return {
        "from_address": payload.get("from")
        or payload.get("from_address"),

        "subject": payload.get("subject"),

        "plain_body": payload.get("plain_body")
        or payload.get("text_body")
        or payload.get("body"),

        "message_id": payload.get("message_id"),

        "in_reply_to": payload.get("in_reply_to"),
    }


# ==========================================================
# Route
# ==========================================================

@router.post(
    "/webhook/reply",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Reply processed successfully"},
        400: {"description": "Invalid request payload"},
        422: {"description": "Distributor mapping not found"},
        500: {"description": "Internal server error"},
    },
)
async def postal_reply_webhook(request: Request):
    """
    Receives distributor reply email payload,
    parses demand data,
    emits Kafka event,
    signals Temporal workflow.
    """

    # ------------------------------------------------------
    # Parse JSON
    # ------------------------------------------------------
    try:
        payload = await request.json()

    except JSONDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload"
        ) from exc

    fields = extract_payload_fields(payload)

    from_address = fields["from_address"]
    subject = fields["subject"]
    plain_body = fields["plain_body"]
    message_id = fields["message_id"]
    in_reply_to = fields["in_reply_to"]

    if not from_address:
        raise HTTPException(
            status_code=400,
            detail="Missing from address"
        )

    # ------------------------------------------------------
    # Distributor Mapping
    # ------------------------------------------------------
    distributor_id = get_distributor_id(from_address)

    if not distributor_id:
        raise HTTPException(
            status_code=422,
            detail=f"No distributor mapped to email: {from_address}"
        )

    # ------------------------------------------------------
    # Parse Reply
    # ------------------------------------------------------
    parsed_data = parse_reply(
        from_address,
        plain_body or ""
    )

    parsed_reply_id = parsed_data.get("parsed_reply_id")

    # ------------------------------------------------------
    # Emit Kafka Event
    # ------------------------------------------------------
    redpanda_status = "skipped"

    if parsed_reply_id:
        try:
            emit_reply_received(
                distributor_id,
                parsed_reply_id,
                from_address
            )
            redpanda_status = "ReplyReceived"

        except RuntimeError as exc:
            logger.error(
                "Kafka emit failed: %s",
                exc
            )

    # ------------------------------------------------------
    # Signal Temporal Workflow
    # ------------------------------------------------------
    temporal_status = "skipped"

    if parsed_reply_id:
        try:
            await signal_temporal_workflow(
                distributor_id,
                parsed_reply_id
            )

            temporal_status = f"demand-{distributor_id}"

        except RuntimeError as exc:
            logger.error(
                "Temporal signal failed: %s",
                exc
            )

    # ------------------------------------------------------
    # Final Response
    # ------------------------------------------------------
    return {
        "status": "received",
        "distributor_id": distributor_id,
        "from_address": from_address,
        "subject": subject,
        "message_id": message_id,
        "in_reply_to": in_reply_to,
        "plain_body": plain_body,
        "parsed_data": parsed_data,
        "events_emitted": {
            "redpanda": redpanda_status,
            "temporal": temporal_status,
        },
    }

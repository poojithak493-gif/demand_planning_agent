from fastapi import APIRouter, HTTPException, Request

from app.services.reply_parser_service import ReplyParserService

router = APIRouter(prefix="", tags=["Postal Webhook"])


@router.post("/webhook/reply")
async def postal_reply_webhook(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    from_address = payload.get("from") or payload.get("from_address")
    subject = payload.get("subject")
    plain_body = payload.get("plain_body") or payload.get("text_body") or payload.get("body")
    message_id = payload.get("message_id")
    in_reply_to = payload.get("in_reply_to")

    if not from_address:
        raise HTTPException(status_code=400, detail="Missing from address")

    parser = ReplyParserService()
    parsed_data = parser.execute(plain_body or "")

    return {
        "status": "received",
        "from_address": from_address,
        "subject": subject,
        "message_id": message_id,
        "in_reply_to": in_reply_to,
        "plain_body": plain_body,
        "parsed_data": parsed_data,
    }
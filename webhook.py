"""
Webhook router for 360dialog WhatsApp incoming messages.
Handles verification (GET) and message ingestion (POST).

Full pipeline:
    Incoming message
        -> message_parser.py (extract text + sender)
        -> router.py (check keyword rules)
            -> if rule match:    responder.py (send reply) -> logger.py
            -> if bridal/complaint: handoff.py -> responder.py -> logger.py
            -> if no match:      conversation.py (get history) -> ai.py -> responder.py -> logger.py
"""

from __future__ import annotations

import logging
from collections import OrderedDict
from threading import Lock

from fastapi import APIRouter, Query, Request, Response, status

from ai import get_ai_reply
from config import WEBHOOK_VERIFY_TOKEN
from conversation import add_exchange, get_history
from handoff import escalate_to_staff
from logger import log_conversation
from message_parser import ParsedMessage, parse_message
from responder import send_text_message
from router import route_message

logger = logging.getLogger("fabs_chatbot.webhook")

router = APIRouter(prefix="/webhook", tags=["webhook"])

# ── Duplicate detection (thread-safe bounded set) ───────────────────────
_MAX_SEEN_IDS: int = 100
_seen_ids: OrderedDict[str, None] = OrderedDict()
_seen_lock = Lock()


def _is_duplicate(message_id: str) -> bool:
    """
    Check whether a message ID has been processed recently.
    Uses an OrderedDict as a bounded LRU set capped at _MAX_SEEN_IDS.
    """
    with _seen_lock:
        if message_id in _seen_ids:
            return True
        _seen_ids[message_id] = None
        if len(_seen_ids) > _MAX_SEEN_IDS:
            _seen_ids.popitem(last=False)  # Evict oldest
        return False


# ── Non-text polite rejection message ───────────────────────────────────
NON_TEXT_REPLY = (
    "Sorry, I can only read text messages right now. "
    "Please send your query as a text message. \U0001f60a"
)


# ─────────────────────────────────────────────────────────────────────────
# GET  /webhook  -- Verification handshake
# ─────────────────────────────────────────────────────────────────────────
@router.get("")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
) -> Response:
    """
    360dialog (and Meta-compatible) webhook verification.
    Echoes back hub.challenge if the token matches.
    """
    if hub_mode == "subscribe" and hub_verify_token == WEBHOOK_VERIFY_TOKEN:
        logger.info("Webhook verified successfully.")
        return Response(content=hub_challenge, media_type="text/plain")

    logger.warning(
        "Webhook verification failed. mode=%s token=%s",
        hub_mode,
        hub_verify_token,
    )
    return Response(
        content="Verification failed",
        status_code=status.HTTP_403_FORBIDDEN,
    )


# ─────────────────────────────────────────────────────────────────────────
# POST /webhook  -- Incoming messages
# ─────────────────────────────────────────────────────────────────────────
@router.post("", status_code=status.HTTP_200_OK)
async def receive_message(request: Request) -> dict:
    """
    Receive an incoming WhatsApp message from 360dialog.

    Flow:
    1. Parse the payload.
    2. Reject duplicates.
    3. If non-text -> reply with polite rejection.
    4. If text -> route through: keyword rules -> handoff -> AI.
    5. Log every exchange to Google Sheets.

    Always returns 200 to prevent 360dialog from retrying.
    """
    try:
        payload = await request.json()
    except Exception:
        logger.error("Failed to parse webhook payload as JSON.")
        return {"status": "error", "detail": "Invalid JSON"}

    parsed: ParsedMessage | None = parse_message(payload)

    # Payload contained no actionable message (e.g. delivery receipt)
    if parsed is None:
        return {"status": "ok", "detail": "No message to process"}

    # ── Duplicate guard ─────────────────────────────────────────────
    if _is_duplicate(parsed.message_id):
        logger.info(
            "Duplicate message %s from %s -- skipping.",
            parsed.message_id,
            parsed.sender_phone,
        )
        return {"status": "ok", "detail": "Duplicate ignored"}

    # ── Non-text message handling ───────────────────────────────────
    if not parsed.is_text:
        logger.info(
            "Non-text message (%s) from %s -- sending polite rejection.",
            parsed.message_type,
            parsed.sender_phone,
        )
        await send_text_message(parsed.sender_phone, NON_TEXT_REPLY)
        log_conversation(
            customer_phone=parsed.sender_phone,
            customer_message=f"[{parsed.message_type} message]",
            bot_reply=NON_TEXT_REPLY,
            reply_type="rule",
        )
        return {"status": "ok", "detail": "Non-text handled"}

    # ── Text message pipeline ──────────────────────────────────────
    bot_reply, reply_type = await _process_text_message(parsed)

    # Send the reply
    await send_text_message(parsed.sender_phone, bot_reply)

    # Store in conversation history (for future AI context)
    add_exchange(parsed.sender_phone, parsed.message_text, bot_reply)

    # Log to Google Sheets
    log_conversation(
        customer_phone=parsed.sender_phone,
        customer_message=parsed.message_text,
        bot_reply=bot_reply,
        reply_type=reply_type,
    )

    logger.info(
        "Replied to %s | msg_id=%s | type=%s",
        parsed.sender_phone,
        parsed.message_id,
        reply_type,
    )
    return {"status": "ok", "detail": "Message processed"}


async def _process_text_message(parsed: ParsedMessage) -> tuple[str, str]:
    """
    Route a text message through the full intelligence pipeline.

    Priority:
        1. Keyword rules (instant, no API call)
        2. Bridal/complaint handoff (notify staff)
        3. AI reply via GPT-4o-mini (with conversation context)

    Parameters
    ----------
    parsed : ParsedMessage
        The parsed incoming message.

    Returns
    -------
    tuple[str, str]
        (bot_reply, reply_type) where reply_type is "rule", "handoff", or "ai".
    """
    # Step 1: Try keyword rules
    route_type, rule_reply = route_message(parsed.message_text)

    # ── Keyword rule matched ────────────────────────────────────────
    if route_type == "rule" and rule_reply is not None:
        logger.info("Rule-based reply for %s.", parsed.sender_phone)
        return (rule_reply, "rule")

    # ── Bridal inquiry -- escalate to staff ─────────────────────────
    if route_type == "bridal":
        logger.info("Bridal handoff for %s.", parsed.sender_phone)
        customer_reply = await escalate_to_staff(
            customer_phone=parsed.sender_phone,
            customer_message=parsed.message_text,
            inquiry_type="bridal",
        )
        return (customer_reply, "handoff")

    # ── Complaint -- escalate to staff ──────────────────────────────
    if route_type == "complaint":
        logger.info("Complaint handoff for %s.", parsed.sender_phone)
        customer_reply = await escalate_to_staff(
            customer_phone=parsed.sender_phone,
            customer_message=parsed.message_text,
            inquiry_type="complaint",
        )
        return (customer_reply, "handoff")

    # ── No rule matched -- fall through to AI ───────────────────────
    logger.info("AI reply for %s (no keyword match).", parsed.sender_phone)
    history = get_history(parsed.sender_phone)
    ai_reply = await get_ai_reply(
        user_message=parsed.message_text,
        conversation_history=history,
    )
    return (ai_reply, "ai")

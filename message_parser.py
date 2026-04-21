"""
Message parser for 360dialog WhatsApp webhook payloads.
Extracts structured data from raw JSON payloads.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class ParsedMessage:
    """Immutable representation of a parsed incoming WhatsApp message."""

    sender_phone: str       # E.164 phone number without '+', e.g. "923001234567"
    message_id: str         # Unique 360dialog message ID, e.g. "wamid.xxxxx"
    timestamp: str          # Unix timestamp as string
    message_text: str       # The actual text content (empty string for non-text)
    message_type: str       # "text", "image", "audio", "sticker", "video", etc.
    is_text: bool           # Convenience flag


def parse_message(payload: dict) -> Optional[ParsedMessage]:
    """
    Parse a single message from the Meta Cloud API webhook payload.
    Meta wraps messages inside: entry[0] -> changes[0] -> value -> messages[0]
    """
    # Extract the 'value' object from the Meta structure
    entry = payload.get("entry", [])
    if not entry or not isinstance(entry, list):
        return None
    
    changes = entry[0].get("changes", [])
    if not changes or not isinstance(changes, list):
        return None
        
    value = changes[0].get("value", {})
    if not value or not isinstance(value, dict):
        return None

    # Now we find the actual messages array
    messages = value.get("messages")
    if not messages or not isinstance(messages, list):
        return None

    msg = messages[0]

    sender_phone: str = msg.get("from", "")
    message_id: str = msg.get("id", "")
    timestamp: str = msg.get("timestamp", "")
    message_type: str = msg.get("type", "unknown")

    # Extract text body (only present for type == "text")
    text_obj = msg.get("text")
    message_text = text_obj.get("body", "") if isinstance(text_obj, dict) else ""

    is_text = message_type == "text" and bool(message_text)

    return ParsedMessage(
        sender_phone=sender_phone,
        message_id=message_id,
        timestamp=timestamp,
        message_text=message_text,
        message_type=message_type,
        is_text=is_text,
    )

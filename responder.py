"""
Responder module for sending replies via the Meta WhatsApp Cloud API.
Includes retry logic and structured error handling.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import httpx

from config import WHATSAPP_API_KEY, WHATSAPP_API_URL

logger = logging.getLogger("fabs_chatbot.responder")

# ── Constants ───────────────────────────────────────────────────────────
MAX_RETRIES: int = 2
RETRY_DELAY_SECONDS: float = 1.5
REQUEST_TIMEOUT_SECONDS: float = 15.0


async def send_text_message(
    to_phone: str,
    message_text: str,
    *,
    max_retries: int = MAX_RETRIES,
) -> Optional[dict]:
    """
    Send a text reply to a WhatsApp user via the Meta Cloud API.
    """
    headers = {
        "Authorization": f"Bearer {WHATSAPP_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_phone,
        "type": "text",
        "text": {"body": message_text},
    }

    last_error: Optional[Exception] = None

    for attempt in range(1, max_retries + 2):
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    WHATSAPP_API_URL,
                    headers=headers,
                    json=payload,
                )

            if response.status_code in (200, 201):
                logger.info(
                    "Message sent to %s (attempt %d/%d)",
                    to_phone,
                    attempt,
                    max_retries + 1,
                )
                return response.json()

            # Non-retryable client errors (400-499 except 429)
            if 400 <= response.status_code < 500 and response.status_code != 429:
                logger.error(
                    "Non-retryable API error %d sending to %s: %s",
                    response.status_code,
                    to_phone,
                    response.text,
                )
                return None

            # Retryable: 429 (rate limit) or 5xx server errors
            logger.warning(
                "Retryable API error %d sending to %s (attempt %d/%d): %s",
                response.status_code,
                to_phone,
                attempt,
                max_retries + 1,
                response.text,
            )

        except httpx.TimeoutException as exc:
            last_error = exc
            logger.warning(
                "Timeout sending to %s (attempt %d/%d): %s",
                to_phone,
                attempt,
                max_retries + 1,
                exc,
            )

        except httpx.HTTPError as exc:
            last_error = exc
            logger.warning(
                "HTTP error sending to %s (attempt %d/%d): %s",
                to_phone,
                attempt,
                max_retries + 1,
                exc,
            )

        # Wait before retrying (skip delay after last attempt)
        if attempt <= max_retries:
            await asyncio.sleep(RETRY_DELAY_SECONDS * attempt)  # Linear back-off

    logger.error(
        "All %d attempts failed sending to %s. Last error: %s",
        max_retries + 1,
        to_phone,
        last_error,
    )
    return None

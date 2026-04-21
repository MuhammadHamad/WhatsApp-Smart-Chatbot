"""
Human handoff module for Fab's Salon chatbot.
Escalates bridal inquiries and complaints to staff via WhatsApp.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from config import HANDOFF_PHONE_NUMBER
from responder import send_text_message

logger = logging.getLogger("fabs_chatbot.handoff")

# ── Customer-facing reply after handoff ─────────────────────────────────
HANDOFF_CUSTOMER_REPLY: str = (
    "Ji! I have notified our team and someone will reach out to you shortly, "
    f"InshAllah. For urgent matters please call *+{HANDOFF_PHONE_NUMBER}* directly. \U0001f49b"
)


async def escalate_to_staff(
    customer_phone: str,
    customer_message: str,
    inquiry_type: str,
) -> str:
    """
    Escalate a conversation to human staff.

    Sends a notification to the staff WhatsApp number and returns
    the customer-facing acknowledgement reply.

    Parameters
    ----------
    customer_phone : str
        The customer's phone number (E.164 without '+').
    customer_message : str
        The customer's original message text.
    inquiry_type : str
        Either "bridal" or "complaint" — determines the notification label.

    Returns
    -------
    str
        The reply text to send back to the customer.
    """
    # Determine label for the staff notification
    label = inquiry_type.upper()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Build the staff notification message
    staff_message = (
        f"\U0001f514 *New [{label}] Inquiry*\n\n"
        f"Customer: +{customer_phone}\n"
        f"Message: {customer_message}\n"
        f"Time: {now}\n\n"
        f"Please follow up with this customer directly."
    )

    # Send notification to staff (fire-and-forget — don't block customer reply)
    result = await send_text_message(HANDOFF_PHONE_NUMBER, staff_message)

    if result is not None:
        logger.info(
            "Handoff notification sent to staff for %s inquiry from +%s.",
            label,
            customer_phone,
        )
    else:
        logger.error(
            "Failed to send handoff notification to staff for %s inquiry from +%s.",
            label,
            customer_phone,
        )

    return HANDOFF_CUSTOMER_REPLY

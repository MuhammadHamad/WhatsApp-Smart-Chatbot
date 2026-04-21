"""
Google Sheets conversation logger.
Writes one row per message exchange. Fails silently to never disrupt the main flow.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

from config import GOOGLE_CREDENTIALS_JSON, GOOGLE_SHEET_ID

logger = logging.getLogger("fabs_chatbot.logger")

# ── Google Sheets scopes ────────────────────────────────────────────────
_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# ── Lazy-initialised client (avoids startup crash if Sheets is down) ───
_worksheet: Optional[gspread.Worksheet] = None
_initialised: bool = False

# ── Column headers ──────────────────────────────────────────────────────
HEADERS = [
    "Timestamp",
    "Customer Phone",
    "Customer Message",
    "Bot Reply",
    "Reply Type",
    "Channel",
]


def _get_worksheet() -> Optional[gspread.Worksheet]:
    """
    Lazily initialise and return the target worksheet.
    Returns None on any error so the caller can bail out gracefully.
    """
    global _worksheet, _initialised

    if _initialised:
        return _worksheet

    _initialised = True

    try:
        credentials = Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_JSON,
            scopes=_SCOPES,
        )
        gc = gspread.authorize(credentials)
        spreadsheet = gc.open_by_key(GOOGLE_SHEET_ID)

        # Use the first worksheet; create headers if the sheet is empty
        _worksheet = spreadsheet.sheet1

        existing = _worksheet.row_values(1)
        if not existing:
            _worksheet.append_row(HEADERS, value_input_option="USER_ENTERED")
            logger.info("Initialised Google Sheets headers.")

        logger.info("Google Sheets logger connected successfully.")
        return _worksheet

    except Exception as exc:
        logger.error("Failed to initialise Google Sheets logger: %s", exc)
        _worksheet = None
        return None


def log_conversation(
    customer_phone: str,
    customer_message: str,
    bot_reply: str,
    reply_type: str = "rule",
    channel: str = "whatsapp",
) -> bool:
    """
    Log a single conversation turn to Google Sheets.

    Parameters
    ----------
    customer_phone : str
        The customer's phone number.
    customer_message : str
        The message the customer sent.
    bot_reply : str
        The reply the bot sent back.
    reply_type : str
        One of "rule", "ai", or "handoff".
    channel : str
        The messaging channel (default "whatsapp").

    Returns
    -------
    bool
        True if the row was written successfully, False otherwise.
    """
    try:
        ws = _get_worksheet()
        if ws is None:
            logger.warning("Google Sheets unavailable – skipping log.")
            return False

        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        row = [
            now,
            customer_phone,
            customer_message,
            bot_reply,
            reply_type,
            channel,
        ]

        ws.append_row(row, value_input_option="USER_ENTERED")
        logger.debug("Logged conversation with %s to Google Sheets.", customer_phone)
        return True

    except Exception as exc:
        # ── NEVER crash the main flow because of logging ────────────
        logger.error("Failed to log conversation to Google Sheets: %s", exc)
        return False

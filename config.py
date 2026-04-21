"""
Configuration module for Fabs Chatbot.
Loads all required environment variables from .env file with validation.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_env_path)


def _require_env(name: str) -> str:
    """Retrieve a required environment variable or exit with a clear error."""
    value = os.getenv(name)
    if not value:
        print(f"[FATAL] Missing required environment variable: {name}", file=sys.stderr)
        sys.exit(1)
    return value


# ── WhatsApp API (Meta Cloud API) ──────────────────────────────────────
# For Meta, this is the "Temporary Access Token"
WHATSAPP_API_KEY: str = _require_env("WHATSAPP_API_KEY")
# For Meta, this is the "Phone Number ID"
WHATSAPP_PHONE_NUMBER_ID: str = _require_env("WHATSAPP_PHONE_NUMBER_ID")

# ── OpenAI ─────────────────────────────────────────────────────────────
OPENAI_API_KEY: str = _require_env("OPENAI_API_KEY")

# ── Google Sheets logging ──────────────────────────────────────────────
GOOGLE_SHEET_ID: str = _require_env("GOOGLE_SHEET_ID")
GOOGLE_CREDENTIALS_JSON: str = _require_env("GOOGLE_CREDENTIALS_JSON")

# Validate credentials file exists
if not Path(GOOGLE_CREDENTIALS_JSON).is_file():
    print(
        f"[FATAL] Google credentials file not found at: {GOOGLE_CREDENTIALS_JSON}",
        file=sys.stderr,
    )
    sys.exit(1)

# ── Handoff / escalation ───────────────────────────────────────────────
HANDOFF_PHONE_NUMBER: str = _require_env("HANDOFF_PHONE_NUMBER")

# ── Webhook verification ───────────────────────────────────────────────
WEBHOOK_VERIFY_TOKEN: str = _require_env("WEBHOOK_VERIFY_TOKEN")

# ── Meta API base URL ─────────────────────────────────────────────────
# Meta uses a versioned URL format
WHATSAPP_API_URL: str = f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"

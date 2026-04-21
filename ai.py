"""
OpenAI GPT-4o-mini integration for Fab's Salon chatbot.
Generates contextual replies when no keyword rule matches.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Optional

from openai import AsyncOpenAI, APIError, APIConnectionError, RateLimitError

from config import HANDOFF_PHONE_NUMBER, OPENAI_API_KEY

logger = logging.getLogger("fabs_chatbot.ai")

# ── OpenRouter configuration ──────────────────────────────────────────
# OpenRouter uses the same library but needs a different "address"
_client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

# ── Model configuration ────────────────────────────────────────────────
# OpenRouter API keys are account-level; model selection happens per request.
MODEL: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
MAX_TOKENS: int = 300
TEMPERATURE: float = 0.7

# ── Fallback reply when OpenAI is unavailable ──────────────────────────
FALLBACK_REPLY: str = (
    "Ji, ek second! Our team will get back to you shortly. "
    f"For immediate help please call +{HANDOFF_PHONE_NUMBER} \U0001f60a"
)

# ── System prompt ──────────────────────────────────────────────────────
SYSTEM_PROMPT: str = f"""You are Zara, the digital assistant for Fab's Salon & Bridal Lounge in Islamabad, Pakistan. You are warm, professional, and knowledgeable — like a well-trained receptionist who genuinely loves the salon.

PERSONALITY:
- Friendly but efficient, never robotic
- Use occasional Pakistani conversational warmth (Ji, InshAllah)
- Never use excessive emojis (max 1-2 per message)
- Always end with one clear next step for the customer
- Keep replies under 3 short paragraphs — WhatsApp is not email
- Sound like a real salon front-desk person, not an AI bot
- Vary wording naturally; avoid repetitive templates
- Be empathetic and practical, especially for complaints or confusion

KNOWLEDGE:
- Two branches: E-11/2 (main) and I-8 Markaz (Fabs Prestige)
- Both open 7 days, 11 AM to 8 PM
- Phone: +{HANDOFF_PHONE_NUMBER}
- Services: bridal makeup, hair treatments, facials, HydraFacial, nails, body massage, keratin, rebounding
- Starting price: Rs. 6,900
- Bridal packages are custom quoted in consultation — never give a bridal price
- Key staff: Reema (haircuts), Anita (massage), Farwa and Rida (nails)
- Instagram: @fabs_salon (322K followers), @fabs_hairport

HARD RULES:
- Never quote a bridal package price — say it is discussed in consultation
- For complaints: apologise sincerely, empathise, offer to connect with management
- If you are not sure about something: say so honestly and offer to connect with a human
- Never say "As an AI language model..."
- If asked about competitor salons: politely redirect to Fabs' strengths
- Keep answers factually grounded in known salon details; do not invent
- For ambiguous requests, ask one short clarifying question before suggesting booking
- Use short, conversational WhatsApp-style replies, not long essays"""


def _is_pure_english_message(user_message: str) -> bool:
    """
    Heuristic language-style detector:
    - If message contains obvious Roman Urdu markers, treat as mixed.
    - Else if it is mostly Latin letters/common punctuation, treat as English.
    """
    text = user_message.strip().lower()
    if not text:
        return True

    roman_urdu_markers = {
        "hai", "hain", "kya", "ka", "ki", "ke", "kr", "kar", "ap", "aap",
        "mujhe", "mera", "meri", "hum", "mein", "acha", "achha", "inshaallah",
        "jazakallah", "shukriya", "pls", "plz", "yr", "yar", "han", "haan",
        "nahi", "nahin", "chahiye", "kitna", "kab", "kahan", "wala",
    }
    tokens = re.findall(r"[a-zA-Z']+", text)
    if any(token in roman_urdu_markers for token in tokens):
        return False

    allowed_pattern = re.compile(r"^[a-zA-Z0-9\s.,!?'\-:/()]+$")
    return bool(allowed_pattern.match(user_message))


def _language_style_instruction(user_message: str) -> str:
    """
    Enforce response style:
    - pure English input -> pure English output
    - otherwise -> natural Roman Urdu + English mix
    """
    if _is_pure_english_message(user_message):
        return (
            "Language policy: Reply in clear, natural English only. "
            "Do not mix Roman Urdu unless user explicitly asks."
        )
    return (
        "Language policy: Reply in natural mixed Roman Urdu + English "
        "(friendly Pakistani WhatsApp tone). Keep it human and concise."
    )


def _logic_safety_instruction(user_message: str) -> str:
    """
    Add guardrails for confusing/negated queries so the model does not
    answer the opposite of what the user asked.
    """
    text = user_message.lower()
    negation_markers = [
        "don't", "do not", "dont", "not", "n't", "without", "except",
        "other than", "nahi", "nahin",
    ]
    asks_about_exclusions = any(marker in text for marker in negation_markers)
    if not asks_about_exclusions:
        return ""

    return (
        "Logic policy: The user may be asking about exclusions or unavailable items. "
        "Do NOT answer with a generic available-services list. "
        "First address what is not offered/uncertain, then ask for exact service name if needed."
    )


async def get_ai_reply(
    user_message: str,
    conversation_history: Optional[list[dict[str, str]]] = None,
) -> str:
    """
    Generate an AI reply using GPT-4o-mini.

    Parameters
    ----------
    user_message : str
        The customer's current message.
    conversation_history : list[dict] | None
        Previous exchanges in OpenAI message format
        [{"role": "user"/"assistant", "content": "..."}].

    Returns
    -------
    str
        The AI-generated reply, or FALLBACK_REPLY on failure.
    """
    # Build the messages array
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    # Inject conversation history for context
    if conversation_history:
        messages.extend(conversation_history)

    # Add the current user message
    messages.append({"role": "system", "content": _language_style_instruction(user_message)})
    logic_instruction = _logic_safety_instruction(user_message)
    if logic_instruction:
        messages.append({"role": "system", "content": logic_instruction})
    messages.append({"role": "user", "content": user_message})

    try:
        # OpenRouter needs these extra headers to work for free
        extra_headers = {
            "HTTP-Referer": "https://fabs-salon.com",
            "X-Title": "Fabs Salon Chatbot"
        }

        response = await _client.chat.completions.create(
            model=MODEL,
            messages=messages,  # pyright: ignore[reportArgumentType]
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            extra_headers=extra_headers,
        )

        reply = response.choices[0].message.content

        if not reply or not reply.strip():
            logger.warning("OpenAI returned empty reply. Using fallback.")
            return FALLBACK_REPLY

        logger.info("AI reply generated (%d tokens used).", response.usage.total_tokens if response.usage else 0)
        return reply.strip()

    except RateLimitError as exc:
        logger.error("OpenAI rate limit hit: %s", exc)
        return FALLBACK_REPLY

    except APIConnectionError as exc:
        logger.error("OpenAI connection error: %s", exc)
        return FALLBACK_REPLY

    except APIError as exc:
        status_code = getattr(exc, "status_code", 0)
        logger.error(
            "OpenAI API error (%d) for model '%s': %s",
            status_code,
            MODEL,
            exc,
        )
        return FALLBACK_REPLY

    except Exception as exc:
        logger.error("Unexpected error calling OpenAI: %s", exc)
        return FALLBACK_REPLY

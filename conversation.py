"""
In-memory conversation history tracker.
Stores the last 4 message exchanges per user for AI context.
Auto-expires entries older than 24 hours.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Optional

logger = logging.getLogger("fabs_chatbot.conversation")

# ── Constants ───────────────────────────────────────────────────────────
MAX_EXCHANGES_PER_USER: int = 4
EXPIRY_SECONDS: int = 24 * 60 * 60  # 24 hours


@dataclass
class Exchange:
    """A single user ↔ bot message pair."""

    user_message: str
    bot_reply: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class UserConversation:
    """Conversation state for a single user."""

    exchanges: list[Exchange] = field(default_factory=list)
    last_activity: float = field(default_factory=time.time)

    def add_exchange(self, user_message: str, bot_reply: str) -> None:
        """Append an exchange and trim to the most recent MAX_EXCHANGES_PER_USER."""
        self.exchanges.append(Exchange(user_message=user_message, bot_reply=bot_reply))
        self.last_activity = time.time()

        # Keep only the last N exchanges
        if len(self.exchanges) > MAX_EXCHANGES_PER_USER:
            self.exchanges = self.exchanges[-MAX_EXCHANGES_PER_USER:]

    def is_expired(self) -> bool:
        """Check if this conversation has been inactive for more than 24 hours."""
        return (time.time() - self.last_activity) > EXPIRY_SECONDS

    def to_openai_messages(self) -> list[dict[str, str]]:
        """
        Convert stored exchanges to OpenAI chat message format.

        Returns
        -------
        list[dict[str, str]]
            List of {"role": "user"/"assistant", "content": "..."} dicts.
        """
        messages: list[dict[str, str]] = []
        for ex in self.exchanges:
            messages.append({"role": "user", "content": ex.user_message})
            messages.append({"role": "assistant", "content": ex.bot_reply})
        return messages


# ── Global conversation store (thread-safe) ────────────────────────────
_conversations: dict[str, UserConversation] = {}
_lock = Lock()


def _cleanup_expired() -> None:
    """Remove all expired conversations. Called internally under lock."""
    expired_keys = [
        phone for phone, conv in _conversations.items() if conv.is_expired()
    ]
    for key in expired_keys:
        del _conversations[key]

    if expired_keys:
        logger.info("Cleaned up %d expired conversation(s).", len(expired_keys))


def get_history(phone: str) -> list[dict[str, str]]:
    """
    Get conversation history for a user in OpenAI message format.

    Parameters
    ----------
    phone : str
        The customer's phone number (key).

    Returns
    -------
    list[dict[str, str]]
        List of role/content dicts for the OpenAI API.
        Empty list if no history exists.
    """
    with _lock:
        _cleanup_expired()
        conv = _conversations.get(phone)
        if conv is None or conv.is_expired():
            return []
        return conv.to_openai_messages()


def add_exchange(phone: str, user_message: str, bot_reply: str) -> None:
    """
    Record a new message exchange for a user.

    Parameters
    ----------
    phone : str
        The customer's phone number (key).
    user_message : str
        What the customer said.
    bot_reply : str
        What the bot replied.
    """
    with _lock:
        _cleanup_expired()
        if phone not in _conversations:
            _conversations[phone] = UserConversation()
        _conversations[phone].add_exchange(user_message, bot_reply)
        logger.debug(
            "Stored exchange for %s (%d total).",
            phone,
            len(_conversations[phone].exchanges),
        )


def get_active_count() -> int:
    """Return the number of active (non-expired) conversations."""
    with _lock:
        _cleanup_expired()
        return len(_conversations)

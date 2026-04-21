"""
Rule-based keyword matching engine for Fab's Salon chatbot.
Runs BEFORE any AI call to handle common queries instantly.

Returns:
    - ("rule", reply_text)   for keyword matches
    - ("bridal", None)       for bridal-related keywords  (triggers handoff)
    - ("complaint", None)    for complaint keywords        (triggers handoff)
    - (None, None)           if no rule matched            (falls through to AI)
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from config import HANDOFF_PHONE_NUMBER

logger = logging.getLogger("fabs_chatbot.router")

# ── Keyword rule definitions ────────────────────────────────────────────
KEYWORD_RULES: dict[str, dict] = {
    "walkin_vs_appointment": {
        "keywords": [
            "walk in", "walkin", "without appointment", "without booking",
            "direct aa", "direct a sakte", "same day", "today slot",
        ],
        "reply": (
            "Yes, walk-ins are welcome when a slot is available. 😊\n\n"
            "But we strongly recommend booking first to avoid waiting, especially on weekends.\n\n"
            f"Please WhatsApp/call *+{HANDOFF_PHONE_NUMBER}* and we will confirm your best time."
        ),
    },
    "female_staff": {
        "keywords": [
            "female staff", "lady staff", "women staff", "ladies staff",
            "male staff", "gents staff", "who will do service",
        ],
        "reply": (
            "Our salon team is professionally trained, and we can guide you to the right stylist/therapist based on your comfort and required service.\n\n"
            f"Share your preferred service and branch, and we will arrange accordingly. You can also call *+{HANDOFF_PHONE_NUMBER}* for quick guidance."
        ),
    },
    "kids_services": {
        "keywords": [
            "kids", "kid", "child", "children", "baby", "boy haircut",
            "girl haircut", "for kids",
        ],
        "reply": (
            "Yes, we do offer selected services for kids (especially grooming/hair related), depending on age and service type.\n\n"
            f"Please share your child's age and needed service, or contact *+{HANDOFF_PHONE_NUMBER}* for a quick confirmation."
        ),
    },
    "branch_recommendation": {
        "keywords": [
            "which branch", "best branch", "e11 or i8", "e-11 or i-8",
            "where should i go", "recommended branch",
        ],
        "reply": (
            "Both branches maintain strong quality standards. 💛\n\n"
            "E-11/2 is our main branch and I-8 Markaz is Fabs Prestige. "
            "The best choice depends on your service and preferred slot.\n\n"
            f"Tell us your required service and timing, and we will recommend the best branch right away (or call *+{HANDOFF_PHONE_NUMBER}*)."
        ),
    },
    "payment_methods": {
        "keywords": [
            "payment", "pay", "card", "cash", "online payment", "transfer",
            "easypaisa", "jazzcash", "debit card", "credit card",
        ],
        "reply": (
            "Payment options can vary by branch/service and current policy.\n\n"
            f"For the latest accepted methods (cash/card/transfer), please confirm at *+{HANDOFF_PHONE_NUMBER}* before your visit."
        ),
    },
    "parking": {
        "keywords": [
            "parking", "car parking", "bike parking", "park", "parking available",
        ],
        "reply": (
            "Parking availability depends on branch location and time of day.\n\n"
            f"For smooth planning, please confirm current parking guidance on *+{HANDOFF_PHONE_NUMBER}* before arrival."
        ),
    },
    "reschedule_cancel": {
        "keywords": [
            "reschedule", "cancel appointment", "change appointment", "move appointment",
            "appointment change", "booking change", "cancel booking",
        ],
        "reply": (
            "No problem — we can help with reschedule/cancellation. 👍\n\n"
            f"Please share your booked name, number, and preferred new time on *+{HANDOFF_PHONE_NUMBER}* so the team can update it quickly."
        ),
    },
    "availability_hours": {
        "keywords": [
            "when are you not available", "when are you unavailable", "when are you closed",
            "not available timing", "unavailable timing", "off day", "closed day",
            "close timing", "closing time", "are you closed",
        ],
        "reply": (
            "We are open *7 days a week* from *11:00 AM to 8:00 PM* at both branches.\n\n"
            "So there is no weekly off-day in regular schedule. For special holiday closures, please confirm on the day at "
            f"*+{HANDOFF_PHONE_NUMBER}*."
        ),
    },
    "not_provided_services": {
        "keywords": [
            "don't provide", "do not provide", "dont provide", "not provide",
            "don't offer", "do not offer", "dont offer", "not offer",
            "services you don't", "services you do not",
            "which services not", "konsi services nahi", "kya nahi karte",
            "what you don't do", "what you do not do",
        ],
        "reply": (
            "Good question. We mainly provide salon and beauty services such as bridal/event makeup, hair, skin/facial, nails, and body care.\n\n"
            "If you are asking about a specific service that may be outside this scope, please tell us its exact name and we will confirm honestly right away.\n\n"
            f"You can also confirm instantly on *+{HANDOFF_PHONE_NUMBER}*."
        ),
    },
    "gender_services": {
        "keywords": [
            "men", "male", "gents", "gent", "boys", "women", "woman",
            "ladies", "female", "unisex", "for men", "for women",
            "just women", "only women", "only ladies",
        ],
        "reply": (
            "Great question! We serve *both women and men*.\n\n"
            "Our core focus is ladies/bridal services, and we also offer selected "
            "services for men (especially hair and grooming related).\n\n"
            f"Share what you need and we will guide you right away, or call/WhatsApp *+{HANDOFF_PHONE_NUMBER}*."
        ),
    },
    "location": {
        "keywords": [
            "location", "address", "where", "kahan", "kdr", "loc",
            "directions", "pata",
        ],
        "reply": (
            "We have two branches in Islamabad:\n\n"
            "\U0001f4cd *E-11/2 (Main Branch)*\n"
            "Nafees Mansion, F.E.C.H.S. PMCHS E-11/2\n\n"
            "\U0001f4cd *I-8 Markaz (Fabs Prestige)*\n"
            "I-8 Markaz, Islamabad\n\n"
            "Both branches are open 7 days a week, 11 AM to 8 PM. \U0001f60a"
        ),
    },
    "hours": {
        "keywords": [
            "timing", "time", "hours", "open", "close", "band", "waqt",
            "schedule", "timings", "kab",
        ],
        "reply": (
            "We are open *7 days a week* from *11:00 AM to 8:00 PM* "
            "at both our E-11/2 and I-8 Markaz branches. \U0001f550\n\n"
            "Would you like to book an appointment?"
        ),
    },
    "price": {
        "keywords": [
            "price", "rate", "cost", "kitna", "charges", "fee", "rates",
            "pricing", "how much", "kitne",
        ],
        "reply": (
            "Our services start from *Rs. 6,900*. Prices vary depending "
            "on the service and your specific requirements.\n\n"
            "For a detailed price list or to discuss your needs, "
            f"please call or WhatsApp us at *+{HANDOFF_PHONE_NUMBER}*. \U0001f49b"
        ),
    },
    "booking": {
        "keywords": [
            "book", "appointment", "slot", "available", "booking",
            "reserve", "schedule", "when", "appoint",
        ],
        "reply": (
            "To book an appointment, please call or WhatsApp us at:\n"
            f"\U0001f4de *+{HANDOFF_PHONE_NUMBER}*\n\n"
            "For bridal bookings, we recommend reaching out "
            "*at least 4-6 weeks in advance* as our slots fill up quickly! \U0001f4ab"
        ),
    },
    "services": {
        "keywords": [
            "services", "service", "offer", "what do you do", "kya",
            "treatments", "treatment", "menu",
        ],
        "reply": (
            "Here is what we offer at Fab's Salon:\n\n"
            "\U0001f484 *Bridal & Event* \u2014 Nikkah, Barat, Valima, Mehndi, Groom styling\n"
            "\U0001f487 *Hair* \u2014 Cuts, color, keratin, rebounding, Extenso, blow dry\n"
            "\u2728 *Skin & Face* \u2014 Facials, HydraFacial, waxing, polishing\n"
            "\U0001f485 *Nails & Body* \u2014 Manicure, pedicure, full body massage\n\n"
            "Would you like to know more about any specific service?"
        ),
    },
    "instagram": {
        "keywords": [
            "instagram", "insta", "ig", "social media", "follow",
        ],
        "reply": (
            "Follow us on Instagram for our latest work and transformations! \U0001f31f\n\n"
            "\U0001f4f8 @fabs_salon\n"
            "\U0001f4f8 @fabs_hairport (hair page)\n\n"
            "With 322K followers, we share our work daily!"
        ),
    },
}

# ── Escalation keywords ────────────────────────────────────────────────
BRIDAL_KEYWORDS: list[str] = [
    "bridal", "bride", "shadi", "barat", "nikkah", "valima",
    "wedding", "dulhan", "mehndi", "shaadi",
]

COMPLAINT_KEYWORDS: list[str] = [
    "complaint", "problem", "issue", "bad", "worst", "disappointed",
    "refund", "bura", "ganda", "kharab",
]


def _keyword_matches(text_lower: str, keyword: str) -> bool:
    """
    Match keywords more safely:
    - Multi-word keywords: substring match
    - Single-word keywords: whole-word match only
    Prevents false positives like 'men' matching inside 'recommend'.
    """
    kw = keyword.strip().lower()
    if not kw:
        return False
    if " " in kw:
        return kw in text_lower
    return re.search(rf"\b{re.escape(kw)}\b", text_lower) is not None


def route_message(
    message_text: str,
) -> tuple[Optional[str], Optional[str]]:
    """
    Match an incoming message against keyword rules.

    Parameters
    ----------
    message_text : str
        The customer's message text.

    Returns
    -------
    tuple[str | None, str | None]
        (reply_type, reply_text)
        - ("rule", "<reply>")     if a keyword rule matched
        - ("bridal", None)        if bridal keywords detected
        - ("complaint", None)     if complaint keywords detected
        - (None, None)            if nothing matched (fall through to AI)

    Priority order: complaints > bridal > keyword rules > None
    """
    text_lower = message_text.strip().lower()

    # 1. Check complaint keywords first (highest priority)
    for kw in COMPLAINT_KEYWORDS:
        if _keyword_matches(text_lower, kw):
            logger.info("Complaint keyword matched: '%s'", kw)
            return ("complaint", None)

    # 2. Check bridal keywords
    for kw in BRIDAL_KEYWORDS:
        if _keyword_matches(text_lower, kw):
            logger.info("Bridal keyword matched: '%s'", kw)
            return ("bridal", None)

    # 3. Check standard keyword rules (best match wins)
    best_rule_name: Optional[str] = None
    best_rule_reply: Optional[str] = None
    best_keyword: Optional[str] = None
    best_score = 0

    for rule_name, rule in KEYWORD_RULES.items():
        matched_keywords = [
            kw for kw in rule["keywords"] if _keyword_matches(text_lower, kw)
        ]
        if not matched_keywords:
            continue

        # Prefer rules with more matches and then longer (more specific) keywords
        local_score = len(matched_keywords) * 100 + max(len(kw) for kw in matched_keywords)
        if local_score > best_score:
            best_score = local_score
            best_rule_name = rule_name
            best_rule_reply = rule["reply"]
            best_keyword = max(matched_keywords, key=len)

    if best_rule_name and best_rule_reply:
        logger.info("Keyword rule matched: '%s' (rule: %s)", best_keyword, best_rule_name)
        return ("rule", best_rule_reply)

    # 4. No match — fall through to AI
    return (None, None)

"""Scam shield: spots chat messages that look like common marketplace scams.

How it works (simple on purpose):
  * RULES below is a short list. Each rule has a plain-English reason and a pattern to look for.
  * scam_warnings(text) returns the reasons that match. An empty list means "looks fine".
  * It only ever WARNS the person who RECEIVED the message. It never blocks, changes, stores or reports
    anything by itself, and staff still can't read chats because of it. Nothing is saved: the check is
    simply done again each time the chat is shown.

It is a warning, not proof: an honest message can match (for example a real link), and a clever scammer can
avoid every pattern. That is why the warning says "looks like" and tells people what to do instead.
"""

import re
import unicodedata

# (reason shown to the person, pattern). Patterns ignore upper/lower case.
RULES = [
    (
        "asks for payment by gift card or crypto",
        r"\b(gift ?cards?|(itunes|google ?play|steam|amazon|apple) (gift )?cards?|prepaid (card|voucher)"
        r"|bitcoin|btc|usdt|cryptocurrency|western union|moneygram)\b",
    ),
    (
        "asks for money before you have met or seen the item",
        r"\b(deposit|holding fee|booking fee|reservation fee)\b.{0,40}\b(first|before|upfront|up front|to (hold|reserve|secure|book|keep))\b"
        r"|\b(first|before|upfront|up front|to (hold|reserve|secure|book|keep))\b.{0,40}\b(deposit|holding fee|booking fee|reservation fee)\b"
        r"|\b(pay|send|transfer|wire)( the| me| you)?( money| payment| it| cash)? (first|upfront|up front|in advance)\b"
        r"|\b(advance|upfront|up-front) (payment|fee)\b",
    ),
    (
        "asks for or shares bank or card details",
        r"\b(bsb|iban|swift code|sort code|routing number|account (number|no|details)|acc ?(no|num|number)"
        r"|bank (details|account)|pay ?id|osko|card (number|details)|cvv|cvc|security code)\b",
    ),
    (
        "tries to take the chat or the payment off NextMove",
        r"\b(whatsapp|whats app|telegram|wechat|we chat|viber|kik|snapchat|signal app|zelle|venmo|cash ?app)\b"
        r"|\b(text|message|contact|email|reach|call) me (on|at|via|through)\b"
        r"|[\w.+-]+@[\w-]+(\.[\w-]+)+"
        r"|\bpaypal\b.{0,25}\b(friends|family|f&f|ff)\b",
    ),
    (
        "contains a link",
        r"(https?://|www\.)\S+|\b(bit\.ly|tinyurl\.com|t\.co|goo\.gl|cutt\.ly|is\.gd|rb\.gy|shorturl\.at)/\S*",
    ),
    (
        "mentions a courier or overpayment (a common scam)",
        r"\b(my|a|the|our) (courier|shipping agent|shipping company|pick ?up agent|delivery agent)\b"
        r"|\boverpa(y|id|yment|ying)\b"
        r"|\b(send|refund|return|transfer)\b.{0,15}\b(the )?(extra|difference|balance)\b",
    ),
    (
        "asks for a verification or login code",
        r"\b(verification|verify|security|login|log-in|sign-?in|one[- ]time|confirmation|sms|text message)\b.{0,15}\bcodes?\b"
        r"|\botp\b"
        r"|\b\d{1,2}[- ]digit (code|pin)\b"
        r"|\bcode (you|that you) (got|received|were sent|just got)\b"
        r"|\bcode (sent|texted|messaged) to (your|ur) (phone|mobile|number)\b",
    ),
    (
        "asks for ID documents or personal numbers",
        r"\b(passport|driver'?s? licen[cs]e|drivers? licen[cs]e|tax file number|tfn|medicare (card|number)"
        r"|(photo|picture|scan|copy) of your (id|passport|licen[cs]e|card)"
        r"|your (id|passport|licen[cs]e) (number|photo|scan))\b",
    ),
]

_COMPILED = [(reason, re.compile(pattern, re.IGNORECASE)) for reason, pattern in RULES]


def _tidy(text):
    """Make simple tricks harmless: full-width letters, invisible characters, odd spacing."""
    text = unicodedata.normalize("NFKC", text)  # "ｇｉｆｔ" becomes "gift"
    text = "".join(
        ch for ch in text if unicodedata.category(ch) != "Cf"
    )  # drop zero-width characters
    return re.sub(r"\s+", " ", text)  # new lines and runs of spaces become one space


def scam_warnings(text):
    """The reasons this message looks like a scam, as a list of short sentences (empty = looks fine)."""
    text = _tidy(text or "")
    return [reason for reason, pattern in _COMPILED if pattern.search(text)]

"""Parser helpers for P2000 Companion."""
from __future__ import annotations

import hashlib
import re
from urllib.parse import urlsplit, urlunsplit
from dataclasses import dataclass, asdict
from typing import Any


CITY_ALIASES = {
    "sgravh": "Den Haag",
    "'s-gravenhage": "Den Haag",
    "s-gravenhage": "Den Haag",
    "den haag": "Den Haag",
    "rijszh": "Rijswijk",
    "rijswijk": "Rijswijk",
    "honselersdijk": "Honselersdijk",
    "naaldwijk": "Naaldwijk",
    "de lier": "De Lier",
    "wateringen": "Wateringen",
    "monster": "Monster",
    "poeldijk": "Poeldijk",
    "delft": "Delft",
    "schipluiden": "Schipluiden",
    "maasdijk": "Maasdijk",
    "kwintsheul": "Kwintsheul",
}

PRIORITY_PATTERNS = [
    (r"\b(?:A\s*0|P\s*0|PRIO\s*0)\b", "P0"),
    (r"\b(?:A\s*1|P\s*1|PRIO\s*1)\b", "P1"),
    (r"\b(?:A\s*2|P\s*2|PRIO\s*2)\b", "P2"),
    (r"\b(?:P\s*3|PRIO\s*3)\b", "P3"),
    (r"\bB\s*1\b", "B1"),
    (r"\bB\s*2\b", "B2"),
]

SERVICE_PATTERNS = [
    (r"\b(ambulance|ambu|a\s*[012]\b|b\s*[12]\b|rapid responder|zorgambulance|medium care)\b", "ambulance"),
    (r"\b(brandweer|brand|buitenbrand|binnenbrand|middelbrand|grote brand|oms|buitenmelding|buitensluiting|bdh-|ts\b)\b", "fire"),
    (r"\b(politie|prio\s*[123]|ongeval wegvervoer|aanrijding|overval|inbraak)\b", "police"),
    (r"\b(lifeliner|lfl\d|mmt|traumaheli)\b", "mmt"),
    (r"\b(knrm|reddingboot|kustwacht)\b", "lifeboat"),
]


@dataclass
class Alert:
    """Parsed P2000 alert."""

    id: str
    title: str
    message: str
    summary: str | None
    link: str | None
    published: str | None
    city: str | None
    service: str | None
    priority: str | None
    raw_text: str
    source_feed_url: str | None = None

    def as_event_data(self) -> dict[str, Any]:
        data = asdict(self)
        data["url"] = self.link
        return data


def normalize_text(value: Any) -> str:
    """Normalize unknown value to lowercase searchable text."""
    if value is None:
        return ""
    return str(value).strip()


def parse_priority(text: str) -> str | None:
    upper = text.upper()
    for pattern, priority in PRIORITY_PATTERNS:
        if re.search(pattern, upper, flags=re.IGNORECASE):
            return priority
    return None


def normalize_service(value: Any) -> str:
    """Normalize service names to stable internal English identifiers."""
    raw = normalize_text(value).lower().strip()
    aliases = {
        "ambulance": "ambulance",
        "ambu": "ambulance",
        "brandweer": "fire",
        "brand": "fire",
        "fire": "fire",
        "politie": "police",
        "police": "police",
        "traumaheli": "mmt",
        "lifeliner": "mmt",
        "mmt": "mmt",
        "knrm": "lifeboat",
        "lifeboat": "lifeboat",
    }
    return aliases.get(raw, raw)


def parse_service(text: str) -> str | None:
    lower = text.lower()
    for pattern, service in SERVICE_PATTERNS:
        if re.search(pattern, lower, flags=re.IGNORECASE):
            return service
    return None


def normalize_city(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip(" .,:;\n\t").lower()
    return CITY_ALIASES.get(cleaned, value.strip(" .,:;\n\t"))


def parse_city(text: str, link: str | None = None) -> str | None:
    lower = text.lower()

    # URL often contains /haaglanden/<city>/...
    if link:
        match = re.search(r"/haaglanden/([^/]+)/", link.lower())
        if match:
            slug = match.group(1).replace("-", " ")
            city = normalize_city(slug)
            if city:
                return city

    # Summary often says: "... in Den Haag"
    matches = re.findall(r"\bin\s+([a-zà-ÿ'\- ]+?)(?:\s*[:.,]|$)", lower, flags=re.IGNORECASE)
    if matches:
        city = normalize_city(matches[-1])
        if city:
            return city

    for alias, city in CITY_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", lower, flags=re.IGNORECASE):
            return city

    return None


def normalize_link_for_id(link: str | None) -> str:
    """Return a stable link key for de-duplication across feeds.

    Alarmeringen.nl can publish the same alert in multiple feeds with different
    tracking query parameters, for example `utm_campaign=haaglanden` vs another
    feed campaign. If the query string is part of the id, the same alert can
    trigger twice. For de-duplication we keep scheme/netloc/path and drop query
    parameters/fragments.
    """
    if not link:
        return ""
    try:
        parts = urlsplit(link)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    except Exception:  # noqa: BLE001
        return link.split("?")[0].split("#")[0]


def normalize_for_id(value: str | None) -> str:
    """Normalize text for stable duplicate detection.

    RSS feeds can republish the same alert after a few minutes with a changed
    timestamp or minor whitespace/case differences. The event should not fire
    again for the same operational alert, so IDs must be based on stable
    content, not on the feed's published/updated timestamp.
    """
    if not value:
        return ""
    text = str(value).lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def make_id(title: str, link: str | None, published: str | None, summary: str | None = None) -> str:
    """Create a stable alert id for de-duplication.

    Prefer the normalized Alarmeringen detail-page path. Do not include
    `published`, because some feeds appear to refresh/rewrite timestamps and
    would otherwise re-trigger the same alert every few minutes. When no link
    is available, fall back to normalized title + summary.
    """
    stable_link = normalize_link_for_id(link)
    if stable_link:
        base = normalize_for_id(stable_link)
    else:
        base = f"{normalize_for_id(title)}|{normalize_for_id(summary)}"
    return hashlib.md5(base.encode("utf-8"), usedforsecurity=False).hexdigest()


def parse_entry(entry: Any, source_feed_url: str | None = None) -> Alert:
    title = normalize_text(getattr(entry, "title", None) or entry.get("title") if hasattr(entry, "get") else "")
    summary = normalize_text(getattr(entry, "summary", None) or entry.get("summary") if hasattr(entry, "get") else "")
    link = normalize_text(getattr(entry, "link", None) or entry.get("link") if hasattr(entry, "get") else "") or None
    published = normalize_text(getattr(entry, "published", None) or entry.get("published") if hasattr(entry, "get") else "") or None
    raw_text = " ".join(part for part in [title, summary] if part)

    alert_id = make_id(title, link, published, summary)

    return Alert(
        id=alert_id,
        title=title,
        message=title,
        summary=summary or None,
        link=link,
        published=published,
        city=parse_city(raw_text, link),
        service=parse_service(raw_text),
        priority=parse_priority(raw_text),
        raw_text=raw_text,
        source_feed_url=source_feed_url,
    )


def csv_to_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [part.strip() for part in str(value).split(",") if part.strip()]


def slugify_event_name(value: str) -> str:
    """Convert a monitor name to a safe Home Assistant event suffix."""
    text = normalize_for_id(value)
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text[:64] or "monitor"


def parse_telegram_message(
    text: str,
    *,
    chat_id: str,
    message_id: int,
    published: str | None = None,
) -> Alert:
    """Parse a Telegram P2000 message into the common Alert model."""
    clean_text = normalize_text(text)
    # Telegram message IDs are stable within a chat and therefore ideal for
    # duplicate detection. Prefix with the chat so multiple chats cannot clash.
    alert_id = hashlib.md5(
        f"telegram|{chat_id}|{message_id}".encode("utf-8"),
        usedforsecurity=False,
    ).hexdigest()
    summary = clean_text or None
    return Alert(
        id=alert_id,
        title=clean_text,
        message=clean_text,
        summary=summary,
        link=None,
        published=published,
        city=parse_city(clean_text),
        service=parse_service(clean_text),
        priority=parse_priority(clean_text),
        raw_text=clean_text,
        source_feed_url=f"telegram://{chat_id}",
    )

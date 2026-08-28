"""Decide if the pilgrim wants a ROUTE (travel agent), not a temple fact (RAG).

Travel does not search Qdrant.
It only borrows locations when it must go somewhere.
"""

from __future__ import annotations

import re

# Movement / how-do-I-go
_ROUTE = re.compile(
    r"\b("
    r"how to reach|how do i reach|how do we reach|"
    r"how to go|how do i go|how do we go|"
    r"how to get to|way to go|route to|"
    r"from\s+.+\s+to\s+|"
    r"to\s+.+\s+from\s+|"
    r"by\s+bus|by\s+train|by\s+car|by\s+cab|by\s+taxi|"
    r"which bus|which train|"
    r"cheapest|fastest|quickest|longest|farthest"
    r")\b",
    re.I,
)

# These stay with RAG even if the word "go" appears
_RAG_FACT = re.compile(
    r"\b("
    r"darshan|timing|timings|seva|sevas|pooja|puja|"
    r"dress\s*code|history|overview|"
    r"hotel|hotels|lodge|lodges|stay|room|rooms|"
    r"food|restaurant|restaurants|annadanam|"
    r"hospital|police|pharmacy|emergency|ambulance"
    r")\b",
    re.I,
)

_COMPARE = re.compile(
    r"\b(cheapest|cheaper|lowest cost|fastest|quickest|least time|"
    r"longest|farthest|more km|how many km)\b",
    re.I,
)
_MANY_MODES = re.compile(
    r"\b(bus|train|car|cab|taxi)\b.+\b(bus|train|car|cab|taxi)\b",
    re.I,
)


def compare_kind(query: str) -> str | None:
    """cheapest / fastest / longest — or None."""
    text = (query or "").lower()
    if re.search(r"\b(cheapest|cheaper|lowest cost)\b", text):
        return "cheapest"
    if re.search(r"\b(fastest|quickest|least time)\b", text):
        return "fastest"
    if re.search(r"\b(longest|farthest|more km|how many km)\b", text):
        return "longest"
    if _MANY_MODES.search(text) and not re.search(r"\bby\s+(bus|train|car|cab|taxi)\b", text):
        return "compare"
    return None


def parse_mode(query: str) -> str | None:
    text = (query or "").lower()
    if not text:
        return None
    # "bus or train or car" / cheapest / fastest → not one mode
    if compare_kind(text) in {"cheapest", "fastest", "longest", "compare"}:
        if not re.search(r"\bby\s+(bus|train|car|cab|taxi)\b", text):
            return None
    # Explicit "by X" wins. "Bhongir railway station by bus" is bus.
    if re.search(r"\bby\s+bus\b", text):
        return "transit"
    if re.search(r"\bby\s+train\b", text):
        return "train"
    if re.search(r"\bby\s+(car|cab|taxi)\b", text):
        return "drive"
    # Place name "railway station" is not a train request.
    if re.search(r"railway\s+station", text) and re.search(r"\bbus\b", text):
        return "transit"
    if re.search(r"\b(train)\b", text) and not re.search(r"railway\s+station", text):
        return "train"
    if re.search(r"\b(car|taxi|cab|driv(e|ing)|own vehicle)\b", text):
        return "drive"
    if re.search(r"\b(bus|tcrtc|tsrtc)\b", text):
        return "transit"
    return None


def _source_dest(query: str) -> tuple[str | None, str | None]:
    text = (query or "").strip()
    match = re.search(
        r"\bfrom\s+(.+?)\s+to\s+(.+?)(?:\s+by\b|\s+at\b|\s+for\b|$)",
        text,
        re.I,
    )
    if match:
        return match.group(1).strip(" ,."), match.group(2).strip(" ,.")
    match = re.search(
        r"\bto\s+(.+?)\s+from\s+(.+?)(?:\s+by\b|\s+at\b|$)",
        text,
        re.I,
    )
    if match:
        return match.group(2).strip(" ,."), match.group(1).strip(" ,.")
    match = re.search(r"\bfrom\s+(.+?)(?:\s+by\b|\s+at\b|$)", text, re.I)
    if match:
        bit = match.group(1).strip(" ,.")
        if bit.lower() not in {"which", "where", "here"}:
            return bit, None
    return None, None


def extract_travel_slots(query: str) -> dict:
    """Pull from / to / mode if the pilgrim already said them."""
    source = None
    destination = None
    fallback_src, fallback_dst = _source_dest(query)
    try:
        from travel.agents.intent_agent import IntentAgent

        parsed = IntentAgent().parse(query)
        if parsed.source and str(parsed.source).lower() != "unknown":
            source = parsed.source.strip()
        if parsed.destination and str(parsed.destination).lower() != "unknown":
            destination = parsed.destination.strip()
    except Exception:
        pass
    # "to Yadagirigutta from Uppal" — IntentAgent reads this backwards.
    if fallback_src and (not source or " from " in (source or "").lower()):
        source = fallback_src
    if fallback_dst and (not destination or " from " in (destination or "").lower()):
        destination = fallback_dst
    return {
        "source": source,
        "destination": destination,
        "mode": parse_mode(query),
        "compare": compare_kind(query),
    }


def is_route_query(query: str) -> bool:
    text = (query or "").strip()
    if not text:
        return False
    if _RAG_FACT.search(text) and not re.search(r"\bfrom\s+.+\s+to\b", text, re.I):
        return False
    if _COMPARE.search(text) and re.search(r"\bfrom\b|\bto\b|\breach\b", text, re.I):
        return True
    return bool(_ROUTE.search(text))

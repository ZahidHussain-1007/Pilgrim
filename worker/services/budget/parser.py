"""Fill trip-form fields from a sentence. Empty patch = not a form change."""

from __future__ import annotations

import re
from typing import Any

_BUDGET = re.compile(
    r"\b(budget|how much|cost|fare|afford|rupees?|inr|spending|expenses?)\b|₹",
    re.I,
)


def is_budget_query(query: str) -> bool:
    """Rupees / afford. Not 'cheapest way from X' (that is travel)."""
    text = (query or "").strip()
    if not text:
        return False
    if re.search(r"\b(hotel|hotels|food|restaurant)s?\s+near\b", text, re.I):
        return False
    if re.search(r"\blist hotels\b", text, re.I):
        return True
    if re.search(r"\bhotels?\b", text, re.I) and re.search(r"\b(price|prices|cost|costs|₹)\b", text, re.I):
        return True
    if re.search(r"\bon the way\b", text, re.I):
        return False
    if re.search(r"how much time|how long", text, re.I):
        return False
    # "cheapest way from X" is travel. "budget … cheapest" stays budget (guessed ₹ only).
    if re.search(r"\b(cheapest|fastest|longest)\b", text, re.I) and re.search(
        r"\b(from|to|reach|way)\b", text, re.I
    ):
        if not _BUDGET.search(text):
            return False
    return bool(_BUDGET.search(text))


def parse_budget_slots(query: str) -> dict[str, Any]:
    text = query or ""
    people = days = nights = None
    m = re.search(r"\b(\d+)\s*(?:people|persons|pax|members)\b", text, re.I)
    if m:
        people = int(m.group(1))
    m = re.search(r"\b(\d+)\s*days?\b", text, re.I)
    if m:
        days = int(m.group(1))
    m = re.search(r"\b(\d+)\s*nights?\b", text, re.I)
    if m:
        nights = int(m.group(1))
    round_trip = bool(re.search(r"\bround[\s-]*trip\b|\band back\b|\breturn trip\b", text, re.I))
    list_hotels = bool(re.search(r"\bhotels?\b", text, re.I))
    origin = None
    m = re.search(
        r"\bfrom\s+([A-Za-z][A-Za-z.\s-]{0,40}?)(?=\s+(?:round|return|and\s+back|one[\s-]*way|by|to|for|\d+|people|days?|nights?)\b|$)",
        text,
        re.I,
    )
    if m:
        origin = re.sub(r"\s+", " ", m.group(1)).strip(" .,")
        if origin.lower() in {"which", "where", "here", "the"}:
            origin = None
    return {
        "people": people,
        "days": days,
        "nights": nights,
        "round_trip": round_trip,
        "list_hotels": list_hotels,
        "origin": origin,
    }


def parse_slot_patch(query: str) -> dict[str, Any]:
    """Only fields this sentence changes. Must not wipe people/origin/round_trip."""
    text = (query or "").strip()
    if not text:
        return {}
    patch: dict[str, Any] = {}
    m = re.search(r"\b(\d+)\s*(?:people|persons|pax|members)\b", text, re.I)
    if m:
        patch["people"] = int(m.group(1))
    m = re.search(r"\b(\d+)\s*[- ]?seater\b", text, re.I)
    if m:
        patch["car_seats"] = int(m.group(1))
        patch["driver_included"] = True
        patch["passenger_capacity"] = max(int(m.group(1)) - 1, 1)
        patch["travel_mode"] = "car"
    m = re.search(r"\b(\d+)\s*passengers?\s*(?:\+|and)\s*driver\b", text, re.I)
    if m:
        patch["passenger_capacity"] = int(m.group(1))
        patch["driver_included"] = True
        patch["car_seats"] = int(m.group(1)) + 1
        patch["travel_mode"] = "car"
    m = re.search(r"\b(\d+)\s*rooms?\b", text, re.I)
    if m:
        patch["rooms"] = int(m.group(1))
    m = re.search(r"\b(\d+)\s*days?\b", text, re.I)
    if m:
        patch["days"] = int(m.group(1))
    m = re.search(r"\b(\d+)\s*nights?\b", text, re.I)
    if m:
        patch["nights"] = int(m.group(1))
    if re.search(r"\bround[\s-]*trip\b|\band back\b", text, re.I):
        patch["round_trip"] = True
    if re.search(r"\bone[\s-]*way\b", text, re.I):
        patch["round_trip"] = False
    origin = parse_budget_slots(text).get("origin")
    if origin:
        patch["origin"] = origin
    if re.search(r"\bby\s+car\b|\bown car\b", text, re.I):
        patch["travel_mode"] = "car"
    if re.search(r"\bby\s+bus\b", text, re.I):
        patch["travel_mode"] = "bus"
    return patch


def query_for_temple(query: str) -> str:
    """Drop 'from <origin>' so Warangal is not picked as the temple."""
    text = (query or "").strip()
    cut = re.sub(r"\bfrom\s+.+$", "", text, flags=re.I).strip()
    return cut or text

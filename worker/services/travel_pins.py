"""Hotel/food pins from catalog. Not RAG. Not Groq prices."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from services.travel_attractions import route_tokens, tokens

ROOT = Path(__file__).resolve().parent.parent

_PIN = re.compile(r"\b(hotel|hotels|lodge|stay|food|eat|restaurant|restaurants|lunch|dinner)\b", re.I)
_ON_WAY = re.compile(
    r"\b(on the way|along the (way|route)|en route|on this (bus|route|way)|while going)\b",
    re.I,
)


def wants_route_pins(query: str) -> bool:
    text = query or ""
    if not _PIN.search(text):
        return False
    return True


def is_on_way_followup(query: str) -> bool:
    text = query or ""
    return bool(_PIN.search(text) and _ON_WAY.search(text))


def _price(item: dict[str, Any]) -> str:
    lo = item.get("min_inr")
    hi = item.get("max_inr")
    if lo is None and hi is None:
        return "price unknown"
    if lo is not None and hi is not None and lo != hi:
        return f"₹{lo}–{hi}"
    n = lo if lo is not None else hi
    return f"₹{n}"


def _label(item: dict[str, Any]) -> str:
    return f"{item.get('name') or 'place'} ({_price(item)})"


def catalog_pins(temple_id: str, option: dict[str, Any] | None, kind: str) -> dict[str, list[str]]:
    on_way: list[str] = []
    at_end: list[str] = []
    try:
        from services.catalog import Catalog

        cat = Catalog(ROOT / "data")
        if kind == "restaurant":
            items = cat.get_restaurants(temple_id).get("items") or []
        else:
            items = cat.get_hotels(temple_id).get("items") or []
    except Exception:
        return {"on_the_way": [], "at_the_temple": []}

    route = route_tokens(option)
    for item in items:
        name = str(item.get("name") or "")
        line = _label(item)
        if route and tokens(name) & route:
            if line not in on_way:
                on_way.append(line)
        else:
            if line not in at_end:
                at_end.append(line)
    return {"on_the_way": on_way[:2], "at_the_temple": at_end[:3]}


def format_pins(hotels: dict[str, list[str]], food: dict[str, list[str]]) -> list[str]:
    lines: list[str] = []
    if hotels["on_the_way"] or food["on_the_way"]:
        bits = hotels["on_the_way"] + food["on_the_way"]
        lines.append("On this way (listed in corpus): " + "; ".join(bits[:4]))
    else:
        lines.append("On this way: no listed hotel/food in our corpus at these stops.")
    if hotels["at_the_temple"]:
        lines.append("Stay at the temple: " + "; ".join(hotels["at_the_temple"]))
    if food["at_the_temple"]:
        lines.append("Food at the temple: " + "; ".join(food["at_the_temple"]))
    return lines

"""Split nearby places into on-the-way vs at-the-temple. Corpus only. No Groq."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
TEMPLES_DIR = ROOT / "data" / "temples"

_SKIP = {
    "temple",
    "sri",
    "swamy",
    "swami",
    "fort",
    "park",
    "village",
    "bus",
    "stand",
    "road",
    "nagar",
    "from",
    "take",
    "walk",
    "drive",
    "min",
    "lord",
    "devi",
}


def tokens(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z]{4,}", (text or "").lower())
    return {w for w in words if w not in _SKIP}


def route_tokens(option: dict[str, Any] | None) -> set[str]:
    if not option:
        return set()
    blob = " ".join(option.get("steps") or [])
    blob += " " + " ".join(option.get("via") or [])
    return tokens(blob)


def split_attractions(temple: dict[str, Any], option: dict[str, Any] | None) -> dict[str, list[str]]:
    route = route_tokens(option)
    on_way: list[str] = []
    at_end: list[str] = []

    def place(name: str, force_end: bool = False) -> None:
        label = str(name).strip()
        if not label:
            return
        if label in on_way or label in at_end:
            return
        hit = bool(tokens(label) & route)
        if hit and not force_end:
            on_way.append(label)
        else:
            at_end.append(label)

    for item in temple.get("nearby_places") or []:
        place(str(item))

    dest_id = str(temple.get("temple_id") or "")
    if TEMPLES_DIR.is_dir():
        for path in sorted(TEMPLES_DIR.glob("T*.json")):
            if path.stem == dest_id:
                continue
            try:
                other = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            loc = other.get("location") or {}
            label = other.get("name") or path.stem
            village = loc.get("village") or ""
            if tokens(f"{label} {village}") & route:
                place(f"{label} ({village})" if village else str(label))

    return {"on_the_way": on_way, "at_the_temple": at_end}

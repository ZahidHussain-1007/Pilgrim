"""Stay is per ROOM. Do not multiply by people."""

from __future__ import annotations

import re
from typing import Any

from .calculations import line, money


def uniq_places(rows: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for row in rows or []:
        name = str(row.get("name") or "").strip() or "unnamed"
        key = re.sub(r"\s+", " ", name).lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def priced(rows: list[dict]) -> list[dict]:
    out = []
    for row in uniq_places(rows):
        lo = money(row.get("min_inr"))
        hi = money(row.get("max_inr"))
        if lo is None and hi is None:
            continue
        if lo is None:
            lo = hi
        if hi is None:
            hi = lo
        out.append({**row, "min_inr": min(lo, hi), "max_inr": max(lo, hi)})
    out.sort(key=lambda r: (r["min_inr"], r["max_inr"], str(r.get("name") or "")))
    return out


def stay_cost(hotels: list[dict], nights: int, rooms: int) -> dict[str, Any]:
    verified: list[dict] = []
    unknown: list[str] = []
    cheap = min(hotels, key=lambda h: h["min_inr"]) if hotels else None
    costly = max(hotels, key=lambda h: h["max_inr"]) if hotels else None
    cheap_night = cheap["min_inr"] if cheap else None
    costly_night = costly["max_inr"] if costly else None
    if nights > 0 and rooms > 0:
        if hotels:
            lo = cheap_night * rooms * nights
            hi = costly_night * rooms * nights
            verified.append(
                line("stay (catalog hotels)", "verified", lo, None, hi, f"{rooms} room(s) × {nights} night(s)")
            )
        else:
            unknown.append("stay (no priced hotel in catalog)")
    elif nights == 0:
        verified.append(line("stay", "verified", 0, 0, 0, "day trip · 0 nights"))
    overnight_min = overnight_max = None
    if hotels:
        stay_rooms = rooms if rooms > 0 else 1
        overnight_min = cheap_night * stay_rooms * max(nights, 1)
        overnight_max = costly_night * stay_rooms * max(nights, 1)
    return {
        "verified": verified,
        "unknown": unknown,
        "cheap": cheap,
        "costly": costly,
        "overnight_min": overnight_min,
        "overnight_max": overnight_max,
    }

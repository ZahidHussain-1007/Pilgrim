"""Darshan windows from temple JSON + leave-by time. No Groq. No invented hours."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parent.parent
TEMPLES_DIR = ROOT / "data" / "temples"

_WINDOW = re.compile(
    r"(\d{1,2})(?::(\d{2}))?\s*[–\-]\s*(\d{1,2})(?::(\d{2}))?\s*(AM|PM)",
    re.I,
)
_CLOCK = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", re.I)
_SARVA = re.compile(r"\bsarva\b|\bgeneral darshan\b|\b7\s*(am|:00)", re.I)


def _minutes(hour: int, minute: int, ampm: str) -> int:
    hour = int(hour)
    minute = int(minute or 0)
    tag = ampm.lower()
    if tag == "pm" and hour < 12:
        hour += 12
    if tag == "am" and hour == 12:
        hour = 0
    return hour * 60 + minute


def parse_sarva_windows(text: str) -> list[tuple[int, int]]:
    windows: list[tuple[int, int]] = []
    for match in _WINDOW.finditer(text or ""):
        start = _minutes(int(match.group(1)), int(match.group(2) or 0), match.group(5))
        end = _minutes(int(match.group(3)), int(match.group(4) or 0), match.group(5))
        if end < start:
            end += 12 * 60
        windows.append((start, end))
    return windows


def windows_from_temple(temple: dict[str, Any]) -> list[tuple[int, int]]:
    tickets = temple.get("darshan_and_tickets") or {}
    blob = " ".join(
        [
            str(tickets.get("general_darshan") or ""),
            str(tickets.get("special_darshan") or ""),
        ]
    )
    found = parse_sarva_windows(blob)
    if found:
        return found
    for row in temple.get("darshan_timings") or []:
        if not isinstance(row, dict):
            continue
        found.extend(parse_sarva_windows(str(row.get("morning") or "")))
        found.extend(parse_sarva_windows(str(row.get("evening") or "")))
    # unique
    uniq = []
    for item in found:
        if item not in uniq:
            uniq.append(item)
    return uniq


def target_from_query(query: str) -> Optional[int]:
    text = query or ""
    if not _SARVA.search(text) and not re.search(r"\bleave\b|\breach\b|\barrive\b", text, re.I):
        # still allow explicit clock + darshan
        if not re.search(r"\bdarshan\b", text, re.I):
            clocks = list(_CLOCK.finditer(text))
            if not clocks:
                return None
    clocks = list(_CLOCK.finditer(text))
    if clocks:
        match = clocks[0]
        return _minutes(int(match.group(1)), int(match.group(2) or 0), match.group(3))
    if _SARVA.search(text):
        return 7 * 60
    return None


def _fmt(total: int) -> str:
    total = total % (24 * 60)
    hour = total // 60
    minute = total % 60
    suffix = "AM" if hour < 12 else "PM"
    show = hour % 12
    if show == 0:
        show = 12
    return f"{show}:{minute:02d} {suffix}"


def next_window_after(arrive: int, windows: list[tuple[int, int]]) -> Optional[tuple[int, int]]:
    for start, end in sorted(windows):
        if arrive <= end:
            return start, end
    if windows:
        start, end = sorted(windows)[0]
        return start + 24 * 60, end + 24 * 60
    return None


def darshan_travel_advice(
    temple_id: str,
    duration_minutes: Optional[int],
    query: str = "",
    now: Optional[datetime] = None,
) -> Optional[str]:
    if duration_minutes is None:
        return None
    path = TEMPLES_DIR / f"{(temple_id or '').strip().upper()}.json"
    if not path.is_file():
        return None
    temple = json.loads(path.read_text(encoding="utf-8"))
    windows = windows_from_temple(temple)
    if not windows:
        return None

    clock = now or datetime.now()
    now_min = clock.hour * 60 + clock.minute
    arrive = now_min + int(duration_minutes)
    target = target_from_query(query)

    if target is not None:
        leave = target - int(duration_minutes)
        while leave < 0:
            leave += 24 * 60
        return (
            f"For { _fmt(target) } darshan, leave by {_fmt(leave)} "
            f"(travel ~{int(duration_minutes)} min). Confirm today's board at the temple."
        )

    window = next_window_after(arrive % (24 * 60), windows)
    if not window:
        return None
    start, end = window
    arrive_mod = arrive % (24 * 60)
    if start <= arrive_mod <= end or (start >= 24 * 60 and arrive_mod <= end):
        return (
            f"If you leave now, you should arrive around {_fmt(arrive)} "
            f"during Sarva {_fmt(start % (24*60))}–{_fmt(end % (24*60))}. Confirm today's board."
        )
    leave = start - int(duration_minutes)
    while leave < 0:
        leave += 24 * 60
    return (
        f"If you leave now you arrive around {_fmt(arrive)}, outside Sarva. "
        f"Next Sarva {_fmt(start % (24*60))}–{_fmt(end % (24*60))}: leave by {_fmt(leave)}. "
        f"Doors may be closed 3:00–4:00 PM at Yadadri. Confirm today's board."
    )

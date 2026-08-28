"""Shared money helpers. Round to nearest rupee before adding."""

from __future__ import annotations

from typing import Any


def money(value: Any) -> int | None:
    if value is None or value is False:
        return None
    if isinstance(value, bool):
        return None
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


def plus(*pairs):
    lo = hi = 0
    ok = False
    for a, b in pairs:
        if a is None and b is None:
            continue
        lo += money(a) or 0
        hi += money(b) or 0
        ok = True
    return (lo, hi) if ok else (None, None)


def sum_field(lines: list[dict], field: str) -> int:
    total = 0
    for row in lines:
        n = row.get(field)
        if n is not None:
            total += int(n)
    return total


def line(name: str, status: str, min_inr=None, expected_inr=None, max_inr=None, note: str | None = None):
    return {
        "name": name,
        "status": status,
        "min_inr": money(min_inr),
        "expected_inr": money(expected_inr),
        "max_inr": money(max_inr),
        "note": note,
    }

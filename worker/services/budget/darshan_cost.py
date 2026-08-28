"""Default trip = general darshan only. Sevas are optional, not in the total."""

from __future__ import annotations

from .calculations import line


def _is_vip(item: dict) -> bool:
    blob = f"{item.get('code') or ''} {item.get('name') or ''}".lower()
    return any(w in blob for w in ("vip", "seegra", "break", "special darshan"))


def _is_general(item: dict) -> bool:
    code = str(item.get("code") or "").lower()
    name = str(item.get("name") or "").lower()
    if _is_vip(item):
        return False
    if code in {"sarva", "general"} or "sarva" in name or "general" in name:
        return True
    if item.get("fee_inr") == 0:
        return True
    return False


def darshan_lines(catalog: dict, people: int) -> tuple[list[dict], list[str], list[dict]]:
    """Returns (default_verified, unknown, optional_not_in_total)."""
    verified: list[dict] = []
    unknown: list[str] = []
    optional: list[dict] = []
    seen: set[str] = set()
    for item in catalog.get("darshan") or []:
        fee = item.get("fee_inr")
        name = str(item.get("name") or item.get("code") or "darshan")
        key = name.lower().strip()
        if key in seen:
            continue
        seen.add(key)
        if fee is None:
            unknown.append(f"{name} fee")
            optional.append({"name": name, "fee_inr": None})
            continue
        total = int(fee) * people
        note = "from catalog · free" if int(fee) == 0 else f"₹{int(fee)}/person · catalog"
        row = line(name, "verified", total, total, total, note)
        row["unit_inr"] = int(fee)
        if _is_general(item):
            verified.append(row)
        else:
            optional.append(row)
    return verified, unknown, optional


def seva_lines(catalog: dict) -> tuple[list[dict], list[str]]:
    """Optional sevas. Never added to the default total."""
    optional: list[dict] = []
    unknown: list[str] = []
    for item in catalog.get("sevas") or []:
        fee = item.get("fee_inr")
        lo = item.get("min_inr")
        hi = item.get("max_inr")
        name = str(item.get("name") or "seva")
        if fee is not None:
            optional.append(line(name, "optional", int(fee), int(fee), int(fee), "not selected"))
        elif lo is not None or hi is not None:
            optional.append(line(name, "optional", lo, None, hi, "not selected"))
        else:
            unknown.append(f"{name} fee")
            optional.append(line(name, "optional", None, None, None, "fee unknown · not selected"))
    return optional, unknown

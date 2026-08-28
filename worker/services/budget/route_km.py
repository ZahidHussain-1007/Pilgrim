"""Ask Travel for road km. Budget does not invent distance or Palle Velugu."""

from __future__ import annotations

import re
from typing import Any, Callable

from .transport_cost import travel_facts_from_plan

_HYD = re.compile(r"hyderabad|secunderabad", re.I)


def _norm(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def origin_matches_plan(origin: str | None, plan: dict[str, Any] | None) -> bool:
    if not origin or not plan:
        return False
    src = _norm(plan.get("source") or "")
    o = _norm(origin)
    if not src or not o:
        return False
    o0 = o.split(",")[0].strip()
    s0 = src.split(",")[0].strip()
    return o in src or src in o or o0 == s0 or o0 in src or s0 in o


def km_from_plan(plan: dict[str, Any] | None) -> float | None:
    km = travel_facts_from_plan(plan).get("distance_km")
    try:
        km = float(km)
    except (TypeError, ValueError):
        return None
    if km <= 0 or km > 900:
        return None
    return km


def resolve_trip_km(
    *,
    origin: str | None,
    temple_id: str | None,
    hyd_km: float | None = None,
    travel_plan: dict[str, Any] | None = None,
    cached_km: float | None = None,
    cached_origin: str | None = None,
    cached_source: str | None = None,
    cached_lookup: str | None = None,
    drive_km_fn: Callable[[str, str], Any] | None = None,
) -> dict[str, Any]:
    """Priority: matching last route → Hyderabad catalog → Travel Agent drive km."""
    empty = {"distance_km": None, "km_source": None, "travel_plan_ok": False, "duration_minutes": None}
    origin = (origin or "").strip() or None
    tid = (temple_id or "").strip() or None

    if origin and _norm(cached_origin) == _norm(origin) and cached_km:
        try:
            km = float(cached_km)
        except (TypeError, ValueError):
            km = None
        if km and 0 < km <= 900:
            return {
                "distance_km": km,
                "km_source": cached_source or "cached",
                "travel_plan_ok": False,
                "duration_minutes": None,
            }
    if origin and _norm(cached_origin) == _norm(origin) and cached_lookup == "miss":
        return empty

    if travel_plan and tid and str(travel_plan.get("temple_id") or "") == tid:
        if origin_matches_plan(origin, travel_plan):
            km = km_from_plan(travel_plan)
            if km:
                return {
                    "distance_km": km,
                    "km_source": "last route / given km",
                    "travel_plan_ok": True,
                    "duration_minutes": None,
                }

    if origin and hyd_km is not None and _HYD.search(origin):
        try:
            km = float(hyd_km)
        except (TypeError, ValueError):
            km = None
        if km and km > 0:
            return {
                "distance_km": km,
                "km_source": "catalog (Hyderabad/Secunderabad start)",
                "travel_plan_ok": False,
                "duration_minutes": None,
            }

    if origin and tid and drive_km_fn:
        try:
            hit = drive_km_fn(tid, origin)
        except Exception:
            hit = None
        km = None
        mins = None
        if isinstance(hit, dict):
            km = hit.get("distance_km")
            mins = hit.get("duration_minutes")
        else:
            km = hit
        try:
            km = float(km) if km is not None else None
        except (TypeError, ValueError):
            km = None
        if km and 0 < km <= 900:
            return {
                "distance_km": km,
                "km_source": "Travel Agent · Google Maps drive",
                "travel_plan_ok": False,
                "duration_minutes": mins,
            }

    return empty

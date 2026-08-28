"""Canonical trip form. Receptionist fills this. Calculator only reads it."""

from __future__ import annotations

from typing import Any

from .parser import parse_budget_slots, parse_slot_patch


def _take(*vals):
    for v in vals:
        if v is not None and v != "":
            return v
    return None


def merge_form(form: dict[str, Any] | None, query: str) -> dict[str, Any]:
    """Patch only fields this sentence changes. Must not wipe people/origin/round_trip."""
    form = dict(form or {})
    slots = parse_budget_slots(query)
    patch = parse_slot_patch(query)

    if patch.get("round_trip") is not None:
        round_trip = bool(patch["round_trip"])
    elif slots.get("round_trip"):
        round_trip = True
    else:
        round_trip = bool(form.get("round_trip"))

    if patch.get("driver_included") is not None:
        driver_included = bool(patch["driver_included"])
    elif form.get("driver_included") is not None:
        driver_included = bool(form.get("driver_included"))
    else:
        driver_included = True

    rooms = _take(patch.get("rooms"), form.get("rooms"))
    if rooms is None:
        rooms = 0

    return {
        "temple_id": form.get("temple_id"),
        "people": _take(patch.get("people"), slots.get("people"), form.get("people")),
        "days": _take(patch.get("days"), slots.get("days"), form.get("days")),
        "nights": _take(patch.get("nights"), slots.get("nights"), form.get("nights")),
        "rooms": rooms,
        "origin": _take(patch.get("origin"), slots.get("origin"), form.get("origin")),
        "round_trip": round_trip,
        "car_seats": _take(patch.get("car_seats"), form.get("car_seats")),
        "passenger_capacity": _take(patch.get("passenger_capacity"), form.get("passenger_capacity")),
        "driver_included": driver_included,
        "travel_mode": _take(patch.get("travel_mode"), form.get("travel_mode")),
        "selected_sevas": list(form.get("selected_sevas") or []),
        "distance_km": form.get("distance_km"),
        "km_source": form.get("km_source"),
        "km_lookup": form.get("km_lookup"),
        "duration_minutes": form.get("duration_minutes"),
    }

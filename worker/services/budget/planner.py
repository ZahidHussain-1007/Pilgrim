"""Orchestrate catalog + transport + food + stay. No LLM."""

from __future__ import annotations

import re
from typing import Any

from .accommodation_cost import priced, stay_cost
from .assumptions import nights_of
from .calculations import money, plus, sum_field
from .catalog_slice import load_catalog_slice
from .darshan_cost import darshan_lines, seva_lines
from .food_cost import food_cost
from .parser import parse_budget_slots
from .transport_cost import transport_cost, travel_facts_from_plan
from .validation import judge


def plan_budget(payload: dict[str, Any]) -> dict[str, Any]:
    slots = parse_budget_slots(payload.get("query") or "")
    people = max(int(payload.get("people") or slots.get("people") or 1), 1)
    days = max(int(payload.get("days") or slots.get("days") or 1), 1)
    rooms = int(payload.get("rooms") or 0)
    if rooms < 0:
        rooms = 0
    if payload.get("nights") is not None:
        nights = max(int(payload["nights"]), 0)
    elif slots.get("nights") is not None:
        nights = max(int(slots["nights"]), 0)
    else:
        nights = nights_of(days)
    budget_limit = money(payload.get("budget"))
    round_trip = bool(payload.get("round_trip") or slots.get("round_trip"))
    origin = (payload.get("origin") or "").strip() or None
    list_hotels = bool(payload.get("list_hotels") or slots.get("list_hotels"))
    query = payload.get("query") or ""
    wants_cheapest = bool(re.search(r"\bcheapest\b", query, re.I) or payload.get("wants_cheapest"))

    travel = dict(payload.get("travel") or {})
    if payload.get("travel_plan"):
        facts = travel_facts_from_plan(payload.get("travel_plan"))
        facts.pop("mode_asked", None)  # last bus route must not lock the budget to bus
        travel = {**facts, **travel}
    catalog = payload.get("catalog")
    if not catalog:
        tid = payload.get("temple_id")
        catalog = load_catalog_slice(str(tid), payload.get("data_root")) if tid else {}
    catalog = catalog or {}
    mode = str(payload.get("travel_mode") or travel.get("mode_asked") or "").lower()

    hyd_km = catalog.get("road_km")
    if hyd_km is not None:
        try:
            hyd_km = float(hyd_km)
        except (TypeError, ValueError):
            hyd_km = None

    origin_given = bool(origin) or travel.get("distance_km") is not None
    distance_km = travel.get("distance_km")
    km_source = payload.get("km_source")
    if distance_km is not None:
        km_source = km_source or "last route / given km"
    elif origin and hyd_km is not None and re.search(r"hyderabad|secunderabad", origin, re.I):
        distance_km = hyd_km
        km_source = "catalog (Hyderabad/Secunderabad start)"
    if distance_km is not None:
        try:
            distance_km = float(distance_km)
        except (TypeError, ValueError):
            distance_km = None
            km_source = None
    has_km = distance_km is not None and distance_km > 0

    hotels = priced(catalog.get("hotels") or [])
    restaurants = priced(catalog.get("restaurants") or [])
    free_meals = bool(catalog.get("free_meals"))

    d_ok, d_unk, optional_darshan = darshan_lines(catalog, people)
    optional_sevas, s_unk = seva_lines(catalog)
    stay = stay_cost(hotels, nights, rooms)
    food = food_cost(catalog, people, days, restaurants, free_meals, nights=nights)
    free_meals = food["free_meals"]
    tr = transport_cost(
        people=people,
        seats=1,
        round_trip=round_trip,
        origin_given=has_km,
        distance_km=distance_km,
        hyd_km=hyd_km,
        mode=mode,
        travel=travel,
        payload=payload,
    )

    verified = d_ok + stay["verified"]
    estimated = list(tr["estimated"]) + list(food["estimated"])
    unknown = d_unk + s_unk + stay["unknown"] + tr["unknown"] + food["unknown"]

    v_min = sum_field(verified, "min_inr")
    v_max = sum_field(verified, "max_inr")
    e_min = sum_field(estimated, "min_inr")
    e_exp = sum_field(estimated, "expected_inr")
    e_max = sum_field(estimated, "max_inr")
    judged = judge(budget_limit, unknown, estimated, v_min, v_max, e_exp)

    darshan_min = sum(int(x["min_inr"]) for x in verified if "stay" not in x["name"] and x.get("min_inr") is not None)
    darshan_max = sum(int(x["max_inr"]) for x in verified if "stay" not in x["name"] and x.get("max_inr") is not None)
    temple_side = plus((darshan_min, darshan_max), (food["min_inr"], food["max_inr"]))
    day_bus = plus((darshan_min, darshan_max), (food["min_inr"], food["max_inr"]), (tr["bus_min"], tr["bus_max"])) if has_km else temple_side
    day_car = plus((darshan_min, darshan_max), (food["min_inr"], food["max_inr"]), (tr["car_min"], tr["car_max"])) if has_km else temple_side

    total_known = v_max + e_exp
    confidence_pct = 0.0 if total_known <= 0 else round(100.0 * v_max / total_known, 2)
    if not has_km:
        conf_level = "low"
    elif estimated:
        conf_level = "medium"
    else:
        conf_level = "high" if confidence_pct >= 75 else "medium"

    return {
        "currency": "INR",
        "temple_id": payload.get("temple_id"),
        "temple_name": catalog.get("temple_name") or payload.get("temple_name"),
        "input": {
            "people": people,
            "days": days,
            "nights": nights,
            "rooms": rooms,
            "budget": budget_limit,
            "mode": mode,
            "distance_km": distance_km,
            "km_source": km_source,
            "free_meals": free_meals,
            "origin": origin,
            "origin_given": origin_given,
            "has_km": has_km,
            "round_trip": round_trip,
            "list_hotels": list_hotels,
            "hyd_km": hyd_km,
            "n_cars": 1,
            "show_car": tr.get("show_car", True),
            "show_bus": tr.get("show_bus", True),
            "wants_cheapest": wants_cheapest,
            "people_assumed": payload.get("people") is None and slots.get("people") is None,
            "days_assumed": payload.get("days") is None and slots.get("days") is None,
            "selected_sevas": list(payload.get("selected_sevas") or []),
        },
        "verified": verified,
        "estimated": estimated,
        "unknown": unknown,
        "lists": {
            "hotels": hotels,
                "restaurants": restaurants,
                "paid_sevas": optional_sevas,
                "optional_darshan": optional_darshan,
        },
        "approx": {
            "day_trip_bus": {"min_inr": day_bus[0], "max_inr": day_bus[1]},
            "day_trip_car": {"min_inr": day_car[0], "max_inr": day_car[1]},
            "temple_side": {"min_inr": temple_side[0], "max_inr": temple_side[1]},
            "overnight_stay": {
                "min_inr": stay["overnight_min"] and int(stay["overnight_min"]),
                "max_inr": stay["overnight_max"] and int(stay["overnight_max"]),
            },
            "car_fuel": {"min_inr": money(tr["car_min"]), "max_inr": money(tr["car_max"])},
            "bus_guess": {"min_inr": money(tr["bus_min"]), "max_inr": money(tr["bus_max"])},
            "food": {"min_inr": food["min_inr"], "max_inr": food["max_inr"]},
            "hyd_car": tr["hyd_car"],
            "hyd_bus": tr["hyd_bus"],
        },
        "totals": {
            "verified_min": v_min,
            "verified_max": v_max,
            "estimated_min": e_min,
            "estimated_expected": e_exp,
            "estimated_max": e_max,
        },
        "budget": judged,
        "confidence": {
            "verified_percent_of_known": confidence_pct,
            "level": conf_level,
        },
    }

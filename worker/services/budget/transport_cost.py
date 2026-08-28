"""Public fare guess vs private fuel. Not equivalent. No Palle Velugu fare."""

from __future__ import annotations

import re
from typing import Any

from .assumptions import BUS_INR_PER_KM, CAR_KM_PER_LITRE, PETROL_INR_PER_LITRE
from .calculations import line, money


def travel_facts_from_plan(plan: dict[str, Any] | None) -> dict[str, Any]:
    plan = plan or {}
    mode = str(plan.get("mode") or "").lower()
    options = list(plan.get("options") or [])
    car = next((o for o in options if o.get("mode_hint") == "car"), None)
    bus = next((o for o in options if o.get("mode_hint") == "bus"), None)
    train = next((o for o in options if o.get("mode_hint") == "train"), None)

    def _km(option):
        if not option:
            return None
        try:
            return float(option.get("distance_km"))
        except (TypeError, ValueError):
            return None

    distance_km = _km(car) or _km(bus) or _km(train)
    numbered = False
    for option in options:
        if option.get("mode_hint") != "bus":
            continue
        blob = " ".join(option.get("steps") or [])
        if re.search(r"take bus\s+\d", blob, re.I):
            numbered = True
            break
    real_train = bool(plan.get("train_found")) or train is not None
    if mode in {"drive", "car"}:
        asked = "car"
    elif mode == "train":
        asked = "train"
    elif mode in {"transit", "bus"}:
        asked = "bus"
    else:
        asked = ""
    return {
        "mode_asked": asked,
        "distance_km": distance_km,
        "has_numbered_bus": numbered,
        "has_real_train": real_train,
    }


def fuel_band(km: float) -> tuple[float, float]:
    return (km / CAR_KM_PER_LITRE["min"]) * PETROL_INR_PER_LITRE, (km / CAR_KM_PER_LITRE["max"]) * PETROL_INR_PER_LITRE


def bus_band(km: float, people: int) -> tuple[float, float]:
    return BUS_INR_PER_KM["min"] * km * people, BUS_INR_PER_KM["max"] * km * people


def transport_cost(
    *,
    people: int,
    seats: int,
    round_trip: bool,
    origin_given: bool,
    distance_km: float | None,
    hyd_km: float | None,
    mode: str,
    travel: dict,
    payload: dict,
) -> dict[str, Any]:
    # Car = one vehicle. People / seater do not multiply fuel.
    n_cars = 1
    legs = 2 if round_trip else 1
    estimated: list[dict] = []
    unknown: list[str] = []
    car_min = car_max = bus_min = bus_max = None
    hyd_car = hyd_bus = None
    mode = (mode or "").lower()
    show_car = mode in {"", "car", "drive"}
    show_bus = mode in {"", "bus", "transit"}

    if travel.get("has_numbered_bus"):
        unknown.append("bus ticket (no fare in our files)")
    elif mode in {"bus", "transit"}:
        if payload.get("travel_plan") or "has_numbered_bus" in (payload.get("travel") or {}):
            unknown.append("bus ticket (travel: no numbered public bus)")
        else:
            unknown.append("bus ticket (no fare in our files)")
    if mode == "train":
        if travel.get("has_real_train"):
            unknown.append("train ticket (no fare in our files)")
        else:
            unknown.append("train ticket (travel: no real train)")

    if origin_given and distance_km and distance_km > 0:
        c0, c1 = fuel_band(distance_km)
        c0, c1 = c0 * n_cars * legs, c1 * n_cars * legs
        b0, b1 = bus_band(distance_km, people)
        bus_min, bus_max = money(b0 * legs), money(b1 * legs)
        car_min, car_max = money(c0), money(c1)
        if show_car:
            estimated.append(
                line(
                    "car fuel (guess)",
                    "estimated",
                    car_min,
                    ((car_min or 0) + (car_max or 0)) / 2,
                    car_max,
                    f"{distance_km:.0f} km × {legs} · 1 vehicle · not toll/parking",
                )
            )
        if show_bus:
            estimated.append(
                line(
                    "bus fare (guess)",
                    "estimated",
                    bus_min,
                    ((bus_min or 0) + (bus_max or 0)) / 2,
                    bus_max,
                    f"{distance_km:.0f} km × {legs} × ₹{BUS_INR_PER_KM['min']}–{BUS_INR_PER_KM['max']}/km · not a TGSRTC ticket",
                )
            )
    elif mode in {"car", "drive"}:
        unknown.append("car fuel (no distance from travel)")

    if hyd_km and hyd_km > 0 and not origin_given:
        c0, c1 = fuel_band(hyd_km)
        b0, b1 = bus_band(hyd_km, people)
        hyd_car = {"min_inr": money(c0 * n_cars), "max_inr": money(c1 * n_cars)}
        hyd_bus = {"min_inr": money(b0), "max_inr": money(b1)}

    if mode == "cab" and distance_km and distance_km > 0:
        unknown.append("cab fare (no official rate in our files)")
    unknown.append("auto / last-mile (not in catalog)")
    unknown.append("toll")
    unknown.append("parking")

    return {
        "n_cars": n_cars,
        "car_min": car_min,
        "car_max": car_max,
        "bus_min": bus_min,
        "bus_max": bus_max,
        "hyd_car": hyd_car,
        "hyd_bus": hyd_bus,
        "estimated": estimated,
        "unknown": unknown,
        "show_car": show_car,
        "show_bus": show_bus,
    }


def allowed_optimizer_modes(travel: dict[str, Any]) -> list[str]:
    allowed = ["car"]
    if travel.get("has_numbered_bus"):
        allowed.append("bus")
    if travel.get("has_real_train"):
        allowed.append("train")
    return allowed

"""Constants and occupancy. Not a shop bill."""

from __future__ import annotations

import math
from typing import Any

PETROL_INR_PER_LITRE = 116.0
CAR_KM_PER_LITRE = {"min": 20.0, "max": 15.0}  # 15–20 km/l
CAR_SEATS = 4  # total seats including driver
BUS_INR_PER_KM = {"min": 1.2, "max": 2.0}  # guess, not a TGSRTC ticket

MEAL = {
    "breakfast": (80, 150),
    "lunch": (120, 250),
    "dinner": (120, 250),
}
FOOD_GUESS_PER_PERSON_DAY = {
    "min": MEAL["breakfast"][0] + MEAL["lunch"][0] + MEAL["dinner"][0],
    "expected": 485,
    "max": MEAL["breakfast"][1] + MEAL["lunch"][1] + MEAL["dinner"][1],
}


def nights_of(days: int) -> int:
    return max(int(days) - 1, 0)


def cars_needed(people: int, seats: int) -> int:
    """seats = passenger capacity (driver already removed if it should be)."""
    return max(1, math.ceil(max(int(people), 1) / max(int(seats), 1)))


def occupancy(
    total_seats: int | None = None,
    driver_included: bool = True,
    passenger_capacity: int | None = None,
) -> dict[str, Any]:
    """N-seat car = N occupants including driver unless user said N passengers + driver."""
    if passenger_capacity is not None:
        pax = max(int(passenger_capacity), 1)
        drv = bool(driver_included)
        total = pax + (1 if drv else 0)
        return {
            "total_seats": total,
            "passenger_capacity": pax,
            "driver_included": drv,
        }
    total = max(int(total_seats if total_seats is not None else CAR_SEATS), 1)
    drv = bool(driver_included)
    pax = max(total - 1, 1) if drv else total
    return {
        "total_seats": total,
        "passenger_capacity": pax,
        "driver_included": drv,
    }

"""Temple meal vs paid meal estimate. Never treat missing as ₹0."""

from __future__ import annotations

import re
from typing import Any

from .assumptions import FOOD_GUESS_PER_PERSON_DAY, MEAL
from .calculations import line, money


def food_cost(catalog: dict, people: int, days: int, restaurants: list[dict], free_meals: bool, nights: int = 0) -> dict[str, Any]:
    # Day trip: lunch only. Overnight: breakfast+lunch+dinner.
    if nights == 0 and days <= 1:
        meal_lo = MEAL["lunch"][0] * people
        meal_hi = MEAL["lunch"][1] * people
    else:
        meal_lo = FOOD_GUESS_PER_PERSON_DAY["min"] * people * days
        meal_hi = FOOD_GUESS_PER_PERSON_DAY["max"] * people * days
    estimated: list[dict] = []
    unknown: list[str] = []
    if restaurants:
        food_min = restaurants[0]["min_inr"] * people * days
        food_max = restaurants[-1]["max_inr"] * people * days
        if food_max == 0:
            food_max = meal_hi
            unknown.append("paid restaurant ₹ not in catalog · costly side is meal guess")
        estimated.append(
            line("food (catalog + guess if needed)", "estimated", food_min, None, food_max, "not a restaurant bill")
        )
    elif free_meals:
        food_min, food_max = 0, meal_hi
        estimated.append(
            line(
                "food (annadanam + meal guess)",
                "estimated",
                food_min,
                None,
                food_max,
                "₹0 IF annadanam is serving · costly side meal guess",
            )
        )
    else:
        food_min, food_max = meal_lo, meal_hi
        estimated.append(
            line(
                "food (guess)",
                "estimated",
                food_min,
                FOOD_GUESS_PER_PERSON_DAY["expected"] * people * days,
                food_max,
                "breakfast+lunch+dinner rule · restaurant ₹ not in catalog",
            )
        )
        unknown.append("food (no catalog ₹ · meal-band estimate)")
    if not free_meals:
        free_meals = any(
            money(r.get("min_inr")) == 0 and re.search(r"annadanam|free", str(r.get("name") or ""), re.I)
            for r in (catalog.get("restaurants") or [])
        )
    return {
        "min_inr": money(food_min),
        "max_inr": money(food_max),
        "estimated": estimated,
        "unknown": unknown,
        "free_meals": free_meals,
        "paid_lo": meal_lo,
        "paid_hi": meal_hi,
    }

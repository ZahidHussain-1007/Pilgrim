"""Budget judgement. Unknown fares → cannot say within_budget."""

from __future__ import annotations

from typing import Any


def judge(budget_limit, unknown: list[str], estimated: list, v_min: int, v_max: int, e_exp: int) -> dict[str, Any]:
    important = [u for u in unknown if "bus ticket" in u or "train ticket" in u]
    can_judge = budget_limit is not None and not important
    status = None
    note = None
    if budget_limit is None:
        note = None
    elif important:
        note = "Cannot judge ₹" + str(budget_limit) + " until " + "; ".join(important) + "."
        can_judge = False
    elif estimated:
        note = (
            f"Budget ₹{budget_limit}. Known (files) ₹{v_min}–{v_max}. "
            f"Guess extra ~₹{e_exp}. Not a full bill."
        )
        can_judge = False
    elif v_max <= budget_limit:
        status = "within_known_costs"
        note = f"Known catalog costs ₹{v_min}–{v_max} fit ₹{budget_limit}."
        can_judge = True
    else:
        status = "over_known_costs"
        note = f"Known catalog costs ₹{v_min}–{v_max} already over ₹{budget_limit}."
        can_judge = True
    return {
        "limit": budget_limit,
        "can_say_within_budget": can_judge and status == "within_known_costs",
        "status": status,
        "note": note,
    }

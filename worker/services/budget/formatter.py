"""Human card. Clean CLI. No debug, no formulas, no catalog ids."""

from __future__ import annotations

from typing import Any

from .assumptions import PETROL_INR_PER_LITRE


def _rs(lo, hi) -> str:
    if lo is None and hi is None:
        return "—"
    if lo == hi:
        return f"₹{lo}"
    return f"₹{lo}–{hi}"


def _row(item: str, amount: str, status: str, widths=(18, 16, 14)) -> str:
    return f"{item:<{widths[0]}} {amount:<{widths[1]}} {status:<{widths[2]}}".rstrip()


def format_budget(card: dict[str, Any]) -> str:
    inp = card.get("input") or {}
    people = inp.get("people") or 1
    days = inp.get("days") or 1
    nights = inp.get("nights") or 0
    km = inp.get("distance_km")
    name = card.get("temple_name") or "this temple"
    lists = card.get("lists") or {}
    approx = card.get("approx") or {}
    hotels = lists.get("hotels") or []
    origin_given = bool(inp.get("origin_given"))
    round_trip = bool(inp.get("round_trip"))
    mode = str(inp.get("mode") or "").lower()
    show_car = bool(inp.get("show_car", mode in {"", "car", "drive"}))
    show_bus = bool(inp.get("show_bus", mode in {"", "bus", "transit"}))
    car = approx.get("car_fuel") or {}
    bus = approx.get("bus_guess") or {}
    ts = approx.get("temple_side") or {}
    db = approx.get("day_trip_bus") or {}
    dc = approx.get("day_trip_car") or {}
    fa = approx.get("food") or {}
    has_km = bool(inp.get("has_km") or km)
    origin_name = inp.get("origin")
    trip_word = "round trip" if round_trip else "one-way"
    origin_label = origin_name or ("given km" if origin_given else "Origin not given")

    darshan_rows = [r for r in (card.get("verified") or []) if "stay" not in r["name"]]
    n_opt = len(lists.get("paid_sevas") or []) + len(lists.get("optional_darshan") or [])
    cheap = min(hotels, key=lambda h: h["min_inr"]) if hotels else None
    costly = max(hotels, key=lambda h: h["max_inr"]) if hotels else None

    bus_pp_lo = bus_pp_hi = None
    if bus.get("min_inr") is not None and people:
        bus_pp_lo = bus["min_inr"] // people
        bus_pp_hi = bus["max_inr"] // people

    lines = [
        "TRIP BUDGET",
        "Planning estimate — not a bill",
        "",
        str(name),
        "",
        "TRIP DETAILS",
        f"• {people} people" if people != 1 else "• 1 person",
        f"• {days} day(s) · {nights} night(s)",
        f"• {origin_label} → {name}",
        f"• {trip_word.capitalize()}",
        "",
        "TEMPLE",
    ]
    if darshan_rows:
        for row in darshan_rows:
            unit = row.get("unit_inr")
            if unit is not None and people > 1:
                lines.append(f"• Darshan: {row['name']} · ₹{unit}/person · {_rs(row.get('min_inr'), row.get('max_inr'))} [VERIFIED]")
            elif row.get("min_inr") == 0 and row.get("max_inr") == 0:
                lines.append(f"• Darshan: {row['name']} · ₹0 [VERIFIED]")
            else:
                lines.append(f"• Darshan: {row['name']} · {_rs(row.get('min_inr'), row.get('max_inr'))} [VERIFIED]")
    else:
        lines.append("• Darshan: not in our files")
    if n_opt:
        lines.append("• Optional sevas/VIP: not selected — not included")

    lines += ["", "FOOD"]
    if fa.get("min_inr") is not None:
        lines.append(f"• {_rs(fa.get('min_inr'), fa.get('max_inr'))} [ESTIMATED]")
    if inp.get("free_meals"):
        lines.append("• Annadanam: ₹0 if it is serving (confirm at the temple)")
    if nights == 0 and days <= 1:
        lines.append("• Day trip: lunch only (estimate)")
    lines.append("• Food prices are estimates, not a restaurant bill.")

    lines += ["", "STAY"]
    if nights == 0:
        lines.append("• Day trip: ₹0 — stay not included")
        if cheap and costly:
            lines.append(f"• If you stay: {_rs(cheap['min_inr'], costly['max_inr'])}/night [VERIFIED] · per room")
            if inp.get("list_hotels"):
                for h in hotels:
                    lines.append(f"  – {h['name']} · {_rs(h['min_inr'], h['max_inr'])}/night")
    elif cheap and costly:
        lines.append(f"• {_rs(cheap['min_inr'], costly['max_inr'])}/night [VERIFIED] · per room")
        if inp.get("list_hotels"):
            for h in hotels:
                lines.append(f"  – {h['name']} · {_rs(h['min_inr'], h['max_inr'])}/night")
    else:
        lines.append("• Overnight stay: not in our files")

    lines += ["", "TRAVEL"]
    if has_km and km:
        trip_km = km * (2 if round_trip else 1)
        if mode in {"car", "drive"} or (show_car and not show_bus):
            lines += [
                "CAR",
                f"• Distance: {km:.0f} km one-way" + (f" · {trip_km:.0f} km round trip" if round_trip else ""),
                f"• Fuel: {_rs(car.get('min_inr'), car.get('max_inr'))} [ESTIMATED]",
                f"• Assumes 15–20 km/l at ₹{int(PETROL_INR_PER_LITRE)}/l.",
                "• Toll and parking: UNKNOWN — not included",
            ]
        elif mode in {"bus", "transit"} or (show_bus and not show_car):
            lines += [
                "BUS",
                f"• Distance: {km:.0f} km one-way" + (f" · {trip_km:.0f} km round trip" if round_trip else ""),
            ]
            if bus_pp_lo is not None:
                lines.append(f"• Fare: {_rs(bus_pp_lo, bus_pp_hi)}/person [ESTIMATED / GUESSED]")
                lines.append(f"• Group: {_rs(bus.get('min_inr'), bus.get('max_inr'))} [ESTIMATED / GUESSED]")
            else:
                lines.append("• Fare: UNKNOWN")
            lines.append("• Not an official TGSRTC ticket price. Actual fare may vary.")
        else:
            lines += ["TRAVEL OPTIONS", "", "BUS"]
            if bus_pp_lo is not None:
                lines.append(f"• {_rs(bus_pp_lo, bus_pp_hi)}/person [ESTIMATED / GUESSED]")
                lines.append(f"• Group: {_rs(bus.get('min_inr'), bus.get('max_inr'))} [ESTIMATED / GUESSED]")
            else:
                lines.append("• Fare: UNKNOWN")
            lines.append("• Not an official TGSRTC ticket price. Actual fare may vary.")
            lines += ["", "CAR"]
            lines.append(f"• Distance: {km:.0f} km one-way" + (f" · {trip_km:.0f} km round trip" if round_trip else ""))
            lines.append(f"• {_rs(car.get('min_inr'), car.get('max_inr'))} fuel [ESTIMATED]")
            lines.append(f"• Assumes 15–20 km/l at ₹{int(PETROL_INR_PER_LITRE)}/l.")
            lines.append("• Toll and parking: UNKNOWN — not included")
    elif origin_given:
        lines.append(f"• Distance for {origin_name} → {name}: not available yet")
        lines.append("• Travel is not included in the total.")
    else:
        lines.append("• Origin not given — travel not included")

    lines += ["", "TOTAL"]
    if ts.get("min_inr") is not None:
        lines.append(f"• Without travel: {_rs(ts.get('min_inr'), ts.get('max_inr'))}")
    if has_km:
        if show_bus and db.get("min_inr") is not None:
            lines.append("TOTAL WITH BUS")
            lines.append(_rs(db.get("min_inr"), db.get("max_inr")))
        if show_car and dc.get("min_inr") is not None:
            lines.append("TOTAL WITH CAR")
            lines.append(_rs(dc.get("min_inr"), dc.get("max_inr")))
        lines.append("Planning estimate — not a bill.")
    else:
        lines.append("Travel not in this total.")

    if inp.get("wants_cheapest") and has_km and show_bus and show_car:
        b_lo, b_hi = db.get("min_inr"), db.get("max_inr")
        c_lo, c_hi = dc.get("min_inr"), dc.get("max_inr")
        lines += ["", "CHEAPEST ESTIMATE"]
        if b_hi is not None and c_lo is not None and b_hi < c_lo:
            pick = "Bus"
        elif c_hi is not None and b_lo is not None and c_hi < b_lo:
            pick = "Car"
        else:
            pick = None
        if pick:
            lines.append(pick)
            lines.append(
                f"Based on our approximate estimates, {pick.lower()} appears to be the cheaper option."
            )
        else:
            lines.append("Estimates overlap.")
        lines.append("Not guaranteed — bus fares are guessed.")

    lines += ["", "NOT INCLUDED"]
    lines.append("• Optional sevas/VIP unless selected")
    lines.append("• Donations")
    lines.append("• Toll / parking / last-mile when unknown")
    if nights == 0:
        lines.append("• Stay (no overnight selected)")
    if not round_trip:
        lines.append("• Return journey")

    # Overview table
    lines += ["", "OVERVIEW"]
    lines.append("-" * 52)
    lines.append(_row("Item", "Amount", "Status"))
    lines.append("-" * 52)
    if darshan_rows:
        d0 = darshan_rows[0]
        lines.append(_row("Darshan", _rs(d0.get("min_inr"), d0.get("max_inr")), "VERIFIED"))
    if fa.get("min_inr") is not None:
        lines.append(_row("Food", _rs(fa.get("min_inr"), fa.get("max_inr")), "ESTIMATED"))
    if nights == 0:
        lines.append(_row("Stay", "₹0", "not included"))
    elif cheap and costly:
        lines.append(_row("Stay / night", _rs(cheap["min_inr"], costly["max_inr"]), "VERIFIED"))
    if has_km and show_bus and bus.get("min_inr") is not None:
        lines.append(_row("Bus fare", _rs(bus.get("min_inr"), bus.get("max_inr")), "GUESSED"))
    if has_km and show_car and car.get("min_inr") is not None:
        lines.append(_row("Car fuel", _rs(car.get("min_inr"), car.get("max_inr")), "ESTIMATED"))
    if has_km and show_bus and db.get("min_inr") is not None:
        lines.append(_row("TOTAL WITH BUS", _rs(db.get("min_inr"), db.get("max_inr")), "ESTIMATED"))
    if has_km and show_car and dc.get("min_inr") is not None:
        lines.append(_row("TOTAL WITH CAR", _rs(dc.get("min_inr"), dc.get("max_inr")), "ESTIMATED"))
    if not has_km and ts.get("min_inr") is not None:
        lines.append(_row("Without travel", _rs(ts.get("min_inr"), ts.get("max_inr")), "partial"))
    lines.append("-" * 52)
    return "\n".join(lines)

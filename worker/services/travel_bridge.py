"""Bridge: temple_id + starting city → travel.plan_resolved.

Does not open Qdrant. Does not call Groq.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parent.parent
TEMPLES_DIR = ROOT / "data" / "temples"

_ORCH = None


def _orchestrator():
    global _ORCH
    if _ORCH is None:
        from travel.core.orchestrator import TravelAgentOrchestrator

        _ORCH = TravelAgentOrchestrator()
    return _ORCH


def _load_temple(temple_id: str) -> dict[str, Any]:
    tid = (temple_id or "").strip().upper()
    if not re.fullmatch(r"T\d{4}", tid):
        raise ValueError("temple_id must look like T0001")
    path = TEMPLES_DIR / f"{tid}.json"
    if not path.is_file():
        raise FileNotFoundError(tid)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["temple_id"] = tid
    return data


def resolve_origin(source: str) -> dict[str, Any]:
    typed = (source or "").strip()
    empty = {"query": typed, "label": typed, "lat": None, "lng": None}
    if not typed:
        return empty
    try:
        from travel.core.google_client import GoogleMapsClient

        client = GoogleMapsClient()
        if not client.is_available():
            return empty
        query = typed if "india" in typed.lower() else f"{typed}, Telangana, India"
        hit = client.geocode(query)
        if not hit or not hit.get("formatted_address"):
            return empty
        return {
            "query": typed,
            "label": str(hit["formatted_address"]),
            "lat": hit.get("lat"),
            "lng": hit.get("lon"),
        }
    except Exception:
        return empty


def destination_names(temple: dict[str, Any]) -> list[str]:
    """Place-like names for GTFS, not the long deity title first."""
    names: list[str] = []

    def add(value: Any) -> None:
        if not value:
            return
        text = str(value).strip()
        if not text:
            return
        if text not in names:
            names.append(text)

    loc = temple.get("location") or {}
    travel = temple.get("travel") or {}
    multi = temple.get("multilingual") or {}

    add(loc.get("village"))
    district = loc.get("district") or loc.get("mandal") or loc.get("city")
    if loc.get("village") and district:
        add(f"{loc['village']}, {district}, Telangana, India")
    elif loc.get("village"):
        add(f"{loc['village']}, Telangana, India")
    add(district)
    add(travel.get("nearest_bus_station"))
    # Do not send a bare Venkateswara / Balaji title to Google — it becomes Tirupati AP.
    name = str(temple.get("name") or "")
    if loc.get("village") or loc.get("latitude"):
        pass
    else:
        add(name)
    return names


def corpus_travel(temple: dict[str, Any]) -> dict[str, Any]:
    loc = temple.get("location") or {}
    travel = temple.get("travel") or {}
    hyd = None
    for line in travel.get("distances") or []:
        if re.search(r"hyderabad", str(line), re.I):
            match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*km", str(line), re.I)
            if match:
                hyd = float(match.group(1))
            break
    return {
        "lat": loc.get("latitude"),
        "lng": loc.get("longitude"),
        "road_from_hyderabad_km": hyd,
        "nearest_railway": travel.get("nearest_railway_station"),
        "nearest_bus": travel.get("nearest_bus_station"),
        "nearest_airport": travel.get("nearest_airport"),
    }


TSRTC_LIKE = re.compile(r"^[0-9]{1,4}[A-Z]{0,4}(?:/[0-9]{1,4}[A-Z]{0,4})?$", re.I)
PRIVATE_COACH = re.compile(r"tours|travels|mythri|orange|private|luxury coach", re.I)
TRAIN_VEHICLE = re.compile(
    r"\b(train|heavy_rail|commuter_train|high_speed_train|long_distance_train|rail)\b",
    re.I,
)
TRAIN_NUM = re.compile(r"^\d{4,5}[A-Z]?$")
TRAIN_NAME = re.compile(r"express|passenger|superfast|\bsf\b|mail|mmts|memu|local", re.I)


def display_bus_id(raw: Any) -> str:
    """Show a TSRTC-like number only if Maps actually sent one. Never invent 284P."""
    text = str(raw or "").strip()
    if not text:
        return "(number not given)"
    if PRIVATE_COACH.search(text):
        return "(number not given)"
    token = text.split()[0].strip()
    compact = token.replace(" ", "")
    if TSRTC_LIKE.match(compact):
        return compact
    if re.fullmatch(r"[0-9]{1,4}[A-Z]{0,4}", compact, re.I):
        return compact
    return "(number not given)"


def display_train_id(raw: Any) -> str:
    """Show a train number/name only if the provider sent one. Never invent 12760."""
    text = str(raw or "").strip()
    if not text:
        return "(number not given)"
    if PRIVATE_COACH.search(text):
        return "(number not given)"
    token = text.split()[0].strip()
    compact = token.replace(" ", "")
    if TRAIN_NUM.match(compact):
        return compact
    # 113M / 500 / 284P are buses. Do not print them as trains.
    if TSRTC_LIKE.match(compact):
        return "(number not given)"
    if TRAIN_NAME.search(text):
        return text[:60]
    return "(number not given)"


def _is_train_seg(seg: dict[str, Any] | None) -> bool:
    mode = str((seg or {}).get("mode") or "").lower().replace("-", "_")
    if "bus" in mode:
        return False
    if mode in {"metro", "metro_rail", "subway", "tram"}:
        return False
    return bool(TRAIN_VEHICLE.search(mode))


def railway_dests(facts: dict[str, Any]) -> list[str]:
    raw = str((facts or {}).get("nearest_railway") or "")
    names: list[str] = []
    for part in re.split(r";|\bas an alternative\b", raw, flags=re.I):
        part = part.split("(")[0].strip(" .")
        if part and part not in names:
            names.append(part)
    return names



_FOREIGN_CITY = re.compile(
    r"\b(tirupathi|tirupati|chennai|bangalore|bengaluru|mumbai|pune)\b",
    re.I,
)


def _home_blob(temple: dict[str, Any] | None, facts: dict[str, Any] | None) -> str:
    loc = ((temple or {}).get("location") or {})
    return " ".join(
        str(x or "")
        for x in (
            loc.get("village"),
            loc.get("district"),
            loc.get("mandal"),
            (temple or {}).get("name"),
            (facts or {}).get("nearest_bus"),
        )
    )


def _sane_option(
    option: dict[str, Any],
    facts: dict[str, Any] | None = None,
    temple: dict[str, Any] | None = None,
) -> bool:
    """Drop Maps jokes: 1526 km cars, Venkateswara→Tirupathi buses."""
    km = float(option.get("distance_km") or 0)
    mins = option.get("duration_minutes") or 0
    blob = " ".join(option.get("steps") or [])
    home = _home_blob(temple, facts)
    hint = option.get("mode_hint")
    if hint == "car":
        # Adilabad → Manyamkonda is ~8 hours. Only drop continent-scale errors.
        if km > 900 or (mins and mins > 1080):
            return False
        return True
    if hint == "bus":
        if _FOREIGN_CITY.search(blob) and not _FOREIGN_CITY.search(home):
            return False
        # Private coach / Maps fake transit. Never show as a public bus.
        if "number not given" in blob.lower():
            return False
        if re.search(r"take bus", blob, re.I) and not re.search(r"take bus\s+\d", blob, re.I):
            return False
    return True


def _boarding_penalty(option: dict[str, Any]) -> int:
    blob = " ".join(option.get("steps") or [])
    if PRIVATE_COACH.search(blob):
        return 2
    if "number not given" in blob.lower():
        return 1
    if re.search(r"take bus\s+\d", blob, re.I):
        return 0
    return 1


def _via_places(segments: list[dict[str, Any]] | None) -> list[str]:
    names: list[str] = []
    for seg in segments or []:
        for key in ("from_stop_id", "to_stop_id", "from_stop", "to_stop", "route_name"):
            value = seg.get(key)
            if not value:
                continue
            text = str(value).strip()
            if re.match(r"^-?\d+\.\d+\s*,\s*-?\d+\.\d+$", text):
                continue
            if len(text) > 80:
                text = text.split(",")[0].strip()
            if text and text not in names:
                names.append(text)
    return names[:8]


def _mode_hint(summary: str, mode: str, segments: list | None) -> str:
    # A bus path asked as "train" is still a bus. Do not relabel it.
    if any(_is_train_seg(s) for s in (segments or [])):
        return "train"
    blob = (summary or "").lower()
    segs = " ".join(str((s or {}).get("mode", "")) for s in (segments or [])).lower()
    if mode == "drive" or "driving" in blob or "drive" in segs:
        return "car"
    return "bus"


def _steps_from_segments(segments: list[dict[str, Any]] | None) -> list[str]:
    segs = list(segments or [])
    steps: list[str] = []
    for index, seg in enumerate(segs):
        mode = str(seg.get("mode") or "").lower()
        start = seg.get("from_stop_id") or seg.get("from_stop") or "?"
        end = seg.get("to_stop_id") or seg.get("to_stop") or "?"
        bus = seg.get("route_id") or seg.get("route_name")
        mins = seg.get("duration_minutes")
        if mode in {"walking", "walk"}:
            nxt = None
            for later in segs[index + 1 :]:
                later_mode = str(later.get("mode") or "").lower()
                if later_mode not in {"walking", "walk", "driving", "bicycling"}:
                    nxt = later.get("from_stop_id") or later.get("from_stop")
                    break
            dest = nxt or end
            text = f"Walk to {dest}" + (f" — {mins} min" if mins else "")
        elif mode in {"driving", "drive"}:
            text = f"Drive to {end}" + (f" — {mins} min" if mins else "")
        elif _is_train_seg(seg):
            shown = display_train_id(bus)
            text = f"Take train {shown} from {start} to {end}"
            if mins:
                text += f" — {mins} min"
        elif bus:
            shown = display_bus_id(bus)
            text = f"Take bus {shown} from {start} to {end}"
            if mins:
                text += f" — {mins} min"
        else:
            text = seg.get("instruction") or f"Go from {start} to {end}"
        if text and text not in steps:
            steps.append(str(text))
    return steps


def _option_from_candidate(candidate, mode: str, label: str) -> dict[str, Any]:
    segments = getattr(candidate, "segments", None) or []
    hint = _mode_hint(getattr(candidate, "summary", ""), mode, segments)
    steps = _steps_from_segments(segments)
    if hint == "car" or (len(steps) > 1 and steps and all("drive" in s.lower() for s in steps)):
        total = getattr(candidate, "duration_minutes", None)
        steps = [f"Drive to the temple — {total} min"] if total else ["Drive to the temple"]
    return {
        "label": label,
        "summary": getattr(candidate, "summary", "") or "",
        "via": _via_places(segments),
        "steps": steps,
        "transfers": getattr(candidate, "transfers", 0) or 0,
        "distance_km": getattr(candidate, "distance_km", 0.0) or 0.0,
        "duration_minutes": getattr(candidate, "duration_minutes", None),
        "departure_time": getattr(candidate, "departure_time", None),
        "arrival_time": getattr(candidate, "arrival_time", None),
        "mode_hint": hint,
        "segments": segments,
        "live_source": "Google Maps Directions" if "google" in (getattr(candidate, "summary", "") or "").lower() else "travel engine",
    }


def _recommend(options: list[dict[str, Any]], asked: str, nearest_railway: str | None = None, nearest_bus: str | None = None) -> str:
    if not options:
        bus = (nearest_bus or "").strip()
        if bus:
            return (
                "Google has no live path from this start. "
                f"Nearest bus in our file: {bus}. "
                "Try car if you can. I will not invent a route."
            )
        return (
            "Google has no live path from this start. "
            "I will not invent a bus. Try car, or a closer city."
        )
    bus = [o for o in options if o["mode_hint"] == "bus"]
    car = [o for o in options if o["mode_hint"] == "car"]
    train = [o for o in options if o["mode_hint"] == "train"]
    if asked in {"transit", "bus"} and not bus:
        car_bit = ""
        if car:
            best = min(car, key=lambda o: o.get("duration_minutes") or 9999)
            if best.get("duration_minutes"):
                car_bit = f" Car is about {best['duration_minutes']} min ({best.get('distance_km', 0):.0f} km)."
        depot = (nearest_bus or "").strip()
        extra = f" Nearest bus in our file: {depot}." if depot else ""
        return (
            "Google Maps has no numbered public bus from this start to this temple. "
            "Village Palle Velugu is not in Maps. I will not invent a bus number."
            + extra
            + car_bit
            + " For village buses use the TGSRTC Gamyam app or the local depot."
        )
    if asked == "train" and not train:
        station = (nearest_railway or "").strip() or "unknown (not in temple file)"
        return (
            "No real train from your start to this temple. "
            "I will not invent a train number. "
            f"Nearest station in our file: {station}. "
            "Best: bus (cheaper) or car (faster, fewer changes)."
        )
    best_bus = min(bus, key=lambda o: (o["transfers"], o["duration_minutes"] or 9999), default=None)
    best_car = min(car, key=lambda o: (o["duration_minutes"] or 9999), default=None)
    if best_bus and best_bus["transfers"] >= 2 and best_car and (best_car["duration_minutes"] or 999) < (best_bus["duration_minutes"] or 999):
        return (
            f"Best overall: car. Bus needs {best_bus['transfers']} changes "
            f"({best_bus['duration_minutes']} min). Car is about {best_car['duration_minutes']} min with no changes."
        )
    if asked == "drive" and best_car:
        return "Best for time and fewer changes: car. Bus is cheaper if you do not mind transfers."
    if best_bus and best_car and (best_car.get("duration_minutes") or 0) and (best_bus.get("duration_minutes") or 0):
        if best_car["duration_minutes"] * 1.5 < best_bus["duration_minutes"]:
            return (
                f"Bus is cheaper ({best_bus['transfers']} change(s), {best_bus['duration_minutes']} min). "
                f"Car is much faster ({best_car['duration_minutes']} min, no change)."
            )
    if best_bus and best_bus["transfers"] <= 1:
        return "Best for most pilgrims: bus — cheaper than car, and this option has at most one change."
    return "If you want cheap, take the bus with fewest changes. If you want simple, take a car/taxi."


def collapse_route_clones(options: list[dict[str, Any]], asked_hint: str = "bus") -> list[dict[str, Any]]:
    """One skeleton per bus-number tail. Extra first buses become a note. One car."""

    def bus_bits(step: str):
        match = re.search(
            r"take bus\s+(\S+)\s+from\s+(.+?)\s+to\s+(.+?)(?:\s+—|$)",
            step,
            re.I,
        )
        if not match:
            return None
        return match.group(1), match.group(2).strip(), match.group(3).strip()

    def sequence(option: dict[str, Any]) -> tuple[str, ...]:
        nums = []
        for step in option.get("steps") or []:
            bits = bus_bits(step)
            if bits:
                nums.append(bits[0].upper())
        return tuple(nums)

    buses = [dict(o) for o in options if o.get("mode_hint") == "bus"]
    cars = [dict(o) for o in options if o.get("mode_hint") == "car"]
    rest = [dict(o) for o in options if o.get("mode_hint") not in {"bus", "car"}]

    groups: dict[tuple[str, ...], list] = {}
    leftovers: list[dict[str, Any]] = []
    for bus in buses:
        seq = sequence(bus)
        if len(seq) >= 2:
            groups.setdefault(seq[1:], []).append((bus, seq))
        else:
            leftovers.append(bus)

    collapsed: list[dict[str, Any]] = []
    for spine, members in groups.items():
        members.sort(key=lambda item: (item[0].get("duration_minutes") or 9999, item[0].get("transfers") or 0))
        best, best_seq = members[0]
        alts = []
        for other, seq in members[1:]:
            if not seq or seq[0] == best_seq[0]:
                continue
            first = next((s for s in (other.get("steps") or []) if s.lower().startswith("take bus")), "")
            bits = bus_bits(first)
            if bits:
                alts.append(f"{bits[0]} from {bits[1]}")
        if alts:
            first_best = bus_bits(
                next((s for s in (best.get("steps") or []) if s.lower().startswith("take bus")), "")
            )
            instead = f"{first_best[0]} from {first_best[1]}" if first_best else "the first bus"
            best["note"] = (
                f"Same {' → '.join(spine)} after the first bus. "
                f"Or board {'; '.join(alts)} instead of {instead}."
            )
        collapsed.append(best)
    collapsed.extend(leftovers)
    collapsed.sort(key=lambda o: (_boarding_penalty(o), o.get("duration_minutes") or 9999, o.get("transfers") or 0))

    if cars:
        cars.sort(key=lambda o: o.get("duration_minutes") or 9999)
        cars = cars[:1]

    if asked_hint == "car":
        return cars[:3] + collapsed[:1] + rest[:1]
    if asked_hint == "train":
        return rest[:3] + collapsed[:1] + cars[:1]
    return collapsed[:3] + cars[:1] + rest[:1]


def plan_to_temple(
    temple_id: str,
    source: Optional[str] = None,
    mode: str = "transit",
    departure_time: Optional[str] = None,
) -> dict[str, Any]:
    try:
        temple = _load_temple(temple_id)
    except ValueError:
        return {
            "status": "unknown_temple",
            "temple_id": temple_id,
            "question": "Send a temple id like T0001, not a nickname.",
        }
    except FileNotFoundError:
        return {
            "status": "unknown_temple",
            "temple_id": (temple_id or "").strip().upper(),
            "question": f"No temple file for {(temple_id or '').strip().upper()}.",
        }

    tid = temple["temple_id"]
    source_clean = (source or "").strip()
    if not source_clean:
        return {
            "status": "needs_origin",
            "temple_id": tid,
            "temple_name": temple.get("name"),
            "question": "From which city or station?",
            "corpus_travel": corpus_travel(temple),
        }

    origin = resolve_origin(source_clean)
    source_for_maps = origin["label"] or source_clean

    tried: list[str] = []
    orch = _orchestrator()
    facts = corpus_travel(temple)
    dest_pin = None
    if facts.get("lat") is not None and facts.get("lng") is not None:
        dest_pin = f"{facts['lat']},{facts['lng']}"

    dests = destination_names(temple)
    dest_pin_use = dest_pin
    if mode == "train":
        dests = railway_dests(facts) + dests
        dest_pin_use = None

    options: list[dict[str, Any]] = []
    warnings: list[str] = []

    def _ingest(result, asked_mode: str, label: str) -> None:
        if result is None:
            return
        warnings.extend(result.warnings or [])
        bag = []
        if result.route is not None:
            bag.append(result.route)
        bag.extend(result.alternatives or [])
        for item in bag:
            blob = _option_from_candidate(item, asked_mode, label)
            if asked_mode == "train" and blob["mode_hint"] != "train":
                continue
            if not _sane_option(blob, facts, temple):
                continue
            key = (blob["mode_hint"], blob["transfers"], round(blob["distance_km"], 1), tuple(blob["via"][:3]))
            if any(
                (o["mode_hint"], o["transfers"], round(o["distance_km"], 1), tuple(o["via"][:3])) == key
                for o in options
            ):
                continue
            options.append(blob)

    if dest_pin_use:
        _ingest(
            orch.plan_resolved(source_for_maps, dests[0] if dests else "temple", mode=mode, dest_pin=dest_pin_use),
            mode,
            "pinned temple hill",
        )
        tried.append(dest_pin_use)

    for dest in dests[:4]:
        tried.append(dest)
        result = orch.plan_resolved(source_for_maps, dest, mode=mode, dest_pin=dest_pin_use)
        _ingest(result, mode, dest)
        if mode == "train":
            if any(o.get("mode_hint") == "train" for o in options):
                break
        elif len([o for o in options if o["mode_hint"] != "car"]) >= 3:
            break

    # Train search is station-only. Always also offer a real bus/car to the temple hill.
    if mode == "train":
        hill_names = destination_names(temple)
        if dest_pin:
            _ingest(
                orch.plan_resolved(source_for_maps, hill_names[0] if hill_names else "temple", mode="transit", dest_pin=dest_pin),
                "transit",
                "temple bus",
            )
            tried.append(dest_pin)
        for dest in hill_names[:3]:
            _ingest(
                orch.plan_resolved(source_for_maps, dest, mode="transit", dest_pin=dest_pin),
                "transit",
                dest,
            )
            if len([o for o in options if o.get("mode_hint") == "bus"]) >= 3:
                break

    if mode != "drive" and dest_pin:
        hill = destination_names(temple)
        _ingest(
            orch.plan_resolved(source_for_maps, hill[0] if hill else "temple", mode="drive", dest_pin=dest_pin),
            "drive",
            "by car",
        )

    def _bus_key(option):
        nums = []
        for step in option.get("steps") or []:
            match = re.search(r"take bus\s+([A-Za-z0-9]+)", step, re.I)
            if match:
                nums.append(match.group(1).upper())
        return tuple(nums)

    unique: list[dict[str, Any]] = []
    seen_buses = set()
    for option in options:
        key = (option["mode_hint"], _bus_key(option) or (round(option["distance_km"], 1), option["transfers"]))
        if key in seen_buses:
            continue
        seen_buses.add(key)
        unique.append(option)
    asked_hint = "car" if mode == "drive" else ("train" if mode == "train" else "bus")
    options = collapse_route_clones(unique, asked_hint)
    train_found = any(o.get("mode_hint") == "train" for o in options)
    if mode == "train" and not train_found:
        warnings.append(
            "No real train found from your start to this temple. I will not invent a train number."
        )
    primary = next((o for o in options if o.get("mode_hint") == asked_hint), None) or (
        options[0] if options else None
    )
    route_blob = None
    if primary:
        route_blob = {
            "summary": primary["summary"],
            "distance_km": primary["distance_km"],
            "duration_minutes": primary["duration_minutes"],
            "transfers": primary["transfers"],
            "departure_time": primary["departure_time"],
            "arrival_time": primary["arrival_time"],
            "segments": primary["segments"],
            "via": primary["via"],
        }

    status = "ok" if options else "no_route"
    if status == "no_route":
        warnings.append(
            "No bus/train path in the travel engine. Showing temple travel facts from our corpus."
        )

    places = locations_for_travel(tid)
    return {
        "status": status,
        "temple_id": tid,
        "temple_name": temple.get("name"),
        "source": source_clean,
        "mode": mode,
        "destinations_tried": tried,
        "route": route_blob,
        "options": options[:5],
        "recommendation": _recommend(
            options,
            "train" if mode == "train" else ("drive" if mode == "drive" else "transit"),
            nearest_railway=facts.get("nearest_railway"),
            nearest_bus=facts.get("nearest_bus"),
        ),
        "train_found": train_found if mode == "train" else None,
        "attractions": (places.get("attractions") or [])[:5],
        "warnings": warnings,
        "corpus_travel": facts,
    }



def format_compare(result: dict[str, Any]) -> str:
    kind = result.get("compare") or "compare"
    title = {
        "cheapest": "COMPARE — cheapest first (no invented rupees)",
        "fastest": "COMPARE — fastest first",
        "longest": "COMPARE — distance short → long",
        "compare": "COMPARE — bus / car / train we actually found",
    }.get(kind, "COMPARE")
    lines = [
        f"Travel to {result.get('temple_name') or result.get('temple_id')} from {result.get('source') or ''}.",
        title,
    ]
    if result.get("cost_note") and kind in {"cheapest", "compare"}:
        lines.append(result["cost_note"])
    rows = result.get("rows") or []
    if not rows:
        lines.append("I could not compare live paths.")
    for i, row in enumerate(rows, 1):
        mins = row.get("minutes")
        tail = f"{row.get('km', 0):.1f} km"
        if mins is not None:
            tail += f", {mins} min"
        extra = ""
        if kind == "cheapest":
            extra = " — fare unknown" if row["mode"] != "car" else " — taxi/fuel unknown"
        lines.append(f"{i}. {row['mode'].upper()} — {tail}{extra}")
    if kind == "cheapest":
        if any(r["mode"] == "bus" for r in rows):
            lines.append("Usually cheapest: bus. I will not invent a ticket price.")
        if not result.get("train_found"):
            lines.append("Train: no real train from this start. I will not invent a fare.")
    if kind == "fastest" and rows:
        lines.append(f"Fastest of these: {rows[0]['mode']}.")
    if kind == "longest" and rows:
        lines.append("Order is kilometres, short to long. Not ticket price.")
    facts = result.get("corpus_travel") or {}
    if facts.get("nearest_railway"):
        lines.append(f"Nearest railway: {facts['nearest_railway']}")
    return chr(10).join(lines)


def compare_to_temple(temple_id: str, source: str, kind: str = "cheapest") -> dict[str, Any]:
    """Rank real bus/car/train. Do not invent rupees. That is budget's job."""
    bus_pack = plan_to_temple(temple_id, source=source, mode="transit")
    if bus_pack.get("status") in {"needs_origin", "unknown_temple"}:
        return bus_pack
    train_pack = plan_to_temple(temple_id, source=source, mode="train")

    def pick(pack: dict[str, Any], hint: str) -> dict[str, Any] | None:
        for option in pack.get("options") or []:
            if option.get("mode_hint") == hint:
                return option
        return None

    rows: list[dict[str, Any]] = []
    for hint, pack in (("bus", bus_pack), ("car", bus_pack), ("train", train_pack)):
        option = pick(pack, hint)
        if not option:
            continue
        if hint == "train" and not train_pack.get("train_found"):
            continue
        rows.append(
            {
                "mode": hint,
                "km": option.get("distance_km") or 0.0,
                "minutes": option.get("duration_minutes"),
                "transfers": option.get("transfers") or 0,
                "option": option,
            }
        )

    if kind == "longest":
        rows.sort(key=lambda row: float(row["km"] or 9999))
    elif kind == "fastest":
        rows.sort(key=lambda row: row["minutes"] if row["minutes"] is not None else 9999)
    else:
        rank = {"bus": 0, "train": 1, "car": 2}
        rows.sort(key=lambda row: rank.get(row["mode"], 9))

    facts = bus_pack.get("corpus_travel") or train_pack.get("corpus_travel") or {}
    return {
        "status": "ok" if rows else "no_route",
        "temple_id": bus_pack.get("temple_id") or temple_id,
        "temple_name": bus_pack.get("temple_name"),
        "source": source,
        "compare": kind if kind in {"cheapest", "fastest", "longest"} else "compare",
        "rows": rows,
        "train_found": bool(train_pack.get("train_found")),
        "options": [row["option"] for row in rows],
        "corpus_travel": facts,
        "cost_note": (
            "Ticket / taxi rupees are not in our travel files. "
            "That is a budget-agent job. I will not invent ₹."
        ),
        "recommendation": None,
        "warnings": list(bus_pack.get("warnings") or []),
    }



def drive_km_to_temple(temple_id: str, origin: str) -> dict[str, Any]:
    """Driving km only. No GTFS. No bus numbers. Soft-fail. Budget asks this for non-Hyd origins."""
    empty = {
        "status": "no_km",
        "temple_id": (temple_id or "").strip().upper(),
        "origin": (origin or "").strip(),
        "distance_km": None,
        "duration_minutes": None,
        "source": None,
    }
    source = (origin or "").strip()
    if not source:
        return empty
    try:
        temple = _load_temple(temple_id)
    except (ValueError, FileNotFoundError):
        return empty
    facts = corpus_travel(temple)
    dest = None
    if facts.get("lat") is not None and facts.get("lng") is not None:
        dest = f"{facts['lat']},{facts['lng']}"
    else:
        names = destination_names(temple)
        dest = names[0] if names else None
    if not dest:
        return empty
    try:
        from travel.core.google_client import GoogleMapsClient

        client = GoogleMapsClient()
        if not client.is_available():
            return empty
        data = client.directions(source, dest, mode="drive")
        if not data or not data.get("routes"):
            return empty
        legs = data["routes"][0].get("legs") or []
        meters = sum(leg.get("distance", {}).get("value", 0) for leg in legs)
        seconds = sum(leg.get("duration", {}).get("value", 0) for leg in legs)
        km = float(meters) / 1000 if meters else None
        if not km or km <= 0 or km > 900:
            return empty
        return {
            "status": "ok",
            "temple_id": temple["temple_id"],
            "origin": source,
            "distance_km": round(km, 1),
            "duration_minutes": int(round(seconds / 60)) if seconds else None,
            "source": "google_maps_drive",
        }
    except Exception:
        return empty


def locations_for_travel(temple_id: str) -> dict[str, Any]:
    """Places travel may pin on a map. Not RAG search. Not prices."""
    try:
        temple = _load_temple(temple_id)
    except (ValueError, FileNotFoundError):
        return {"status": "unknown_temple", "temple_id": temple_id, "items": {}}

    loc = temple.get("location") or {}
    nearby = temple.get("nearby_places") or []
    hotels: list[dict[str, Any]] = []
    restaurants: list[dict[str, Any]] = []
    emergency: list[dict[str, Any]] = []
    try:
        from services.catalog import Catalog

        cat = Catalog(ROOT / "data")
        hotels = [
            {"name": row["name"], "distance_km": row.get("distance_km")}
            for row in cat.get_hotels(temple["temple_id"]).get("items", [])
        ]
        restaurants = [
            {"name": row["name"], "distance_km": row.get("distance_km")}
            for row in cat.get_restaurants(temple["temple_id"]).get("items", [])
        ]
        emergency = [
            {"name": row["name"], "kind": row.get("kind"), "distance_km": row.get("distance_km")}
            for row in cat.get_emergency(temple["temple_id"]).get("items", [])
        ]
    except Exception:
        pass

    return {
        "status": "ok",
        "temple_id": temple["temple_id"],
        "temple": {
            "name": temple.get("name"),
            "lat": loc.get("latitude"),
            "lng": loc.get("longitude"),
            "village": loc.get("village"),
        },
        "attractions": [{"name": str(item)} for item in nearby if item],
        "hotels": hotels,
        "restaurants": restaurants,
        "emergency": emergency,
        "corpus_travel": corpus_travel(temple),
    }

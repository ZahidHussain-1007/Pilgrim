"""Catalog contract tests. No Groq. No Qdrant.

Run from project root:
    python tests/test_catalog.py

This file creates tests/fixtures/ by itself if that folder is missing.
Those fixtures are fake sample data for the test only.
They do not replace your real data/ folder.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.catalog import Catalog, CatalogError

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def ensure_fixtures() -> Path:
    """Create the sample files the 17 checks need."""
    _write(
        FIXTURES / "temples" / "T0001.json",
        {
            "temple_id": "T0001",
            "name": "Sri Lakshmi Narasimha Swamy Temple",
            "last_verified": "2026-08-21",
            "location": {
                "district": "Yadadri Bhuvanagiri District",
                "pincode": "508115",
                "latitude": 17.5886069,
                "longitude": 78.9412785,
            },
            "contact": {"official_website": "https://yadagiriguttatemple.telangana.gov.in/"},
            "darshan_and_tickets": {
                "general_darshan": "Sarva Darshan is free during official windows.",
                "special_darshan": "VIP Break Darshan. Confirm fees at the counter.",
            },
            "sevas": [
                {"name": "Sarva Darshan (General Darshan)", "charges": "Free"},
                {"name": "Kalyanotsavam", "charges": "Paid (amount not specified)"},
            ],
            "accommodation": {
                "price_range": "Temple-managed rooms generally cost between ₹300 and ₹1,500 per night"
            },
            "travel": {
                "distances": ["Hyderabad: ~65 km"],
                "nearest_railway_station": "Raigir Railway Station (~5 km)",
                "nearest_bus_station": "Yadagirigutta Bus Stand (~1 km)",
                "nearest_airport": "Rajiv Gandhi International Airport, Hyderabad (~90 km)",
            },
        },
    )
    _write(
        FIXTURES / "temples" / "T0020.json",
        {
            "temple_id": "T0020",
            "name": "Beechupally Anjaneya Swamy Temple",
            "last_verified": "2026-08-21",
            "location": {"district": "Jogulamba Gadwal", "latitude": 16.0833, "longitude": 77.8167},
            "darshan_and_tickets": {"general_darshan": "Free", "special_darshan": "Paid (amount not specified)"},
            "sevas": [{"name": "Abhishekam", "charges": "Paid (amount not specified)"}],
            "travel": {"distances": ["Hyderabad: ~180 km"], "nearest_railway_station": "Gadwal (~16 km)"},
        },
    )
    _write(
        FIXTURES / "hotels" / "H_YAD_1.json",
        {
            "hotel_id": "H_YAD_1",
            "temple_id": "T0001",
            "name": "Haritha Hotel Yadagirigutta",
            "distance_km": 1.2,
            "price_range": "₹800–₹2500 per night",
            "last_verified": "2026-08-21",
        },
    )
    _write(
        FIXTURES / "hotels" / "H_YAD_DUP.json",
        {
            "hotel_id": "H_YAD_1",
            "temple_id": "T0001",
            "name": "Haritha Hotel Yadagirigutta (duplicate file)",
            "distance_km": 1.2,
            "min_inr": 800,
            "max_inr": 2500,
        },
    )
    _write(
        FIXTURES / "hotels" / "H_YAD_NOPRICE.json",
        {
            "hotel_id": "H_YAD_NOPRICE",
            "temple_id": "T0001",
            "name": "Temple cottage (rate unknown)",
            "distance": "0.8 km",
        },
    )
    _write(
        FIXTURES / "hotels" / "H_BEE_1.json",
        {
            "hotel_id": "H_BEE_1",
            "temple_id": "T0020",
            "name": "Sagaar Lodge Beechupally",
            "distance_km": 0.4,
            "min_price": 600,
            "max_price": 1200,
            "last_verified": "2026-08-21",
        },
    )
    _write(
        FIXTURES / "hotels" / "H_HYD_WRONG.json",
        {
            "hotel_id": "H_HYD_WRONG",
            "temple_id": "T0009",
            "name": "Hotel Rajdhani Hyderabad",
            "distance_km": 5,
            "price_range": "₹3500 per night",
        },
    )
    _write(
        FIXTURES / "restaurants" / "R_YAD_1.json",
        {"restaurant_id": "R_YAD_1", "temple_id": "T0001", "name": "Annadanam Hall", "price": "Free meals"},
    )
    _write(
        FIXTURES / "emergency" / "E_YAD_HOSP.json",
        {
            "id": "E_YAD_HOSP",
            "temple_id": "T0001",
            "name": "Primary Health Centre, Yadagirigutta",
            "service_type": "hospital",
            "phone": "108",
            "distance_km": 1,
        },
    )
    return FIXTURES


def main() -> None:
    data_root = ensure_fixtures()
    cat = Catalog(data_root)
    print(f"Loaded {len(cat.temples)} temples from {data_root}")
    print(f"Temple ids: {sorted(cat.temples)}")
    if "T0001" not in cat.temples:
        print("FATAL: T0001 still missing after writing fixtures.")
        print("Check that services/catalog.py is the new file.")
        raise SystemExit(1)

    passed = 0
    cases: list[tuple[str, bool, str]] = []

    t = cat.get_temple("T0001")
    ok = t["temple_id"] == "T0001" and t["lat"] is not None and bool(t["name"])
    cases.append(("T0001 identity + geo", ok, str(t)))

    costs = cat.get_costs("T0001")
    sarva = next((d for d in costs["darshan"] if d["code"] == "sarva"), None)
    ok = sarva is not None and sarva["fee_inr"] == 0 and sarva["confidence"] in {"official", "listed"}
    cases.append(("T0001 Sarva darshan is 0, not unknown", ok, str(sarva)))

    kalyana = next((s for s in costs["sevas"] if "kalyanotsavam" in s["name"].lower()), None)
    ok = kalyana is not None and kalyana["fee_inr"] is None and kalyana["confidence"] == "unknown"
    cases.append(("T0001 Kalyanotsavam stays null", ok, str(kalyana)))
    ok = any("Kalyanotsavam" in m for m in costs["missing"])
    cases.append(("T0001 missing list names the unknown seva", ok, str(costs["missing"][:8])))

    stay = costs["temple_stay"]
    ok = stay["min_inr"] == 300 and stay["max_inr"] == 1500 and stay["confidence"] == "range"
    cases.append(("T0001 temple stay band 300-1500", ok, str(stay)))

    travel = cat.get_travel("T0001")
    rail_name = (travel.get("nearest_railway") or {}).get("name", "")
    ok = (
        travel["road_from_hyderabad_km"] == 65
        and travel["lat"] is not None
        and "raigir" in rail_name.lower()
    )
    cases.append(("T0001 travel hyd 65km + Raigir", ok, str(travel)))

    hotels = cat.get_hotels("T0001")
    ids = [h["entity_id"] for h in hotels["items"]]
    names = [h["name"] for h in hotels["items"]]
    ok = ids.count("H_YAD_1") == 1
    cases.append(("duplicate hotel entity_id collapsed", ok, str(ids)))
    ok = "H_HYD_WRONG" not in ids and not any("rajdhani" in n.lower() for n in names)
    cases.append(("T0001 hotels exclude Hyderabad Rajdhani", ok, str(ids)))
    ok = "H_BEE_1" not in ids
    cases.append(("T0001 hotels exclude Beechupally lodge", ok, str(ids)))

    yad = next((h for h in hotels["items"] if h["entity_id"] == "H_YAD_1"), None)
    ok = yad is not None and yad["min_inr"] == 800 and yad["max_inr"] == 2500
    cases.append(("T0001 Haritha price parsed from ₹ range", ok, str(yad)))

    noprice = next((h for h in hotels["items"] if h["entity_id"] == "H_YAD_NOPRICE"), None)
    ok = noprice is not None and noprice["min_inr"] is None and noprice["confidence"] == "unknown"
    cases.append(("hotel without number is unknown, not 0", ok, str(noprice)))

    bee = cat.get_hotels("T0020")
    bee_ids = [h["entity_id"] for h in bee["items"]]
    ok = bee_ids == ["H_BEE_1"]
    cases.append(("T0020 hotels are only Beechupally-scoped", ok, str(bee_ids)))

    food = cat.get_restaurants("T0001")
    ok = len(food["items"]) == 1 and food["items"][0]["entity_id"] == "R_YAD_1"
    cases.append(("T0001 restaurant scoped", ok, str(food["items"])))

    em = cat.get_emergency("T0001")
    ok = bool(em["items"]) and em["items"][0]["kind"] == "hospital"
    cases.append(("T0001 emergency hospital", ok, str(em["items"])))

    raised = None
    try:
        cat.get_hotels("T9999")
    except CatalogError as exc:
        raised = exc
    ok = raised is not None and raised.status == 404
    cases.append(("unknown temple_id is 404", ok, str(raised)))

    raised = None
    try:
        cat.get_costs("yadadri")
    except CatalogError as exc:
        raised = exc
    ok = raised is not None and raised.status == 409
    cases.append(("nickname instead of T00xx is 409", ok, str(raised)))

    raised = None
    try:
        cat.get_travel("")
    except CatalogError as exc:
        raised = exc
    ok = raised is not None and raised.status == 422
    cases.append(("empty temple_id is 422", ok, str(raised)))

    print("=" * 80)
    print("PILGRIMAI CATALOG CONTRACT")
    print("=" * 80)
    for i, (name, ok, detail) in enumerate(cases, 1):
        passed += int(ok)
        print(f"\n[{'PASS' if ok else 'FAIL'}] {i}. {name}")
        print("  ", detail[:240])
    total = len(cases)
    print("\n" + "=" * 80)
    print(f"RESULT: {passed}/{total}")
    print("=" * 80)
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

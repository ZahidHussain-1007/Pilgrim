import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.budget import (
    allowed_optimizer_modes,
    format_budget,
    is_budget_query,
    nights_of,
    plan_budget,
    travel_facts_from_plan,
)


def test_receptionist_budget_vs_travel_vs_rag():
    assert is_budget_query("how much will darshan cost") is True
    assert is_budget_query("can I do yadadri in 7000 rupees") is True
    assert is_budget_query("cheapest way from uppal to yadadri") is False
    assert is_budget_query("budget cheapest for yadadri from hyderabad") is True
    assert is_budget_query("hotels near yadadri") is False
    assert is_budget_query("list hotels") is True
    assert is_budget_query("list hotels with prices") is True
    assert is_budget_query("how much time from secunderabad") is False
    assert is_budget_query("history of yadadri") is False


def test_day_trip_zero_nights():
    assert nights_of(1) == 0
    card = plan_budget(
        {
            "people": 3,
            "days": 1,
            "rooms": 1,
            "budget": 7000,
            "temple_id": "T0001",
            "travel": {
                "mode_asked": "bus",
                "distance_km": 60,
                "has_numbered_bus": True,
                "has_real_train": False,
            },
            "catalog": {
                "darshan": [{"name": "Sarva Darshan", "fee_inr": 0}],
                "sevas": [{"name": "Kalyanotsavam", "fee_inr": None}],
                "hotels": [{"name": "X", "min_inr": 800, "max_inr": 1500}],
            },
        }
    )
    assert card["input"]["nights"] == 0
    stay = next(x for x in card["verified"] if x["name"] == "stay")
    assert stay["min_inr"] == 0
    assert "bus ticket" in " ".join(card["unknown"])
    assert "₹288" not in format_budget(card)
    assert card["budget"]["can_say_within_budget"] is False
    assert "cannot judge" in card["budget"]["note"].lower()


def test_no_bus_means_no_bus_fare():
    card = plan_budget(
        {
            "people": 2,
            "days": 1,
            "travel": {
                "mode_asked": "bus",
                "distance_km": 400,
                "has_numbered_bus": False,
                "has_real_train": False,
            },
            "catalog": {"darshan": [], "sevas": [], "hotels": []},
        }
    )
    blob = " ".join(card["unknown"]).lower()
    assert "no numbered public bus" in blob
    text = format_budget(card)
    assert "TGSRTC" in text


def test_no_train_fare_when_travel_said_no():
    card = plan_budget(
        {
            "people": 1,
            "days": 1,
            "travel": {"mode_asked": "train", "has_real_train": False, "has_numbered_bus": False},
            "catalog": {"darshan": [], "sevas": [], "hotels": []},
        }
    )
    assert any("no real train" in u for u in card["unknown"])


def test_car_fuel_is_guess_not_ticket():
    card = plan_budget(
        {
            "people": 2,
            "days": 1,
            "fuel_type": "petrol",
            "vehicle_type": "small_car",
            "travel": {
                "mode_asked": "car",
                "distance_km": 60,
                "has_numbered_bus": True,
                "has_real_train": False,
            },
            "catalog": {"darshan": [{"name": "Sarva", "fee_inr": 0}], "sevas": [], "hotels": []},
        }
    )
    fuel = next(x for x in card["estimated"] if "fuel" in x["name"])
    assert fuel["status"] == "estimated"
    assert fuel["expected_inr"] and fuel["expected_inr"] > 0
    text = format_budget(card)
    assert "ESTIMATED" in text
    assert "VERIFIED" in text


def test_catalog_wire_sarva_free_seva_unknown():
    fixtures = ROOT / "tests" / "fixtures"
    card = plan_budget(
        {
            "temple_id": "T0001",
            "data_root": fixtures,
            "people": 3,
            "days": 1,
            "rooms": 1,
            "budget": 7000,
            "travel": {
                "mode_asked": "bus",
                "distance_km": 60,
                "has_numbered_bus": True,
                "has_real_train": False,
            },
        }
    )
    names = " ".join(x["name"] for x in card["verified"]).lower()
    assert "sarva" in names
    sarva = next(x for x in card["verified"] if "sarva" in x["name"].lower())
    assert sarva["min_inr"] == 0
    blob = " ".join(card["unknown"]).lower()
    assert "kalyanotsavam" in blob
    assert "vip" in blob or "seegra" in blob or "break" in blob
    assert card["budget"]["can_say_within_budget"] is False


def test_catalog_wire_overnight_uses_hotel_range():
    fixtures = ROOT / "tests" / "fixtures"
    card = plan_budget(
        {
            "temple_id": "T0001",
            "data_root": fixtures,
            "people": 2,
            "days": 2,
            "rooms": 1,
            "travel": {"mode_asked": "car", "distance_km": 65, "has_numbered_bus": False},
        }
    )
    stay = next(x for x in card["verified"] if "stay" in x["name"])
    assert stay["min_inr"] and stay["min_inr"] >= 300
    assert stay["max_inr"] and stay["max_inr"] >= stay["min_inr"]
    assert any("fuel" in x["name"] for x in card["estimated"])


def test_optimizer_forbids_fake_train():
    assert "train" not in allowed_optimizer_modes({"has_numbered_bus": True, "has_real_train": False})
    assert "bus" in allowed_optimizer_modes({"has_numbered_bus": True, "has_real_train": False})
    assert allowed_optimizer_modes({"has_numbered_bus": False, "has_real_train": False}) == ["car"]


def test_travel_plan_numbered_bus_still_unknown_fare():
    plan = {
        "mode": "transit",
        "train_found": False,
        "options": [
            {
                "mode_hint": "bus",
                "distance_km": 59.7,
                "steps": ["Take bus 113M from Barkatpura to Uppal"],
            },
            {"mode_hint": "car", "distance_km": 60.2, "steps": ["Drive to the temple — 89 min"]},
        ],
    }
    facts = travel_facts_from_plan(plan)
    assert facts["has_numbered_bus"] is True
    assert facts["has_real_train"] is False
    assert facts["distance_km"] == 60.2
    card = plan_budget(
        {
            "temple_id": "T0001",
            "people": 3,
            "days": 1,
            "budget": 7000,
            "travel_plan": plan,
            "catalog": {"darshan": [{"name": "Sarva", "fee_inr": 0}], "sevas": [], "hotels": []},
        }
    )
    assert any("bus ticket (no fare in our files)" in u for u in card["unknown"])
    assert card["budget"]["can_say_within_budget"] is False


def test_travel_plan_unnumbered_is_not_a_ticket():
    plan = {
        "mode": "transit",
        "train_found": False,
        "options": [
            {
                "mode_hint": "bus",
                "distance_km": 433,
                "steps": ["Take bus (number not given) from Adilabad to Mahabubnagar"],
            },
            {"mode_hint": "car", "distance_km": 394, "steps": ["Drive to the temple — 415 min"]},
        ],
    }
    facts = travel_facts_from_plan(plan)
    assert facts["has_numbered_bus"] is False
    card = plan_budget({"people": 2, "days": 1, "travel_plan": plan, "catalog": {}})
    text = format_budget(card)
    assert "TGSRTC" in text
    assert any("fuel" in x["name"] for x in card["estimated"])


def test_planner_lists_hotels_on_day_trip():
    fixtures = ROOT / "tests" / "fixtures"
    card = plan_budget(
        {
            "temple_id": "T0001",
            "data_root": fixtures,
            "people": 1,
            "days": 1,
            "travel": {"mode_asked": "car", "distance_km": 65, "has_numbered_bus": True},
        }
    )
    names = " ".join(h["name"] for h in card["lists"]["hotels"]).lower()
    assert "haritha" in names
    assert card["input"]["nights"] == 0
    text = format_budget(card)
    assert "STAY" in text
    assert "Day trip" in text
    assert "/night" in text
    assert "sevas" in text.lower() or "VIP" in text
    assert text.count("Kalyanotsavam fee") == 0
    assert "4-seat" not in text
    assert "seater" not in text.lower()
    assert "budget_engine" not in text
    assert "T0001" not in text


def test_car_fuel_band_is_15_to_20_kmpl():
    card = plan_budget(
        {
            "people": 1,
            "days": 1,
            "travel": {"mode_asked": "car", "distance_km": 60, "has_numbered_bus": False},
            "catalog": {"darshan": [{"name": "Sarva", "fee_inr": 0}], "sevas": [], "hotels": []},
        }
    )
    fuel = card["approx"]["car_fuel"]
    # 60/20*116 = 348; 60/15*116 = 464
    assert fuel["min_inr"] == 348
    assert fuel["max_inr"] == 464
    bus = card["approx"]["bus_guess"]
    assert bus["min_inr"] == 72
    assert bus["max_inr"] == 120


def test_honesty_six_fixes():
    fixtures = ROOT / "tests" / "fixtures"
    card = plan_budget(
        {
            "temple_id": "T0001",
            "data_root": fixtures,
            "people": 1,
            "days": 1,
        }
    )
    text = format_budget(card)
    assert "Sri Lakshmi Narasimha" in text
    assert "Known files only" not in text
    assert "No budget given" not in text
    assert "Origin not given" in text
    assert "COST WITHOUT TRAVEL" not in text or "Without travel" in text or "travel not included" in text.lower()
    assert card["input"]["origin_given"] is False
    # Fixture Annadanam is free → food min 0
    assert card["approx"]["food"]["min_inr"] == 0


def test_annadanam_when_restaurants_have_no_rupees():
    catalog = {
        "temple_name": "Sri Lakshmi Narasimha Swamy Temple",
        "free_meals": True,
        "road_km": 65,
        "darshan": [{"name": "Sarva Darshan", "fee_inr": 0}],
        "sevas": [],
        "hotels": [
            {"name": "Lodge A", "min_inr": 700, "max_inr": 1000},
            {"name": "Spectra Pride", "min_inr": 4000, "max_inr": 6500},
            {"name": "H1", "min_inr": 100, "max_inr": 100},
        ],
        "restaurants": [],
    }
    card = plan_budget({"people": 1, "days": 1, "catalog": catalog})
    text = format_budget(card)
    assert card["approx"]["food"]["min_inr"] == 0
    assert "Annadanam" in text or "CONDITIONAL" in text
    assert "Sri Lakshmi Narasimha" in text
    assert "Temple T0001" not in text
    assert "Origin not given" in text
    assert "No budget given" not in text
    listed = format_budget(plan_budget({"people": 1, "days": 1, "query": "how much hotels costs", "catalog": catalog}))
    assert "Spectra Pride" in listed
    assert "H1" in listed


def test_no_silent_hyderabad_in_total():
    card = plan_budget(
        {
            "people": 1,
            "days": 1,
            "catalog": {
                "temple_name": "Sanghi",
                "road_km": 35,
                "darshan": [{"name": "Sarva", "fee_inr": 10}],
                "sevas": [],
                "hotels": [],
            },
        }
    )
    assert card["input"]["origin_given"] is False
    assert card["approx"]["bus_guess"]["min_inr"] is None
    ts = card["approx"]["temple_side"]
    # darshan 10 + food estimate 320–650, no bus
    assert ts["min_inr"] >= 10
    assert "TRAVEL" in format_budget(card)
    assert "not in temple-side total" in format_budget(card).lower() or "Origin not given" in format_budget(card)


def test_parse_people_and_round_trip():
    from services.budget import parse_budget_slots

    s = parse_budget_slots("yadadri budget for 4 people 2 days round trip")
    assert s["people"] == 4
    assert s["days"] == 2
    assert s["round_trip"] is True
    assert parse_budget_slots("from hyderabad round trip 4 people")["origin"].lower() == "hyderabad"
    assert parse_budget_slots("from hyderabad one way")["origin"].lower() == "hyderabad"
    from services.budget import query_for_temple
    assert "warangal" not in query_for_temple("budget for yadadri from warangal").lower()
    assert "yadadri" in query_for_temple("budget for yadadri from warangal").lower()
    card = plan_budget(
        {
            "query": "from hyderabad round trip",
            "origin": "Hyderabad",
            "catalog": {
                "temple_name": "Yadadri",
                "road_km": 65,
                "darshan": [{"name": "Sarva", "fee_inr": 0}],
                "sevas": [],
                "hotels": [],
            },
        }
    )
    assert card["input"]["round_trip"] is True
    assert card["input"]["origin_given"] is True
    # one-way bus 65*1.2=78 → round 156
    assert card["approx"]["bus_guess"]["min_inr"] == 156


def test_ten_people_is_still_one_car_fuel():
    card = plan_budget(
        {
            "people": 10,
            "days": 1,
            "origin": "Hyderabad",
            "round_trip": True,
            "catalog": {
                "temple_name": "Sanghi",
                "road_km": 35,
                "darshan": [{"name": "Sarva", "fee_inr": 10}],
                "sevas": [],
                "hotels": [],
            },
        }
    )
    assert card["input"]["n_cars"] == 1
    # 1 vehicle × 70 km: 70/20*116=406; 70/15*116=541
    fuel = card["approx"]["car_fuel"]
    assert fuel["min_inr"] == 406
    assert fuel["max_inr"] == 541
    text = format_budget(card)
    assert "4-seat" not in text
    assert "3 cars" not in text
    assert "return unless you said round trip" not in text
    assert "35 km" in text
    assert "70 km" in text
    assert "TOTAL WITH BUS" in text
    assert "TOTAL WITH CAR" in text
    assert "OVERVIEW" in text
    assert card["approx"]["day_trip_car"]["max_inr"] == (
        card["approx"]["temple_side"]["max_inr"] + card["approx"]["car_fuel"]["max_inr"]
    )


def test_slot_patch_seven_seater():
    from services.budget import parse_slot_patch

    p = parse_slot_patch("no i am going on 7 seater car")
    assert p.get("car_seats") == 7
    assert parse_slot_patch("history of yadadri") == {}
    card = plan_budget(
        {
            "people": 10,
            "car_seats": 7,
            "origin": "Hyderabad",
            "round_trip": True,
            "catalog": {
                "temple_name": "Sanghi",
                "road_km": 35,
                "darshan": [{"name": "Sarva", "fee_inr": 10}],
                "sevas": [],
                "hotels": [],
            },
        }
    )
    assert card["input"]["n_cars"] == 1
    text = format_budget(card)
    assert "7-seat" not in text
    assert "2 car" not in text
    assert "TOTAL WITH BUS" in text
    assert "TOTAL WITH CAR" in text


def test_cars_needed_table():
    from services.budget import cars_needed, occupancy, parse_slot_patch

    assert cars_needed(1, 7) == 1
    assert cars_needed(7, 7) == 1
    assert cars_needed(8, 7) == 2
    assert cars_needed(10, 7) == 2
    assert cars_needed(14, 7) == 2
    assert cars_needed(15, 7) == 3
    assert cars_needed(10, 4) == 3
    assert cars_needed(10, 5) == 2
    assert occupancy(4)["passenger_capacity"] == 3
    assert occupancy(7)["passenger_capacity"] == 6
    assert occupancy(passenger_capacity=7)["total_seats"] == 8
    assert cars_needed(7, occupancy(4)["passenger_capacity"]) == 3
    assert cars_needed(7, occupancy(7)["passenger_capacity"]) == 2
    assert cars_needed(6, occupancy(7)["passenger_capacity"]) == 1
    assert cars_needed(10, occupancy(4)["passenger_capacity"]) == 4
    p = parse_slot_patch("no I am going in 7 seater car")
    assert p.get("car_seats") == 7
    assert p.get("passenger_capacity") == 6
    assert "people" not in p
    assert "origin" not in p
    assert p.get("round_trip") is None
    p2 = parse_slot_patch("7 passengers + driver")
    assert p2.get("passenger_capacity") == 7
    assert p2.get("car_seats") == 8


def test_khammam_origin_not_hyderabad_and_sevas_not_in_total():
    card = plan_budget(
        {
            "people": 1,
            "origin": "khammam",
            "catalog": {
                "temple_name": "Bhadrachalam",
                "road_km": 320,
                "darshan": [{"name": "Sarva Darshan", "fee_inr": 0, "code": "sarva"}],
                "sevas": [{"name": "Sita Rama Kalyanam", "fee_inr": 5000}],
                "hotels": [],
            },
        }
    )
    assert card["input"]["origin_given"] is True
    assert card["input"]["has_km"] is False
    text = format_budget(card)
    assert "Origin not given" not in text
    assert "khammam" in text.lower()
    assert "khammam" in text.lower()
    assert card["approx"]["temple_side"]["max_inr"] < 5000
    assert "not selected" in text.lower() or "not included" in text.lower()


def test_trip_state_yadadri_from_warangal_not_bhadrakali():
    from services.budget import merge_form, parse_budget_slots, query_for_temple

    q = "budget for yadadri from warangal"
    assert "warangal" not in query_for_temple(q).lower()
    assert "yadadri" in query_for_temple(q).lower()
    assert parse_budget_slots(q)["origin"].lower() == "warangal"
    form = merge_form({}, "budget for bhadrachalam from khammam")
    assert form["origin"].lower() == "khammam"
    form2 = merge_form(form, "budget for yadadri from warangal")
    assert form2["origin"].lower() == "warangal"
    assert "yadadri" in query_for_temple("budget for yadadri from warangal").lower()


def test_merge_form_only_requested_field_changes():
    from services.budget import merge_form

    form = merge_form({}, "budget for yadadri from hyderabad")
    assert form["origin"].lower() == "hyderabad"
    assert form["people"] is None
    form = merge_form({**form, "people": 1, "temple_id": "T0001"}, "make it 7 people")
    assert form["people"] == 7
    assert form["origin"].lower() == "hyderabad"
    assert form["round_trip"] is False
    form = merge_form(form, "actually from warangal")
    assert form["origin"].lower() == "warangal"
    assert form["people"] == 7
    form = merge_form(form, "make it round trip")
    assert form["round_trip"] is True
    assert form["origin"].lower() == "warangal"
    assert form["people"] == 7


def test_resolve_trip_km_asks_travel_not_hyderabad_catalog():
    from services.budget import resolve_trip_km

    calls = []

    def fake(tid, origin):
        calls.append((tid, origin))
        return {"distance_km": 115.0, "source": "google_maps_drive"}

    r = resolve_trip_km(
        origin="khammam",
        temple_id="T0002",
        hyd_km=320,
        drive_km_fn=fake,
    )
    assert r["distance_km"] == 115.0
    assert calls == [("T0002", "khammam")]
    assert "Hyderabad" not in (r["km_source"] or "")

    calls.clear()
    hyd = resolve_trip_km(
        origin="hyderabad",
        temple_id="T0001",
        hyd_km=65,
        drive_km_fn=fake,
    )
    assert hyd["distance_km"] == 65
    assert calls == []
    assert "catalog" in (hyd["km_source"] or "").lower()

    calls.clear()
    stale = {
        "temple_id": "T0001",
        "source": "hyderabad",
        "options": [{"mode_hint": "car", "distance_km": 10.9}],
    }
    r2 = resolve_trip_km(
        origin="khammam",
        temple_id="T0001",
        hyd_km=65,
        travel_plan=stale,
        drive_km_fn=fake,
    )
    assert r2["distance_km"] == 115.0
    assert r2["travel_plan_ok"] is False

    calls.clear()
    live = {
        "temple_id": "T0002",
        "source": "khammam",
        "options": [{"mode_hint": "car", "distance_km": 118}],
    }
    r3 = resolve_trip_km(
        origin="khammam",
        temple_id="T0002",
        hyd_km=320,
        travel_plan=live,
        drive_km_fn=fake,
    )
    assert r3["distance_km"] == 118
    assert r3["travel_plan_ok"] is True
    assert calls == []

    miss = resolve_trip_km(
        origin="warangal",
        temple_id="T0001",
        hyd_km=65,
        drive_km_fn=lambda *a: None,
    )
    assert miss["distance_km"] is None


def test_seven_people_by_car_is_one_vehicle_fuel():
    card = plan_budget(
        {
            "people": 7,
            "origin": "Hyderabad",
            "round_trip": True,
            "travel_mode": "car",
            "catalog": {
                "temple_name": "Yadadri",
                "road_km": 65,
                "darshan": [{"name": "Sarva Darshan", "fee_inr": 0}],
                "sevas": [],
                "hotels": [],
            },
        }
    )
    assert card["input"]["n_cars"] == 1
    # 130 km / 20 * 116 = 754; /15 * 116 = 1005
    assert card["approx"]["car_fuel"]["min_inr"] == 754
    assert card["approx"]["car_fuel"]["max_inr"] == 1005
    text = format_budget(card)
    assert "TRIP BUDGET" in text
    assert "4-seat" not in text
    assert "3 car" not in text
    assert "TOTAL WITH CAR" in text
    assert "TOTAL WITH BUS" not in text
    assert "65 km" in text
    assert "CAR" in text
    assert card["confidence"]["level"] == "medium"


def test_khammam_with_travel_km_uses_that_not_320():
    card = plan_budget(
        {
            "people": 1,
            "origin": "khammam",
            "km_source": "Travel Agent · Google Maps drive",
            "travel": {"distance_km": 115, "mode_asked": "car"},
            "catalog": {
                "temple_name": "Bhadrachalam",
                "road_km": 320,
                "darshan": [{"name": "Sarva Darshan", "fee_inr": 0}],
                "sevas": [{"name": "Sita Rama Kalyanam", "fee_inr": 5000}],
                "hotels": [],
            },
        }
    )
    assert card["input"]["has_km"] is True
    assert card["input"]["distance_km"] == 115
    text = format_budget(card)
    assert "115 km" in text
    assert "320 km" not in text
    assert "Travel Agent" not in text
    assert "budget_engine" not in text
    assert card["approx"]["temple_side"]["max_inr"] < 5000


def test_temple_aliases_stripped_from_origin():
    from services.budget import query_for_temple

    cases = [
        "budget for yadadri from warangal",
        "budget for yadagirigutta from khammam",
        "budget for yadadri narasimha from hyderabad",
        "budget for sanghi from uppal",
        "budget for vemulawada from warangal",
        "budget for basara from nizamabad",
        "budget for bhadrakali from warangal",
    ]
    for q in cases:
        cut = query_for_temple(q).lower()
        assert "from" not in cut
    assert "yadadri" in query_for_temple("budget for yadadri from warangal").lower()
    assert "bhadrakali" in query_for_temple("budget for bhadrakali from warangal").lower()


def test_cheapest_budget_is_an_estimate_only():
    card = plan_budget(
        {
            "query": "budget cheapest for yadadri from hyderabad",
            "origin": "hyderabad",
            "catalog": {
                "temple_name": "Yadadri",
                "road_km": 65,
                "darshan": [{"name": "Sarva Darshan", "fee_inr": 0}],
                "sevas": [],
                "hotels": [],
            },
        }
    )
    assert card["input"]["wants_cheapest"] is True
    text = format_budget(card)
    assert "CHEAPEST ESTIMATE" in text
    assert "guaranteed" in text.lower()
    assert "TOTAL WITH BUS" in text
    assert "TOTAL WITH CAR" in text
    assert "budget_engine" not in text



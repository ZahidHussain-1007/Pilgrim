import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.travel_bridge import (
    display_train_id,
    _is_train_seg,
    _mode_hint,
    _option_from_candidate,
    _recommend,
    _sane_option,
    _steps_from_segments,
    plan_to_temple,
    railway_dests,
)
from services.travel_intent import extract_travel_slots, parse_mode
from travel.agents.intent_agent import IntentAgent
from travel.core.google_client import google_destination
from travel.core.multimodal_router import RailRadarProvider, providers_for_mode


def test_display_train_keeps_real_numbers_only():
    assert display_train_id("12760") == "12760"
    assert display_train_id("47101 MMTS") == "47101"
    assert display_train_id("Goutami Express") == "Goutami Express"


def test_display_train_never_invents_or_uses_bus_ids():
    assert display_train_id("") == "(number not given)"
    assert display_train_id(None) == "(number not given)"
    assert display_train_id("284P") == "(number not given)"
    assert display_train_id("113M") == "(number not given)"
    assert display_train_id("500") == "(number not given)"
    assert display_train_id("Mythri Tours") == "(number not given)"


def test_bus_legs_are_not_trains_even_if_asked_train():
    segs = [
        {
            "mode": "bus",
            "from_stop": "Secunderabad",
            "to_stop": "Yadagirigutta",
            "route_id": "464",
            "duration_minutes": 90,
        }
    ]
    assert _is_train_seg(segs[0]) is False
    assert _mode_hint("google_maps route", "train", segs) == "bus"
    steps = _steps_from_segments(segs)
    assert steps[0].startswith("Take bus 464")
    assert "Take train" not in steps[0]


def test_real_train_leg_is_labeled_train():
    segs = [
        {
            "mode": "HEAVY_RAIL",
            "from_stop": "Secunderabad",
            "to_stop": "Raigir",
            "route_id": "12760",
            "duration_minutes": 40,
        }
    ]
    assert _mode_hint("google_maps route", "train", segs) == "train"
    steps = _steps_from_segments(segs)
    assert steps == ["Take train 12760 from Secunderabad to Raigir — 40 min"]


def test_mixed_train_then_bus_is_a_train_option():
    class Fake:
        summary = "google_maps route"
        segments = [
            {
                "mode": "train",
                "from_stop": "Secunderabad Jn",
                "to_stop": "Bhongir",
                "route_id": "67276",
                "duration_minutes": 50,
            },
            {
                "mode": "bus",
                "from_stop": "Bhongir",
                "to_stop": "Yadagirigutta",
                "route_id": "464",
                "duration_minutes": 30,
            },
        ]
        transfers = 1
        distance_km = 55
        duration_minutes = 80
        departure_time = None
        arrival_time = None

    option = _option_from_candidate(Fake(), "train", "rail")
    assert option["mode_hint"] == "train"
    assert "Take train 67276" in option["steps"][0]
    assert "Take bus 464" in option["steps"][1]


def test_no_train_recommendation_is_honest():
    text = _recommend(
        [
            {
                "mode_hint": "bus",
                "transfers": 2,
                "duration_minutes": 280,
            },
            {
                "mode_hint": "car",
                "transfers": 0,
                "duration_minutes": 90,
            },
        ],
        "train",
        nearest_railway="Raigir Railway Station (~5 km); Bhongir Railway Station as an alternative",
    )
    low = text.lower()
    assert "no real train" in low
    assert "will not invent" in low
    assert "raigir" in low


def test_railway_dests_split_t0001_style():
    names = railway_dests(
        {"nearest_railway": "Raigir Railway Station (~5 km); Bhongir Railway Station as an alternative"}
    )
    assert names[0] == "Raigir Railway Station"
    assert "Bhongir Railway Station" in names


def test_asked_train_but_only_buses_stays_honest(monkeypatch):
    from travel.core.models import RouteCandidate, TravelPlanResult, TripIntent

    class FakeOrch:
        def plan_resolved(self, source, destination, mode="transit", departure_time=None, preference="balanced", dest_pin=None):
            intent = TripIntent(source=source, destination=destination, mode=mode)
            route = RouteCandidate(
                route_id="fake-bus",
                summary="google_maps route from Secunderabad to Yadagirigutta",
                segments=[
                    {
                        "mode": "bus",
                        "from_stop": "Secunderabad",
                        "to_stop": "Yadagirigutta",
                        "route_id": "464",
                        "duration_minutes": 90,
                    }
                ],
                distance_km=60.0,
                duration_minutes=90,
                transfers=0,
            )
            return TravelPlanResult(query="", intent=intent, route=route)

    import services.travel_bridge as bridge

    monkeypatch.setattr(bridge, "_orchestrator", lambda: FakeOrch())
    result = plan_to_temple("T0001", source="Secunderabad", mode="train")
    assert result["train_found"] is False
    assert all(o["mode_hint"] != "train" for o in result["options"])
    assert any(o["mode_hint"] == "bus" for o in result["options"])
    assert "no real train" in result["recommendation"].lower()
    assert "raigir" in result["recommendation"].lower()
    assert any("will not invent" in w.lower() for w in result["warnings"])


def test_railradar_silent_on_bus_and_car():
    class Boom:
        def is_available(self):
            raise AssertionError("RailRadar must not run on bus/car")

        def lookup_stations(self):
            raise AssertionError("RailRadar must not run on bus/car")

    provider = RailRadarProvider(Boom(), "Hyderabad")
    assert provider.get_journeys("Secunderabad", "Raigir", mode="transit") == []
    assert provider.get_journeys("Secunderabad", "Raigir", mode="drive") == []


def test_providers_for_mode_hides_railradar_except_train():
    assert "railradar" not in providers_for_mode("transit")
    assert "railradar" not in providers_for_mode("drive")
    assert "railradar" in providers_for_mode("train")
    assert "gtfs" not in providers_for_mode("train")


def test_google_destination_uses_temple_pin():
    assert google_destination("Raigir Railway Station", "17.5886069,78.9412785") == "17.5886069,78.9412785"
    assert google_destination("Yadagirigutta", None) == "Yadagirigutta"


def test_crazy_car_is_dropped():
    facts = {"road_from_hyderabad_km": 65.0}
    assert _sane_option({"mode_hint": "car", "distance_km": 65, "duration_minutes": 90}, facts) is True
    assert _sane_option({"mode_hint": "car", "distance_km": 1526.6, "duration_minutes": 1674}, facts) is False


def test_parse_by_train_is_train():
    assert parse_mode("from secunderabad to yadadri by train") == "train"
    slots = extract_travel_slots("from secunderabad to yadadri by train")
    assert slots["mode"] == "train"
    intent = IntentAgent().parse("from Secunderabad to Yadagirigutta by train")
    assert intent.mode == "train"

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.travel_bridge import (
    destination_names,
    plan_to_temple,
    _load_temple,
    display_bus_id,
    _option_from_candidate,
    _boarding_penalty,
    collapse_route_clones,
    resolve_origin,
)


def test_needs_origin_does_not_need_a_from_city():
    result = plan_to_temple("T0001", source="")
    assert result["status"] == "needs_origin"
    assert result["temple_id"] == "T0001"
    assert "city" in result["question"].lower() or "station" in result["question"].lower()
    assert result["corpus_travel"]["road_from_hyderabad_km"] == 65.0


def test_unknown_temple_id():
    result = plan_to_temple("T9999", source="Secunderabad")
    assert result["status"] == "unknown_temple"


def test_nickname_rejected():
    result = plan_to_temple("yadadri", source="Secunderabad")
    assert result["status"] == "unknown_temple"


def test_t0001_destination_names_include_yadagirigutta():
    temple = _load_temple("T0001")
    names = [n.lower() for n in destination_names(temple)]
    blob = " ".join(names)
    assert "yadagirigutta" in blob
    assert names[0] != "sri lakshmi narasimha swamy temple".lower() or "yadagirigutta" in names[0]


def test_plan_to_temple_locks_t0001(monkeypatch):
    from travel.core.models import RouteCandidate, TravelPlanResult, TripIntent

    class FakeOrch:
        def plan_resolved(self, source, destination, mode="transit", departure_time=None, preference="balanced", dest_pin=None):
            intent = TripIntent(source=source, destination=destination, mode=mode)
            route = RouteCandidate(
                route_id="fake",
                summary=f"fake {source} -> {destination}",
                distance_km=65.0,
                duration_minutes=90,
            )
            return TravelPlanResult(query="", intent=intent, route=route)

    import services.travel_bridge as bridge

    monkeypatch.setattr(bridge, "_orchestrator", lambda: FakeOrch())
    result = plan_to_temple("T0001", source="Secunderabad")
    assert result["status"] == "ok"
    assert result["temple_id"] == "T0001"
    assert result["route"]["distance_km"] == 65.0
    assert any("yadagirigutta" in d.lower() or "yadadri" in d.lower() for d in result["destinations_tried"])


def test_display_bus_keeps_tsrtc_numbers():
    assert display_bus_id("113M") == "113M"
    assert display_bus_id("500") == "500"
    assert display_bus_id("29B/272G") == "29B/272G"
    assert display_bus_id("284P") == "284P"


def test_display_bus_hides_private_and_empty():
    assert display_bus_id("Mythri Tours And Travels") == "(number not given)"
    assert display_bus_id("") == "(number not given)"
    assert display_bus_id(None) == "(number not given)"


def test_car_collapses_to_one_line():
    class Fake:
        summary = "google_maps drive"
        segments = [
            {"mode": "driving", "from_stop": "A", "to_stop": "B", "duration_minutes": 10},
            {"mode": "driving", "from_stop": "B", "to_stop": "C", "duration_minutes": 20},
        ]
        transfers = 0
        distance_km = 60
        duration_minutes = 70
        departure_time = None
        arrival_time = None

    option = _option_from_candidate(Fake(), "drive", "car")
    assert option["mode_hint"] == "car"
    assert option["steps"] == ["Drive to the temple — 70 min"]


def test_mythri_ranks_worse_than_numbered_bus():
    mythri = {
        "steps": ["Take bus (number not given) from A to B"],
        "duration_minutes": 100,
        "transfers": 0,
    }
    tsrtc = {
        "steps": ["Take bus 113M from A to Uppal", "Take bus 500 from Uppal to B"],
        "duration_minutes": 200,
        "transfers": 1,
    }
    assert _boarding_penalty(tsrtc) < _boarding_penalty(mythri)


def test_collapse_same_500_464_spine():
    a = {
        "mode_hint": "bus",
        "steps": [
            "Walk to Barkatpura",
            "Take bus 113M from Barkatpura to Uppal — 28 min",
            "Take bus 500 from Uppal to Anantharam — 111 min",
            "Take bus 464 from Anantharam to Yadagirigutta — 58 min",
        ],
        "duration_minutes": 281,
        "transfers": 2,
        "distance_km": 59.7,
    }
    b = {
        "mode_hint": "bus",
        "steps": [
            "Walk to Himayath Nagar",
            "Take bus 113K from Himayath Nagar to Uppal — 30 min",
            "Take bus 500 from Uppal to Anantharam — 111 min",
            "Take bus 464 from Anantharam to Yadagirigutta — 58 min",
        ],
        "duration_minutes": 285,
        "transfers": 2,
        "distance_km": 60.7,
    }
    car = {
        "mode_hint": "car",
        "steps": ["Drive to the temple — 89 min"],
        "duration_minutes": 89,
        "transfers": 0,
        "distance_km": 60,
    }
    car2 = {
        "mode_hint": "car",
        "steps": ["Drive to the temple — 91 min"],
        "duration_minutes": 91,
        "transfers": 0,
        "distance_km": 61,
    }
    out = collapse_route_clones([a, b, car, car2], "bus")
    buses = [o for o in out if o["mode_hint"] == "bus"]
    cars = [o for o in out if o["mode_hint"] == "car"]
    assert len(buses) == 1
    assert len(cars) == 1
    assert cars[0]["duration_minutes"] == 89
    assert "113K" in (buses[0].get("note") or "")


def test_resolve_origin_without_maps(monkeypatch):
    class Dead:
        def is_available(self):
            return False

    monkeypatch.setattr(
        "travel.core.google_client.GoogleMapsClient",
        lambda *a, **k: Dead(),
    )
    hit = resolve_origin("suraram")
    assert hit["label"] == "suraram"
    assert hit["query"] == "suraram"

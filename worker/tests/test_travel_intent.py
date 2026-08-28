import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.travel_intent import is_route_query, extract_travel_slots
from services.travel_bridge import locations_for_travel


def test_how_to_reach_is_travel():
    assert is_route_query("how to reach yadadri") is True


def test_from_to_bus_is_travel():
    assert is_route_query("from Secunderabad to Yadadri by bus") is True


def test_darshan_is_not_travel():
    assert is_route_query("what are the darshan timings of yadadri") is False


def test_dress_is_not_travel():
    assert is_route_query("dress code of yadadri") is False


def test_hotels_is_not_travel():
    assert is_route_query("hotels near yadadri") is False


def test_food_is_not_travel():
    assert is_route_query("food near sanghi temple") is False


def test_hospital_is_not_travel():
    assert is_route_query("nearest hospital to yadadri") is False


def test_sevas_is_not_travel():
    assert is_route_query("sevas at yadadri") is False


def test_locations_for_t0001_has_geo():
    pack = locations_for_travel("T0001")
    assert pack["status"] == "ok"
    assert pack["temple_id"] == "T0001"
    assert pack["temple"]["lat"] is not None
    assert pack["temple"]["lng"] is not None
    assert pack["corpus_travel"]["road_from_hyderabad_km"] == 65.0
from services.travel_intent import extract_travel_slots


def test_full_sentence_fills_all_slots():
    slots = extract_travel_slots("from mehdipatnam to sanghi by bus")
    assert slots["source"] and slots["source"].lower() == "mehdipatnam"
    assert slots["destination"] and "sanghi" in slots["destination"].lower()
    assert slots["mode"] == "transit"


def test_how_to_reach_still_missing_origin():
    slots = extract_travel_slots("how to reach yadadri")
    assert not slots["source"]
    assert slots["mode"] is None
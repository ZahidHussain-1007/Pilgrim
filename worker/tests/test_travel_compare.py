import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "rag"))
sys.path.insert(0, str(ROOT / "services"))

from services.travel_intent import compare_kind, extract_travel_slots, parse_mode


def test_by_bus_wins_over_railway_station():
    assert parse_mode("from bhongir railway station to yadadri by bus") == "transit"


def test_by_train_still_train():
    assert parse_mode("from secunderabad to yadadri by train") == "train"


def test_bus_or_train_or_car_is_not_train():
    assert parse_mode("bus or train or car") is None
    assert compare_kind("bus or train or car") == "compare"


def test_cheapest_and_longest_kinds():
    assert compare_kind("cheapest way from uppal to yadadri") == "cheapest"
    assert compare_kind("longest way from uppal to yadadri") == "longest"
    assert compare_kind("fastest way from kukatpally to yadadri") == "fastest"


def test_to_from_word_order():
    slots = extract_travel_slots("which bus to yadagirigutta from uppal")
    assert slots["source"]
    assert "uppal" in slots["source"].lower()


def test_how_to_reach_from_city():
    slots = extract_travel_slots("how to reach from secunderabad by bus")
    assert slots["source"]
    assert "secunderabad" in slots["source"].lower()
    assert slots["mode"] == "transit"


def test_compare_format_does_not_invent_rupees():
    from services.travel_bridge import format_compare

    card = format_compare(
        {
            "compare": "cheapest",
            "temple_name": "Yadadri",
            "source": "uppal",
            "train_found": False,
            "cost_note": "Ticket / taxi rupees are not in our travel files. That is a budget-agent job. I will not invent ₹.",
            "rows": [
                {"mode": "bus", "km": 49.9, "minutes": 233},
                {"mode": "car", "km": 50.2, "minutes": 66},
            ],
            "corpus_travel": {},
        }
    )
    low = card.lower()
    assert "will not invent" in low
    assert "budget" in low
    assert "₹120" not in card
    assert "49.9 km" in card


def test_longest_sorts_km(monkeypatch):
    import services.travel_bridge as bridge

    def fake_plan(temple_id, source=None, mode="transit", departure_time=None):
        bus = {
            "mode_hint": "bus",
            "distance_km": 80.0,
            "duration_minutes": 300,
            "transfers": 2,
            "steps": ["Take bus 500 from A to B"],
        }
        car = {
            "mode_hint": "car",
            "distance_km": 60.0,
            "duration_minutes": 90,
            "transfers": 0,
            "steps": ["Drive to the temple — 90 min"],
        }
        if mode == "train":
            return {
                "status": "ok",
                "temple_id": temple_id,
                "train_found": False,
                "options": [bus, car],
                "corpus_travel": {},
            }
        return {
            "status": "ok",
            "temple_id": temple_id,
            "temple_name": "Yadadri",
            "options": [bus, car],
            "corpus_travel": {"nearest_railway": "Raigir"},
        }

    monkeypatch.setattr(bridge, "plan_to_temple", fake_plan)
    out = bridge.compare_to_temple("T0001", "uppal", kind="longest")
    assert [row["mode"] for row in out["rows"]] == ["car", "bus"]
    assert out["rows"][0]["km"] == 60.0
    cheap = bridge.compare_to_temple("T0001", "uppal", kind="cheapest")
    assert cheap["rows"][0]["mode"] == "bus"
    assert "will not invent" in cheap["cost_note"].lower()


def test_new_sentence_replaces_pending_origin(monkeypatch):
    from ask_service import ask
    import ask_service

    def fake_plan(temple_id, source=None, mode="transit", departure_time=None):
        return {
            "status": "ok",
            "temple_id": temple_id,
            "temple_name": "Sri Lakshmi Narasimha Swamy Temple",
            "source": source,
            "options": [
                {
                    "mode_hint": "bus",
                    "steps": [f"Take bus 113M from {source} to Uppal"],
                    "transfers": 1,
                    "distance_km": 59.7,
                    "duration_minutes": 281,
                    "live_source": "Google Maps Directions",
                }
            ],
            "recommendation": "ok",
            "corpus_travel": {},
            "attractions": [],
        }

    monkeypatch.setattr(ask_service, "plan_to_temple", fake_plan)
    _first, session = ask("from hyderabad to yadadri", {})
    assert session.get("pending_travel_mode")
    packed, session = ask("from narayanaguda to yadadri by bus", session)
    assert packed["status"] == "ok"
    assert "narayanaguda" in packed["answer"].lower()
    assert "from hyderabad." not in packed["answer"].lower()

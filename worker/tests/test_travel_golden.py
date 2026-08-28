"""Travel golden set.

Does not call Google Maps, Groq, or Qdrant.
Proves: route vs RAG, complete sentence, T0001=Yadadri, train=real or no,
boarding-card shape, food-on-the-way is catalog not Groq.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "rag"))
sys.path.insert(0, str(ROOT / "services"))

from services.travel_bridge import (
    _recommend,
    _sane_option,
    display_bus_id,
    display_train_id,
    railway_dests,
)
from services.travel_intent import extract_travel_slots, is_route_query, parse_mode
from services.travel_pins import is_on_way_followup

T0001_RAIL = "Raigir Railway Station (~5 km); Bhongir Railway Station as an alternative"

CANONICAL_BUS = {
    "mode_hint": "bus",
    "steps": [
        "Walk to Barkatpura Nala — 14 min",
        "Take bus 113M from Barkatpura Nala to Uppal — 28 min",
        "Take bus 500 from Uppal to Anantharam — 111 min",
        "Take bus 464 from Anantharam to Yadagirigutta — 58 min",
    ],
    "transfers": 2,
    "distance_km": 59.7,
    "duration_minutes": 281,
    "live_source": "Google Maps Directions",
}

CANONICAL_CAR = {
    "mode_hint": "car",
    "steps": ["Drive to the temple — 89 min"],
    "transfers": 0,
    "distance_km": 59.8,
    "duration_minutes": 89,
    "live_source": "Google Maps Directions",
}


def _fake_plan(temple_id, source=None, mode="transit", departure_time=None):
    facts = {
        "nearest_railway": T0001_RAIL,
        "nearest_bus": "Yadagirigutta Bus Stand (~1 km from temple)",
        "road_from_hyderabad_km": 65.0,
    }
    if mode == "train":
        return {
            "status": "ok",
            "temple_id": temple_id,
            "temple_name": "Sri Lakshmi Narasimha Swamy Temple",
            "source": source,
            "mode": mode,
            "options": [CANONICAL_BUS, CANONICAL_CAR],
            "recommendation": _recommend(
                [CANONICAL_BUS, CANONICAL_CAR],
                "train",
                nearest_railway=T0001_RAIL,
            ),
            "train_found": False,
            "warnings": [
                "No real train found from your start to this temple. I will not invent a train number."
            ],
            "corpus_travel": facts,
            "attractions": [],
        }
    return {
        "status": "ok",
        "temple_id": temple_id,
        "temple_name": "Sri Lakshmi Narasimha Swamy Temple",
        "source": source,
        "mode": mode,
        "options": [CANONICAL_BUS, CANONICAL_CAR],
        "recommendation": "Bus is cheaper (2 change(s), 281 min). Car is much faster (89 min, no change).",
        "corpus_travel": facts,
        "attractions": [{"name": "Surendrapuri Mythological Theme Park"}],
    }


def _load_ask():
    from ask_service import _format_travel, ask

    return ask, _format_travel


def test_route_yes():
    for query in (
        "how to reach yadadri",
        "from secunderabad to yadadri",
        "from narayanaguda to yadadri by bus",
        "from secunderabad to yadadri by train",
        "from mehdipatnam to sanghi by car",
        "how to go to yadagirigutta",
    ):
        assert is_route_query(query) is True, query


def test_route_no_stays_with_rag():
    for query in (
        "what are the darshan timings of yadadri",
        "dress code of yadadri",
        "sevas at yadadri",
        "hotels near yadadri",
        "food near sanghi temple",
        "nearest hospital to yadadri",
    ):
        assert is_route_query(query) is False, query


def test_complete_sentence_fills_slots():
    bus = extract_travel_slots("from mehdipatnam to sanghi by bus")
    assert bus["source"]
    assert "mehdipatnam" in bus["source"].lower()
    assert bus["mode"] == "transit"

    train = extract_travel_slots("from secunderabad to yadadri by train")
    assert train["mode"] == "train"
    assert parse_mode("car") == "drive"


def test_food_on_way_is_followup_hotels_near_is_not():
    assert is_on_way_followup("any food on the way?") is True
    assert is_on_way_followup("hotels near yadadri") is False


def test_t0001_is_yadadri_never_kondagattu():
    path = ROOT / "data" / "temples" / "T0001.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    blob = " ".join(
        [
            str(data.get("name") or ""),
            " ".join(str(x) for x in (data.get("alternate_names") or [])),
            str((data.get("location") or {}).get("village") or ""),
        ]
    ).lower()
    assert "yadadri" in blob or "yadagirigutta" in blob
    assert "kondagattu" not in blob
    rail = (data.get("travel") or {}).get("nearest_railway_station") or ""
    assert "raigir" in rail.lower()


def test_never_invent_bus_or_train_numbers():
    assert display_bus_id("113M") == "113M"
    assert display_bus_id("Mythri Tours") == "(number not given)"
    assert display_train_id("") == "(number not given)"
    assert display_train_id("284P") == "(number not given)"
    assert display_train_id("500") == "(number not given)"
    assert display_train_id("12760") == "12760"


def test_train_honesty_and_sane_car():
    rec = _recommend(
        [CANONICAL_BUS, CANONICAL_CAR],
        "train",
        nearest_railway=T0001_RAIL,
    )
    low = rec.lower()
    assert "no real train" in low
    assert "will not invent" in low
    assert "raigir" in low
    assert _sane_option(
        {"mode_hint": "car", "distance_km": 59.8, "duration_minutes": 89},
        {"road_from_hyderabad_km": 65},
    )
    assert not _sane_option(
        {"mode_hint": "car", "distance_km": 1526.6, "duration_minutes": 1674},
        {"road_from_hyderabad_km": 65},
    )
    assert "raigir" in " ".join(railway_dests({"nearest_railway": T0001_RAIL})).lower()


def test_boarding_card_shape():
    _ask, format_travel = _load_ask()
    card = format_travel(
        {
            "status": "ok",
            "temple_id": "T0001",
            "temple_name": "Sri Lakshmi Narasimha Swamy Temple",
            "source": "narayanaguda",
            "options": [CANONICAL_BUS, CANONICAL_CAR],
            "recommendation": "Bus is cheaper.",
            "corpus_travel": {"nearest_railway": T0001_RAIL},
            "attractions": [],
        }
    )
    low = card.lower()
    assert "way 1 — bus" in low
    assert "113m" in low and "500" in low and "464" in low
    assert "yadagirigutta" in low
    assert "drive to the temple — 89 min" in low
    assert "284p" not in low
    assert "take train" not in low


def test_ask_needs_origin(monkeypatch):
    ask, _ = _load_ask()
    import ask_service

    monkeypatch.setattr(ask_service, "plan_to_temple", _fake_plan)
    packed, session = ask("how to reach yadadri", {})
    assert packed["status"] == "needs_origin"
    assert packed["temple_id"] == "T0001"
    assert packed["entity"] == "travel"
    assert "city" in packed["answer"].lower() or "station" in packed["answer"].lower()
    assert session.get("pending_travel_origin")


def test_ask_needs_mode_when_source_present(monkeypatch):
    ask, _ = _load_ask()
    import ask_service

    monkeypatch.setattr(ask_service, "plan_to_temple", _fake_plan)
    packed, session = ask("from secunderabad to yadadri", {})
    assert packed["status"] == "needs_mode"
    assert packed["temple_id"] == "T0001"
    assert packed["entity"] == "travel"
    assert "bus" in packed["answer"].lower()
    assert session.get("pending_travel_mode")


def test_ask_complete_bus_sentence_does_not_reask(monkeypatch):
    ask, _ = _load_ask()
    import ask_service

    monkeypatch.setattr(ask_service, "plan_to_temple", _fake_plan)
    packed, session = ask("from narayanaguda to yadadri by bus", {})
    assert packed["status"] == "ok"
    assert packed["temple_id"] == "T0001"
    assert packed["entity"] == "travel"
    assert not session.get("pending_travel_origin")
    assert not session.get("pending_travel_mode")
    low = packed["answer"].lower()
    assert "way 1" in low
    assert "113m" in low
    assert session.get("last_travel", {}).get("temple_id") == "T0001"


def test_ask_train_does_not_invent_number(monkeypatch):
    ask, _ = _load_ask()
    import ask_service

    monkeypatch.setattr(ask_service, "plan_to_temple", _fake_plan)
    packed, _session = ask("from secunderabad to yadadri by train", {})
    assert packed["status"] == "ok"
    assert packed["temple_id"] == "T0001"
    low = packed["answer"].lower()
    assert "no real train" in low
    assert "raigir" in low
    assert "12760" not in low
    assert "take train" not in low


def test_ask_sanghi_car_locks_t0010(monkeypatch):
    ask, _ = _load_ask()
    import ask_service

    monkeypatch.setattr(ask_service, "plan_to_temple", _fake_plan)
    packed, session = ask("from mehdipatnam to sanghi by car", {})
    assert packed["status"] == "ok"
    assert packed["temple_id"] == "T0010"
    assert packed["entity"] == "travel"
    assert session.get("last_travel", {}).get("mode") == "drive"


def test_ask_how_to_reach_without_temple():
    ask, _ = _load_ask()
    packed, _session = ask("how to reach", {})
    assert packed["status"] == "needs_temple"
    assert packed["entity"] == "travel"


def test_ask_dakshina_kasi_route_is_ambiguous():
    ask, _ = _load_ask()
    packed, _session = ask("how to reach dakshina kasi", {})
    assert packed["status"] == "ambiguous"
    assert packed["temple_id"] is None


def test_food_on_the_way_uses_catalog_not_groq(monkeypatch):
    ask, _ = _load_ask()
    import ask_service

    def boom(*_a, **_k):
        raise AssertionError("Groq / retrieve must not run for food on the way")

    monkeypatch.setattr(ask_service, "generate_answer", boom)
    monkeypatch.setattr(ask_service, "retrieve", boom)
    session = {
        "last_travel": {
            "temple_id": "T0001",
            "option": {
                "steps": ["Take bus 500 from Uppal to Anantharam"],
                "via": ["Uppal"],
            },
            "source": "narayanaguda",
            "mode": "transit",
        }
    }
    packed, _session = ask("any food on the way?", session)
    assert packed["status"] == "ok"
    assert packed["entity"] == "travel"
    assert packed["intent"] == "route_pins"
    assert packed["sources"][0]["name"] == "catalog"
    assert "on this way" in packed["answer"].lower()


def test_hotels_near_is_not_travel_route():
    assert is_route_query("hotels near yadadri") is False
    assert is_on_way_followup("hotels near it") is False

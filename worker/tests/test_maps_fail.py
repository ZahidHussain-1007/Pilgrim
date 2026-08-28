import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import requests

from travel.core.google_client import GoogleMapsClient
from travel.core.multimodal_router import GoogleMapsProvider


class Boom500:
    status_code = 500

    def raise_for_status(self):
        raise requests.exceptions.HTTPError("500 Server Error")

    def json(self):
        return {}


def test_geocode_500_returns_none_does_not_crash(monkeypatch):
    monkeypatch.setattr("travel.core.google_client.requests.get", lambda *a, **k: Boom500())
    hit = GoogleMapsClient("test-key").geocode("adilabad")
    assert hit is None


def test_directions_500_returns_none(monkeypatch):
    monkeypatch.setattr("travel.core.google_client.requests.get", lambda *a, **k: Boom500())
    hit = GoogleMapsClient("test-key").directions("uppal", "yadadri", "transit")
    assert hit is None
    hit = GoogleMapsClient("test-key").directions("uppal", "yadadri", "drive")
    assert hit is None


def test_adilabad_8h_car_is_not_dropped():
    from services.travel_bridge import _sane_option

    temple = {"name": "Manyamkonda Lakshmi Venkateswara Swamy Temple", "location": {"village": "Manyamkonda", "district": "Mahabubnagar"}}
    assert _sane_option(
        {"mode_hint": "car", "distance_km": 380, "duration_minutes": 481},
        {"road_from_hyderabad_km": 100},
        temple,
    ) is True
    assert _sane_option(
        {"mode_hint": "car", "distance_km": 1526.6, "duration_minutes": 1674},
        {"road_from_hyderabad_km": 65},
        temple,
    ) is False


def test_tirupati_bus_dropped_for_manyamkonda():
    from services.travel_bridge import _sane_option, _recommend

    temple = {"name": "Manyamkonda Lakshmi Venkateswara Swamy Temple", "location": {"village": "Manyamkonda"}}
    junk = {
        "mode_hint": "bus",
        "distance_km": 755.9,
        "duration_minutes": 1075,
        "steps": ["Take bus (number not given) from Adilabad office to Tirupathi — 145 min"],
    }
    assert _sane_option(junk, {}, temple) is False
    unnumbered = {
        "mode_hint": "bus",
        "distance_km": 433.1,
        "duration_minutes": 885,
        "steps": [
            "Take bus (number not given) from Adilabad office to Kukatpally — 325 min",
            "Take bus (number not given) from Kukatpally to Mahabubnagar — 220 min",
        ],
    }
    assert _sane_option(unnumbered, {}, temple) is False
    numbered = {
        "mode_hint": "bus",
        "distance_km": 59.7,
        "duration_minutes": 281,
        "steps": ["Take bus 113M from Barkatpura Nala to Uppal — 28 min"],
    }
    assert _sane_option(numbered, {}, temple) is True
    rec = _recommend(
        [{"mode_hint": "car", "duration_minutes": 415, "distance_km": 393.5, "transfers": 0}],
        "transit",
        nearest_bus="Manyamkonda village bus stop",
    )
    assert "will not invent" in rec.lower()
    assert "palle velugu" in rec.lower() or "gamyam" in rec.lower()
    rec_empty = _recommend([], "transit", nearest_bus="Manyamkonda village bus stop")
    assert "yadagirigutta" not in rec.lower()
    assert "will not invent" in rec.lower()


def test_provider_geocode_500_returns_empty(monkeypatch):
    class Client:
        def is_available(self):
            return True

        def directions(self, *a, **k):
            return None

        def geocode(self, *a, **k):
            raise requests.exceptions.HTTPError("500 Server Error")

    assert GoogleMapsProvider(Client()).get_journeys("uppal", "yadadri", "transit") == []

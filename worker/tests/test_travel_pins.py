import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.travel_pins import catalog_pins, format_pins, is_on_way_followup, wants_route_pins, _label


def test_hotels_near_is_not_on_way_followup():
    assert is_on_way_followup("hotels near yadadri") is False


def test_eat_on_the_way_is_followup():
    assert is_on_way_followup("any food on the way?") is True
    assert wants_route_pins("from hyd to yadadri by bus where to eat") is True


def test_price_unknown_not_zero():
    assert _label({"name": "X", "min_inr": None, "max_inr": None}) == "X (price unknown)"
    assert "₹800" in _label({"name": "Y", "min_inr": 800, "max_inr": 1500})


def test_uppal_name_goes_on_way():
    option = {"steps": ["Take bus 500 from Uppal to Anantharam"], "via": []}
    hotels = {
        "on_the_way": [],
        "at_the_temple": [],
    }
    # unit the token split without live catalog
    from services.travel_attractions import tokens, route_tokens

    route = route_tokens(option)
    assert "uppal" in route
    assert tokens("Hotel Uppal Residency") & route
    assert not (tokens("Haritha Hotel Yadagirigutta") & route)
    _ = hotels
    _ = catalog_pins
    _ = format_pins

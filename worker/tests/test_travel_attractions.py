import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.travel_attractions import split_attractions


TEMPLE = {
    "temple_id": "T0001",
    "name": "Sri Lakshmi Narasimha Swamy Temple",
    "nearby_places": [
        "Surendrapuri Mythological Theme Park",
        "Bhongir Fort",
        "Kolanupaka Jain Temple",
        "Kolanupaka Someswara Temple",
    ],
}


def test_kolanupaka_not_on_lakdikapul_bus():
    option = {
        "steps": [
            "Take bus 113M from Lakdikapool to Uppal",
            "Take bus 500 from Uppal to Anantharam",
            "Take bus 464 from Anantharam to Yadagirigutta",
        ],
        "via": [],
    }
    split = split_attractions(TEMPLE, option)
    assert "Kolanupaka Jain Temple" not in split["on_the_way"]
    assert "Kolanupaka Jain Temple" in split["at_the_temple"]
    assert "Surendrapuri Mythological Theme Park" in split["at_the_temple"]


def test_bhongir_on_way_if_stop_says_bhongir():
    option = {
        "steps": [
            "Take bus 500 from Uppal to Bhongir",
            "Take bus 464 from Bhongir to Yadagirigutta",
        ],
        "via": [],
    }
    split = split_attractions(TEMPLE, option)
    assert "Bhongir Fort" in split["on_the_way"]

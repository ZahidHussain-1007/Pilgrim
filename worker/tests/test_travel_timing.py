import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.travel_timing import (
    darshan_travel_advice,
    parse_sarva_windows,
    target_from_query,
    windows_from_temple,
)


def test_parse_official_sarva_windows():
    text = (
        "Sarva Darshan windows: 7:00–9:00 AM, 10:00–11:45 AM, "
        "12:30–3:00 PM, 5:00–7:00 PM, and 8:15–9:00 PM."
    )
    windows = parse_sarva_windows(text)
    assert (7 * 60, 9 * 60) in windows
    assert any(start == 10 * 60 for start, _ in windows)


def test_target_7am_sarva():
    assert target_from_query("from hyd to yadadri by bus for 7 am sarva") == 7 * 60
    assert target_from_query("how to reach yadadri") is None


def test_leave_by_for_7am():
    advice = darshan_travel_advice("T0001", 180, "for 7 am sarva")
    assert advice
    assert "leave by" in advice.lower()
    assert "4:00 AM" in advice


def test_t0001_has_windows():
    path = ROOT / "data" / "temples" / "T0001.json"
    if not path.is_file():
        path = ROOT / "T0001.json"
    temple = json.loads(path.read_text(encoding="utf-8"))
    windows = windows_from_temple(temple)
    assert windows

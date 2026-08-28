from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

TRAVEL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_GTFS_DIR = TRAVEL_DIR / "gtfs"


def _gtfs_file(filename: str, env_name: str) -> str:
    """Use .env path only if that file really exists on THIS computer."""
    from_env = os.getenv(env_name)
    if from_env and Path(from_env).is_file():
        return from_env
    return str(DEFAULT_GTFS_DIR / filename)


GTFS_CONFIG = {
    "routes": _gtfs_file("routes.txt", "GTFS_ROUTES_PATH"),
    "trips": _gtfs_file("trips.txt", "GTFS_TRIPS_PATH"),
    "stop_times": _gtfs_file("stop_times.txt", "GTFS_STOP_TIMES_PATH"),
    "stops": _gtfs_file("stops.txt", "GTFS_STOPS_PATH"),
}

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN") or os.getenv("HF_TOKEN")
HUGGINGFACE_MODEL = os.getenv("HUGGINGFACE_MODEL", "HuggingFaceH4/zephyr-7b-beta")
RAILRADAR_API_KEY = os.getenv("RAILRADAR_API_KEY")
RAILRADAR_CITY = os.getenv("RAILRADAR_CITY", "Hyderabad")

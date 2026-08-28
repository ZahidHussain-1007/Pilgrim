from __future__ import annotations

import os
import re
from typing import Dict, Optional

import requests

_LATLNG = re.compile(r"^-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?$")


def google_destination(name: str, dest_pin: Optional[str] = None) -> str:
    """Prefer the temple lat,lng pin so Google does not drive to the wrong Raigir."""
    pin = (dest_pin or "").strip()
    if pin and _LATLNG.match(pin):
        return pin
    return (name or "").strip()


def _in_telangana(place: str) -> str:
    text = (place or "").strip()
    if not text or _LATLNG.match(text):
        return text
    if "india" in text.lower() or "telangana" in text.lower():
        return text
    return f"{text}, Telangana, India"


class GoogleMapsClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def geocode(self, query: str) -> Optional[Dict[str, object]]:
        if not self.api_key:
            return None
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": query, "key": self.api_key}
        try:
            response = requests.get(url, params=params, timeout=20)
            if response.status_code != 200:
                return None
            data = response.json()
        except (requests.RequestException, ValueError):
            return None
        if not data.get("results"):
            return None
        result = data["results"][0]
        loc = (result.get("geometry") or {}).get("location") or {}
        return {
            "formatted_address": result.get("formatted_address"),
            "lat": loc.get("lat"),
            "lon": loc.get("lng"),
        }

    def directions(self, origin: str, destination: str, mode: str = "transit") -> Optional[Dict[str, object]]:
        if not self.api_key or not origin or not destination:
            return None
        google_modes = {
            "drive": "driving",
            "walk": "walking",
            "bike": "bicycling",
            "bus": "transit",
            "train": "transit",
            "transit": "transit",
        }
        google_mode = google_modes.get(mode, mode)
        origin = _in_telangana(origin)
        destination = _in_telangana(destination)
        params = {
            "origin": origin,
            "destination": destination,
            "mode": google_mode,
            "alternatives": "true",
            "region": "in",
            "key": self.api_key,
        }
        if google_mode == "transit":
            import time
            import copy

            params["departure_time"] = str(int(time.time()))
            if mode == "train":
                params["transit_mode"] = "train|rail"
                try:
                    response = requests.get(
                        "https://maps.googleapis.com/maps/api/directions/json",
                        params=params,
                        timeout=20,
                    )
                    payload = response.json() if response.status_code == 200 else {}
                except (requests.RequestException, ValueError):
                    return None
                if payload.get("status") == "OK" and payload.get("routes"):
                    return payload
                return None

            params["transit_mode"] = "bus"
            merged = {"status": "OK", "routes": []}
            seen = set()
            for extra in ({"transit_routing_preference": "fewer_transfers"}, {}):
                p = copy.deepcopy(params)
                p.update(extra)
                try:
                    response = requests.get(
                        "https://maps.googleapis.com/maps/api/directions/json",
                        params=p,
                        timeout=20,
                    )
                    payload = response.json() if response.status_code == 200 else {}
                except requests.RequestException:
                    payload = {}
                for route in payload.get("routes") or []:
                    key = str(route.get("overview_polyline", {}).get("points", ""))[:80]
                    if key in seen:
                        continue
                    seen.add(key)
                    merged["routes"].append(route)
            return merged if merged["routes"] else None

        try:
            response = requests.get(
                "https://maps.googleapis.com/maps/api/directions/json",
                params=params,
                timeout=20,
            )
            data = response.json() if response.status_code == 200 else {}
        except (requests.RequestException, ValueError):
            return None
        return data if data.get("status") == "OK" and data.get("routes") else None

    def road_distance_km(self, origin: str, destination: str, mode: str = "driving") -> Optional[float]:
        data = self.directions(origin, destination, mode)
        if not data or not data.get("routes"):
            return None
        meters = sum(
            leg.get("distance", {}).get("value", 0)
            for leg in data["routes"][0].get("legs", [])
        )
        return float(meters) / 1000

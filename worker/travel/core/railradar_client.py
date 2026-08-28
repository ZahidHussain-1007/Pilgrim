from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests


class RailRadarClient:
    """Client for the verified RailRadar local-train lookup endpoint."""

    endpoint = "https://api.railradar.in/v1/lookup/trains/local"
    stations_endpoint = "https://api.railradar.in/v1/lookup/stations"
    trains_between_endpoint = "https://api.railradar.in/v1/trains/between"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("RAILRADAR_API_KEY")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def lookup_local_trains(self, city: str) -> List[Dict[str, Any]]:
        if not self.api_key or not city:
            return []

        try:
            response = requests.get(
                self.endpoint,
                params={"city": city},
                headers={"Authorization": self.api_key},
                timeout=20,
            )
            if response.status_code >= 400:
                return []
            payload = response.json()
        except (requests.RequestException, ValueError):
            return []
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("trains", "data", "results"):
                if isinstance(payload.get(key), list):
                    return payload[key]
                if isinstance(payload.get(key), dict):
                    return [
                        item
                        if isinstance(item, dict)
                        else {
                            "train_number": train_number,
                            "train_name": item,
                        }
                        for train_number, item in payload[key].items()
                        if isinstance(item, (dict, str))
                    ]
        return []

    def lookup_stations(self) -> Dict[str, str]:
        if not self.api_key:
            return {}
        try:
            response = requests.get(
                self.stations_endpoint,
                headers={"Authorization": self.api_key},
                timeout=20,
            )
            if response.status_code >= 400:
                return {}
            payload = response.json()
        except (requests.RequestException, ValueError):
            return {}
        data = payload.get("data", {}) if isinstance(payload, dict) else {}
        return {
            str(code): str(name)
            for code, name in data.items()
            if isinstance(data, dict) and isinstance(name, str)
        }

    def trains_between(self, from_code: str, to_code: str, date: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.api_key or not from_code or not to_code:
            return []
        params = {"date": date} if date else {}
        try:
            response = requests.get(
                f"{self.trains_between_endpoint}/{from_code}/{to_code}",
                params=params,
                headers={"Authorization": self.api_key},
                timeout=20,
            )
            if response.status_code >= 400:
                return []
            payload = response.json()
        except (requests.RequestException, ValueError):
            return []
        data = payload.get("data", {}) if isinstance(payload, dict) else {}
        trains = data.get("trains", []) if isinstance(data, dict) else []
        return trains if isinstance(trains, list) else []

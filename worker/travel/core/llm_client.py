from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import requests


class LLMIntentClient:
    """Kept on disk. Orchestrator v1 does not call this."""

    endpoint = "https://api-inference.huggingface.co/models/{model}"

    def __init__(self, api_token: Optional[str] = None, model: Optional[str] = None):
        self.api_token = api_token or os.getenv("HUGGINGFACE_API_TOKEN") or os.getenv("HF_TOKEN")
        self.model = model or os.getenv("HUGGINGFACE_MODEL", "HuggingFaceH4/zephyr-7b-beta")

    def extract_intent(self, query: str) -> Optional[Dict[str, Any]]:
        if not self.api_token or not query:
            return None

        prompt = (
            "Extract travel intent from the request. Return only valid JSON with these keys: "
            "source, destination, mode, departure_time, date, day_of_week, passengers, "
            "preference, avoid, requested_tools, confidence. "
            "requested_tools may contain only gtfs, google_maps, railradar. "
            "Use ISO date YYYY-MM-DD when a date is stated, and avoid must be an array. "
            f"Request: {query}"
        )
        try:
            response = requests.post(
                self.endpoint.format(model=self.model),
                headers={"Authorization": f"Bearer {self.api_token}"},
                json={"inputs": prompt, "parameters": {"max_new_tokens": 160, "return_full_text": False}},
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
            generated = payload[0].get("generated_text", "") if isinstance(payload, list) else ""
            start, end = generated.find("{"), generated.rfind("}")
            if start < 0 or end <= start:
                return None
            intent = json.loads(generated[start : end + 1])
            if not isinstance(intent, dict) or not intent.get("source") or not intent.get("destination"):
                return None
            intent["requested_tools"] = [
                tool
                for tool in intent.get("requested_tools", [])
                if tool in {"gtfs", "google_maps", "railradar"}
            ]
            intent["avoid"] = intent.get("avoid", []) if isinstance(intent.get("avoid", []), list) else []
            return intent
        except (requests.RequestException, ValueError, TypeError, KeyError):
            return None

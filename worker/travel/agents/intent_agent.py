from __future__ import annotations

import re
from datetime import date, timedelta

from travel.core.models import TripIntent


class IntentAgent:
    def parse(self, query: str) -> TripIntent:
        text = (query or "").strip()
        intent = TripIntent(raw_query=text)

        from_match = re.search(r"\bfrom\s+(.+?)\s+to\b", text, flags=re.IGNORECASE)
        if from_match:
            intent.source = from_match.group(1).strip(" ,.")

        to_match = re.search(r"\bto\s+(.+?)(?:\s+by\b|\s+at\b|\s+on\b|$)", text, flags=re.IGNORECASE)
        if to_match:
            intent.destination = to_match.group(1).strip(" ,.")

        if not intent.source and re.search(r"\bfrom\b", text, flags=re.IGNORECASE):
            intent.source = "unknown"
        if not intent.destination and re.search(r"\bto\b", text, flags=re.IGNORECASE):
            intent.destination = "unknown"

        mode = "transit"
        if re.search(r"\bby\s+bus\b|\bbus\b", text, flags=re.IGNORECASE):
            mode = "transit"
        elif re.search(r"\bby\s+train\b|\btrain\b|\brailway\b", text, flags=re.IGNORECASE):
            mode = "train"
        elif re.search(r"\bby\s+car\b|\bdriving\b|\bdrive\b|\btaxi\b|\bcab\b", text, flags=re.IGNORECASE):
            mode = "drive"
        elif re.search(r"\bwalking\b|\bwalk\b|\bon\s+foot\b", text, flags=re.IGNORECASE):
            mode = "walk"
        elif re.search(r"\bbicycle\b|\bbike\b|\bcycling\b", text, flags=re.IGNORECASE):
            mode = "bicycle"
        intent.mode = mode

        if re.search(r"fastest|quickest|least time", text, flags=re.IGNORECASE):
            intent.preference = "fastest"
        elif re.search(r"cheapest|lowest cost|budget", text, flags=re.IGNORECASE):
            intent.preference = "cheapest"
        elif re.search(r"no transfers?|fewer transfers?|direct|without changing", text, flags=re.IGNORECASE):
            intent.preference = "fewest_transfers"

        time_match = re.search(
            r"\b(?:at|around|by)\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b",
            text,
            flags=re.IGNORECASE,
        )
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            ampm = (time_match.group(3) or "").lower()
            if ampm == "pm" and hour < 12:
                hour += 12
            if ampm == "am" and hour == 12:
                hour = 0
            intent.departure_time = f"{hour:02d}:{minute:02d}"

        lowered = text.lower()
        if "tomorrow" in lowered:
            requested_date = date.today() + timedelta(days=1)
            intent.date = requested_date.isoformat()
            intent.day_of_week = requested_date.strftime("%A").lower()
            intent.day_hint = "tomorrow"
        elif "today" in lowered:
            requested_date = date.today()
            intent.date = requested_date.isoformat()
            intent.day_of_week = requested_date.strftime("%A").lower()
            intent.day_hint = "today"
        else:
            day_match = re.search(
                r"\b(mon(?:day)?|tue(?:sday)?|wed(?:nesday)?|thu(?:rsday)?|fri(?:day)?|sat(?:urday)?|sun(?:day)?)\b",
                lowered,
            )
            if day_match:
                intent.day_of_week = day_match.group(1).lower()
                intent.day_hint = day_match.group(1).lower()

        if re.search(r"parents?|family|children|kids|group", lowered):
            intent.passengers = "family"
        elif re.search(r"\b(\d+)\s*(?:people|passengers|persons)\b", lowered):
            intent.passengers = re.search(
                r"\b(\d+)\s*(?:people|passengers|persons)\b", lowered
            ).group(1)

        if re.search(r"avoid|without|no\s+many|few", lowered) and re.search(
            r"transfer|change", lowered
        ):
            intent.avoid.append("transfers")

        if intent.source and intent.destination:
            intent.confidence = 0.8
        else:
            intent.confidence = 0.4
        return intent

from __future__ import annotations

from typing import Any, Iterable, List, Optional

from travel.core.models import Journey, RouteCandidate, TransportLeg


ProviderLeg = TransportLeg
ProviderJourney = Journey


def providers_for_mode(mode: str) -> list[str]:
    """Which tools may run. RailRadar only when the pilgrim asked for a train."""
    asked = (mode or "transit").lower()
    if asked == "train":
        return ["google_maps", "railradar"]
    if asked in {"drive", "driving", "car"}:
        return ["google_maps"]
    return ["gtfs", "google_maps"]


class RouteProvider:
    provider_name: str = "base"

    def get_journeys(self, source: str, destination: str, mode: str = "transit") -> List[ProviderJourney]:
        return []


class GTFSRouteProvider(RouteProvider):
    provider_name = "gtfs"

    def __init__(self, planner: Any):
        self.planner = planner

    def _duration_minutes(self, departure_time: Optional[str], arrival_time: Optional[str]) -> Optional[int]:
        if not departure_time or not arrival_time:
            return None
        try:
            departure = self.planner._time_minutes(departure_time)
            arrival = self.planner._time_minutes(arrival_time)
        except AttributeError:
            return None
        if departure is None or arrival is None:
            return None
        return max(0, arrival - departure)

    def get_journeys(self, source: str, destination: str, mode: str = "transit") -> List[ProviderJourney]:
        raw_candidates = self.planner.find_candidate_routes(source, destination, limit=10, mode=mode)
        journeys: List[ProviderJourney] = []
        for route in raw_candidates:
            if not route.get("path"):
                continue
            legs = [
                ProviderLeg(
                    from_stop=segment["from_stop_id"],
                    to_stop=segment["to_stop_id"],
                    mode=segment.get("mode", mode),
                    route_id=segment.get("route_id"),
                    route_name=segment.get("route_name"),
                    distance_km=float(segment.get("distance_km", 0.0)),
                    duration_minutes=self._duration_minutes(
                        segment.get("departure_time"),
                        segment.get("arrival_time"),
                    ),
                    departure_time=segment.get("departure_time"),
                    arrival_time=segment.get("arrival_time"),
                )
                for segment in route.get("segments", [])
            ]
            journeys.append(
                ProviderJourney(
                    journey_id=f"{self.provider_name}-{route.get('route_id', 'route')}",
                    source=source,
                    destination=destination,
                    legs=legs,
                    transfers=int(route.get("transfers", 0)),
                    mode_changes=int(route.get("mode_changes", 0)),
                    distance_km=float(route.get("distance_km", 0.0)),
                    duration_minutes=route.get("duration_minutes"),
                    confidence=float(route.get("confidence", 0.8)),
                    provider=self.provider_name,
                )
            )
        return journeys


class GoogleMapsProvider(RouteProvider):
    provider_name = "google_maps"

    def __init__(self, client: Any | None = None):
        self.client = client

    def get_journeys(self, source: str, destination: str, mode: str = "transit") -> List[ProviderJourney]:
        try:
            return self._unsafe_journeys(source, destination, mode)
        except Exception:
            return []

    def _unsafe_journeys(self, source: str, destination: str, mode: str = "transit") -> List[ProviderJourney]:
        if not self.client or not self.client.is_available():
            return []
        data = self.client.directions(source, destination, mode)
        resolved_source = source
        resolved_destination = destination
        if not data or not data.get("routes"):
            regional_source = source if "telangana" in source.lower() else f"{source}, Telangana, India"
            regional_destination = (
                destination if "telangana" in destination.lower() else f"{destination}, Telangana, India"
            )
            data = self.client.directions(regional_source, regional_destination, mode)
            if data and data.get("routes"):
                resolved_source = regional_source
                resolved_destination = regional_destination
        if not data or not data.get("routes"):
            source_location = self.client.geocode(source)
            destination_location = self.client.geocode(destination)
            resolved_source = (source_location or {}).get("formatted_address", source)
            resolved_destination = (destination_location or {}).get("formatted_address", destination)
            if resolved_source != source or resolved_destination != destination:
                data = self.client.directions(resolved_source, resolved_destination, mode)
        if not data or not data.get("routes"):
            return []

        journeys: List[ProviderJourney] = []
        for index, route in enumerate(data.get("routes") or []):
            legs = []
            for route_leg in route.get("legs", []):
                for step in route_leg.get("steps", []):
                    transit = step.get("transit_details", {})
                    line = transit.get("line", {})
                    vehicle = line.get("vehicle", {}).get("type", "")
                    leg_mode = "transit" if transit else step.get("travel_mode", mode).lower()
                    if vehicle:
                        leg_mode = vehicle.lower()
                    start = (
                        (transit.get("departure_stop") or {}).get("name")
                        or step.get("start_address")
                        or resolved_source
                    )
                    end = (
                        (transit.get("arrival_stop") or {}).get("name")
                        or step.get("end_address")
                        or resolved_destination
                    )
                    mins = round(step.get("duration", {}).get("value", 0) / 60)
                    line_no = line.get("short_name") or line.get("name")
                    headsign = transit.get("headsign")
                    dep_txt = (transit.get("departure_time") or {}).get("text")
                    arr_txt = (transit.get("arrival_time") or {}).get("text")
                    if transit:
                        vehicle_l = (vehicle or "bus").lower()
                        if "bus" in vehicle_l or vehicle_l in {"", "transit"}:
                            instruction = f"Take bus {line_no or '(number not given)'} from {start} to {end}"
                        elif "rail" in vehicle_l or "train" in vehicle_l:
                            instruction = f"Take train {line_no or ''} from {start} to {end}".strip()
                        else:
                            instruction = f"Take {vehicle or 'transit'} {line_no or ''} from {start} to {end}".strip()
                        if headsign:
                            instruction += f" (towards {headsign})"
                        if mins:
                            instruction += f" — {mins} min"
                    else:
                        instruction = f"Walk {mins} min to {end}"
                    legs.append(
                        ProviderLeg(
                            from_stop=start,
                            to_stop=end,
                            mode=leg_mode,
                            route_id=line_no,
                            route_name=line.get("name") or line_no,
                            distance_km=float(step.get("distance", {}).get("value", 0)) / 1000,
                            duration_minutes=mins,
                            departure_time=dep_txt,
                            arrival_time=arr_txt,
                            instruction=instruction,
                            headsign=headsign,
                        )
                    )

            distance_km = sum(float(item.get("distance", {}).get("value", 0)) for item in route.get("legs", [])) / 1000
            duration_minutes = round(
                sum(float(item.get("duration", {}).get("value", 0)) for item in route.get("legs", [])) / 60
            )
            for i, leg in enumerate(legs):
                if str(leg.mode).lower() in {"walking", "walk"} and i + 1 < len(legs):
                    nxt = legs[i + 1]
                    if str(nxt.mode).lower() not in {"walking", "walk", "driving"}:
                        stop = nxt.from_stop
                        mins = leg.duration_minutes or 0
                        leg.instruction = f"Walk to {stop} stop" + (f" — {mins} min" if mins else "")
                        leg.to_stop = stop
            transit_legs = [leg for leg in legs if leg.mode not in ("walking", "driving", "bicycling")]
            journeys.append(
                ProviderJourney(
                    journey_id=f"{self.provider_name}-{source}-{destination}-{index}",
                    source=source,
                    destination=destination,
                    legs=legs,
                    transfers=max(0, len(transit_legs) - 1),
                    mode_changes=sum(1 for previous, current in zip(legs, legs[1:]) if previous.mode != current.mode),
                    distance_km=distance_km,
                    duration_minutes=duration_minutes,
                    confidence=0.7 - (index * 0.05),
                    provider=self.provider_name,
                    metadata={"summary": route.get("summary")},
                )
            )
        return journeys


class RailRadarProvider(RouteProvider):
    provider_name = "railradar"

    def __init__(self, client: Any | None = None, city: str = "Hyderabad"):
        self.client = client
        self.city = city

    def get_train_options(self) -> List[dict[str, Any]]:
        if not self.client or not self.client.is_available():
            return []
        return self.client.lookup_local_trains(self.city)

    def _station_code(self, place: str, stations: dict[str, str]) -> Optional[str]:
        normalized_place = "".join(character.lower() for character in place if character.isalnum())
        for code, name in stations.items():
            normalized_name = "".join(character.lower() for character in name if character.isalnum())
            if normalized_place == normalized_name or normalized_place in normalized_name:
                return code
        return None

    def _duration_minutes(self, value: Any) -> Optional[int]:
        if isinstance(value, (int, float)):
            return round(float(value) / 60) if value > 300 else round(float(value))
        if not isinstance(value, str) or ":" not in value:
            return None
        try:
            hours, minutes = value.split(":")[:2]
            return int(hours) * 60 + int(minutes)
        except ValueError:
            return None

    def get_journeys(self, source: str, destination: str, mode: str = "transit") -> List[ProviderJourney]:
        # Bus/car trips must not hit RailRadar (it 429'd and is not a bus planner).
        if mode != "train" or not self.client or not self.client.is_available():
            return []
        stations = self.client.lookup_stations()
        source_code = self._station_code(source, stations)
        destination_code = self._station_code(destination, stations)
        if not source_code or not destination_code:
            return []

        journeys = []
        for item in self.client.trains_between(source_code, destination_code):
            train = item.get("train", {})
            from_details = item.get("from", {})
            to_details = item.get("to", {})
            distance_km = float(item.get("distance", 0.0) or 0.0)
            duration_minutes = self._duration_minutes(item.get("duration"))
            journeys.append(
                ProviderJourney(
                    journey_id=f"{self.provider_name}-{train.get('number', 'train')}",
                    source=source,
                    destination=destination,
                    legs=[
                        ProviderLeg(
                            from_stop=stations[source_code],
                            to_stop=stations[destination_code],
                            mode="train",
                            route_id=str(train.get("number", "")) or None,
                            route_name=train.get("name"),
                            distance_km=distance_km,
                            duration_minutes=duration_minutes,
                            departure_time=from_details.get("departure"),
                            arrival_time=to_details.get("arrival"),
                        )
                    ],
                    distance_km=distance_km,
                    duration_minutes=duration_minutes,
                    confidence=0.85,
                    provider=self.provider_name,
                    metadata={"train_type": train.get("type"), "run_days": train.get("runDays", [])},
                )
            )
        return journeys


class MultimodalRouter:
    def __init__(self, providers: Iterable[RouteProvider] | Any | None = None):
        if providers is None:
            self.providers = []
        elif isinstance(providers, RouteProvider):
            self.providers = [providers]
        elif hasattr(providers, "find_candidate_routes"):
            self.providers = [GTFSRouteProvider(providers)]
        else:
            self.providers = list(providers)

    def _build_candidate(self, journey: ProviderJourney) -> RouteCandidate:
        return RouteCandidate(
            route_id=f"{journey.provider}-{journey.destination}",
            summary=f"{journey.provider} route from {journey.source} to {journey.destination}",
            segments=[
                {
                    "from_stop_id": leg.from_stop,
                    "to_stop_id": leg.to_stop,
                    "route_id": leg.route_id,
                    "route_name": leg.route_name,
                    "mode": leg.mode,
                    "distance_km": leg.distance_km,
                    "duration_minutes": leg.duration_minutes,
                    "departure_time": leg.departure_time,
                    "arrival_time": leg.arrival_time,
                }
                for leg in journey.legs
            ],
            confidence=float(journey.confidence),
            transfers=int(journey.transfers),
            mode_changes=int(journey.mode_changes),
            distance_km=float(journey.distance_km),
            duration_minutes=journey.duration_minutes,
            departure_time=journey.legs[0].departure_time if journey.legs else None,
            arrival_time=journey.legs[-1].arrival_time if journey.legs else None,
        )

    def _combine_journeys(self, first: ProviderJourney, second: ProviderJourney) -> Optional[ProviderJourney]:
        if not first.legs or not second.legs:
            return None
        if first.destination != second.source:
            return None

        first_leg = first.legs[-1]
        second_leg = second.legs[0]
        transit_modes = {"bus", "train", "tram", "subway", "transit"}
        transfer = int(
            first_leg.mode in transit_modes
            and second_leg.mode in transit_modes
            and first_leg.route_id != second_leg.route_id
        )
        duration_parts = [value for value in (first.duration_minutes, second.duration_minutes) if value is not None]
        return ProviderJourney(
            journey_id=f"multimodal-{first.journey_id}-{second.journey_id}",
            source=first.source,
            destination=second.destination,
            legs=first.legs + second.legs,
            transfers=first.transfers + second.transfers + transfer,
            mode_changes=first.mode_changes + second.mode_changes + int(first_leg.mode != second_leg.mode),
            distance_km=first.distance_km + second.distance_km,
            duration_minutes=sum(duration_parts) if len(duration_parts) == 2 else None,
            confidence=min(first.confidence, second.confidence),
            provider="multimodal",
            metadata={"providers": [first.provider, second.provider]},
        )

    def generate_candidates(
        self, source: str, destination: str, mode: str = "transit", preference: str = "balanced"
    ) -> List[RouteCandidate]:
        journeys: List[ProviderJourney] = []
        for provider in self.providers:
            try:
                journeys.extend(provider.get_journeys(source, destination, mode))
            except Exception:
                continue

        combined = [
            journey
            for first in journeys
            for second in journeys
            if (journey := self._combine_journeys(first, second)) is not None
            and journey.source == source
            and journey.destination == destination
        ]
        ranked = [self._build_candidate(journey) for journey in journeys + combined]
        if preference == "fewest_transfers":
            for candidate in ranked:
                candidate.confidence = 0.9 - (candidate.transfers * 0.05)

        if not ranked:
            return []

        ranked.sort(key=lambda item: (item.transfers, item.distance_km, item.duration_minutes or 0))
        return ranked

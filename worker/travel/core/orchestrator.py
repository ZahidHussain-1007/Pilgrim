from __future__ import annotations

from typing import Optional

from travel.agents.intent_agent import IntentAgent
from travel.core.google_client import GoogleMapsClient, google_destination
from travel.core.gtfs_engine import GTFSLoader, GTFSPlanner
from travel.core.models import CandidateStop, RouteCandidate, TravelPlanResult, TripIntent
from travel.core.multimodal_router import (
    GTFSRouteProvider,
    GoogleMapsProvider,
    MultimodalRouter,
    RailRadarProvider,
    providers_for_mode,
)
from travel.core.railradar_client import RailRadarClient
from travel.core.settings import (
    GOOGLE_MAPS_API_KEY,
    GTFS_CONFIG,
    RAILRADAR_API_KEY,
    RAILRADAR_CITY,
)
from travel.core.web_fallback import WebFallbackService


class TravelAgentOrchestrator:
    _shared_planner = None

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.intent_agent = IntentAgent()
        self.google_client = GoogleMapsClient(GOOGLE_MAPS_API_KEY)
        self.railradar_client = RailRadarClient(RAILRADAR_API_KEY)
        self.railradar_provider = RailRadarProvider(self.railradar_client, RAILRADAR_CITY)
        self.web_fallback = WebFallbackService()

        if TravelAgentOrchestrator._shared_planner is None:
            print("Loading bus map (first time can take 1–2 minutes)...")
            gtfs_loader = GTFSLoader(
                GTFS_CONFIG["routes"],
                GTFS_CONFIG["trips"],
                GTFS_CONFIG["stop_times"],
                GTFS_CONFIG["stops"],
            )
            self.gtfs_data = gtfs_loader.load()
            TravelAgentOrchestrator._shared_planner = GTFSPlanner(self.gtfs_data)
            print("Bus map loaded.")
        self.gtfs_planner = TravelAgentOrchestrator._shared_planner
        self.gtfs_data = self.gtfs_planner.data
        self.multimodal_router = MultimodalRouter(
            [
                GTFSRouteProvider(self.gtfs_planner),
                GoogleMapsProvider(self.google_client),
                self.railradar_provider,
            ]
        )

    def _resolve_intent(self, query: str) -> TripIntent:
        return self.intent_agent.parse(query)

    def _selected_providers(self, intent: TripIntent):
        providers = {
            "gtfs": GTFSRouteProvider(self.gtfs_planner),
            "google_maps": GoogleMapsProvider(self.google_client),
            "railradar": self.railradar_provider,
        }
        selected_tools = list(intent.requested_tools or [])
        if not selected_tools:
            selected_tools = providers_for_mode(intent.mode)
        elif "railradar" in selected_tools and (intent.mode or "") != "train":
            selected_tools = [name for name in selected_tools if name != "railradar"]
        return [providers[name] for name in selected_tools if name in providers]

    def plan(self, query: str) -> TravelPlanResult:
        """Door 1: natural language. Parses 'from A to B'."""
        intent = self._resolve_intent(query)
        return self._plan_from_intent(query, intent, geocode=True)

    def plan_resolved(
        self,
        source: str,
        destination: str,
        mode: str = "transit",
        departure_time: Optional[str] = None,
        preference: str = "balanced",
        dest_pin: Optional[str] = None,
    ) -> TravelPlanResult:
        """Door 2: official names already chosen (temple id → Yadagirigutta).

        dest_pin is lat,lng so Google hits the temple hill, not another shrine.
        """
        source = (source or "").strip()
        destination = (destination or "").strip()
        intent = TripIntent(
            source=source or None,
            destination=destination or None,
            mode=mode or "transit",
            departure_time=departure_time,
            preference=preference or "balanced",
            raw_query=f"from {source} to {destination}",
            confidence=1.0 if source and destination else 0.0,
        )
        query = intent.raw_query
        return self._plan_from_intent(query, intent, geocode=False, dest_pin=dest_pin)

    def _plan_from_intent(
        self, query: str, intent: TripIntent, geocode: bool, dest_pin: Optional[str] = None
    ) -> TravelPlanResult:
        result = TravelPlanResult(query=query, intent=intent, data_sources_used=[])

        if not intent.source or not intent.destination or intent.source == "unknown" or intent.destination == "unknown":
            result.warnings.append("Source or destination could not be confidently extracted from the query.")
            result.fallback_used = True
            return result

        source_match = self.gtfs_planner.find_stop_matches(intent.source)[:1]
        destination_match = self.gtfs_planner.find_stop_matches(intent.destination)[:1]

        if source_match:
            result.matched_source = CandidateStop(
                stop_id=source_match[0].get("stop_id", "unknown"),
                stop_name=source_match[0].get("stop_name", intent.source),
                source="gtfs",
                score=source_match[0].get("score", 0.0),
            )
            result.data_sources_used.append("gtfs")
        if destination_match:
            result.matched_destination = CandidateStop(
                stop_id=destination_match[0].get("stop_id", "unknown"),
                stop_name=destination_match[0].get("stop_name", intent.destination),
                source="gtfs",
                score=destination_match[0].get("score", 0.0),
            )
            if "gtfs" not in result.data_sources_used:
                result.data_sources_used.append("gtfs")

        if geocode and self.google_client.is_available():
            result.data_sources_used.append("google_maps")
            if intent.source:
                geo_source = self.google_client.geocode(intent.source)
                if geo_source:
                    result.warnings.append("Google Maps geocoding used for origin context.")
            if intent.destination:
                geo_dest = self.google_client.geocode(intent.destination)
                if geo_dest:
                    result.warnings.append("Google Maps geocoding used for destination context.")

        route = None
        # GTFS is a bus map. Do not treat a bus path as a train.
        if (
            result.matched_source
            and result.matched_destination
            and (intent.mode or "transit") not in {"train", "drive", "driving", "car"}
        ):
            route = self.gtfs_planner.plan_from_gtfs(
                intent.source,
                intent.destination,
                intent.mode,
                intent.departure_time,
                intent.preference,
            )

        self.multimodal_router.providers = self._selected_providers(intent)
        provider_candidates = self.multimodal_router.generate_candidates(
            intent.source,
            intent.destination,
            intent.mode,
            intent.preference,
        )
        if route or provider_candidates:
            if route:
                result.route = RouteCandidate(
                    route_id=route["route_id"],
                    summary=route["summary"],
                    segments=route.get("segments", []),
                    confidence=route["confidence"],
                    transfers=route.get("transfers", 0),
                    mode_changes=route.get("mode_changes", 0),
                    distance_km=route.get("distance_km", 0.0),
                    duration_minutes=route.get("duration_minutes"),
                    departure_time=route.get("departure_time"),
                    arrival_time=route.get("arrival_time"),
                )
                result.alternatives = provider_candidates[:5]
                if not result.alternatives:
                    result.alternatives = [
                        RouteCandidate(
                            route_id="alternative",
                            summary=(
                                f"Alternative GTFS route via {' -> '.join(item['path'])}; "
                                f"{item['transfers']} transfer(s)"
                            ),
                            segments=item.get("segments", []),
                            confidence=0.7,
                            transfers=item.get("transfers", 0),
                            mode_changes=item.get("mode_changes", 0),
                            distance_km=item.get("distance_km", 0.0),
                            duration_minutes=item.get("duration_minutes"),
                            departure_time=item.get("departure_time"),
                            arrival_time=item.get("arrival_time"),
                        )
                        for item in route.get("alternatives", [])
                    ]
            else:
                result.route = provider_candidates[0]
                result.alternatives = provider_candidates[1:6]
            result.fallback_used = False
            return result

        web_options = self.web_fallback.search(query)
        if web_options:
            result.data_sources_used.append("web_fallback")
            result.fallback_used = True
            result.warnings.append(
                f"No provider route was found. Web fallback found related public information: {web_options[0].get('title', 'result')}"
            )
            return result

        result.warnings.append(
            "No provider route match found. Need clarification or additional data sources before answering."
        )
        result.fallback_used = True
        return result

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TripIntent:
    source: Optional[str] = None
    destination: Optional[str] = None
    mode: str = "transit"
    departure_time: Optional[str] = None
    date: Optional[str] = None
    day_of_week: Optional[str] = None
    day_hint: Optional[str] = None
    passengers: Optional[str] = None
    preference: str = "balanced"
    avoid: List[str] = field(default_factory=list)
    requested_tools: List[str] = field(default_factory=list)
    raw_query: str = ""
    confidence: float = 0.0


@dataclass
class CandidateStop:
    stop_id: str
    stop_name: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    source: str = "gtfs"
    score: float = 0.0


@dataclass
class RouteCandidate:
    route_id: Optional[str]
    summary: str
    segments: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    transfers: int = 0
    mode_changes: int = 0
    distance_km: float = 0.0
    duration_minutes: Optional[int] = None
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None


@dataclass
class TransportLeg:
    from_stop: str
    to_stop: str
    mode: str
    route_id: Optional[str] = None
    route_name: Optional[str] = None
    distance_km: float = 0.0
    duration_minutes: Optional[int] = None
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    instruction: Optional[str] = None
    headsign: Optional[str] = None


@dataclass
class Journey:
    journey_id: str
    source: Optional[str] = None
    destination: Optional[str] = None
    legs: List[TransportLeg] = field(default_factory=list)
    transfers: int = 0
    mode_changes: int = 0
    distance_km: float = 0.0
    duration_minutes: Optional[int] = None
    confidence: float = 0.0
    provider: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TravelPlanResult:
    query: str
    intent: TripIntent
    route: Optional[RouteCandidate] = None
    alternatives: List[RouteCandidate] = field(default_factory=list)
    matched_source: Optional[CandidateStop] = None
    matched_destination: Optional[CandidateStop] = None
    data_sources_used: List[str] = field(default_factory=list)
    fallback_used: bool = False
    warnings: List[str] = field(default_factory=list)

    def to_cli_text(self) -> str:
        lines: List[str] = []
        lines.append(f"Query: {self.query}")
        lines.append(f"Intent: {self.intent}")
        lines.append(
            f"Data sources: {', '.join(self.data_sources_used) if self.data_sources_used else 'none'}"
        )
        if self.matched_source:
            lines.append(
                f"Source match: {self.matched_source.stop_name} ({self.matched_source.stop_id})"
            )
        if self.matched_destination:
            lines.append(
                f"Destination match: {self.matched_destination.stop_name} ({self.matched_destination.stop_id})"
            )
        if self.route:
            lines.append(f"Route: {self.route.summary}")
            lines.append(
                f"Transfers: {self.route.transfers}; distance: {self.route.distance_km:.1f} km"
            )
            if self.route.duration_minutes is not None:
                lines.append(f"Duration: {self.route.duration_minutes} minutes")
        if self.alternatives:
            lines.append("Alternatives:")
            for alternative in self.alternatives:
                lines.append(f"  - {alternative.summary}")
        if self.warnings:
            lines.append("Warnings:")
            for warning in self.warnings:
                lines.append(f"  - {warning}")
        return "\n".join(lines)

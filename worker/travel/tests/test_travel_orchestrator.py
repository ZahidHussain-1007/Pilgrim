from travel.core.orchestrator import TravelAgentOrchestrator
from travel.core.models import RouteCandidate
from travel.core.railradar_client import RailRadarClient


def test_orchestrator_uses_gtfs_for_known_route():
    orchestrator = TravelAgentOrchestrator()
    result = orchestrator.plan("from Secunderabad to Yadagirigutta by bus")

    assert result.matched_source is not None
    assert result.matched_destination is not None
    assert result.route is not None
    assert "gtfs" in result.data_sources_used


def test_orchestrator_handles_missing_place_gracefully():
    orchestrator = TravelAgentOrchestrator()
    result = orchestrator.plan("from NowhereLand to MysteryPlace by bus")

    assert result.fallback_used is True
    assert result.route is None
    assert len(result.warnings) >= 1


def test_railradar_client_normalizes_train_map_payload(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"success": True, "data": {"47101": {"trainNumber": "47101"}}}

    monkeypatch.setattr(
        "travel.core.railradar_client.requests.get",
        lambda *args, **kwargs: FakeResponse(),
    )

    trains = RailRadarClient("test-key").lookup_local_trains("Hyderabad")

    assert trains == [{"trainNumber": "47101"}]


def test_orchestrator_uses_provider_route_without_gtfs_match(monkeypatch):
    orchestrator = TravelAgentOrchestrator()
    provider_route = RouteCandidate(
        route_id="google-maps-route",
        summary="google_maps route from Hyderabad to Warangal",
        confidence=0.7,
        distance_km=145.0,
        duration_minutes=180,
    )
    monkeypatch.setattr(
        orchestrator.multimodal_router,
        "generate_candidates",
        lambda *args, **kwargs: [provider_route],
    )

    result = orchestrator.plan("from Hyderabad to Warangal by car")

    assert result.route is provider_route
    assert result.fallback_used is False


def test_google_client_maps_internal_modes_to_google_modes(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"status": "OK", "routes": []}

    def fake_get(url, **kwargs):
        captured.update(kwargs)
        return FakeResponse()

    monkeypatch.setattr("travel.core.google_client.requests.get", fake_get)

    from travel.core.google_client import GoogleMapsClient

    GoogleMapsClient("test-key").directions("Parigi", "Basara", "drive")

    assert captured["params"]["mode"] == "driving"


def test_web_fallback_is_empty():
    from travel.core.web_fallback import WebFallbackService

    assert WebFallbackService().search("from A to B") == []


def test_intent_skips_huggingface():
    from travel.agents.intent_agent import IntentAgent

    intent = IntentAgent().parse("from Secunderabad to Yadagirigutta by bus at 8 am")
    assert intent.source == "Secunderabad"
    assert intent.destination == "Yadagirigutta"
    assert intent.departure_time == "08:00"


def test_plan_resolved_does_not_parse_sentence():
    orchestrator = TravelAgentOrchestrator()
    result = orchestrator.plan_resolved("Secunderabad", "Yadagirigutta", mode="transit")

    assert result.intent.source == "Secunderabad"
    assert result.intent.destination == "Yadagirigutta"
    assert result.intent.confidence == 1.0
    assert result.matched_source is not None
    assert "Google Maps geocoding used for destination context." not in result.warnings


def test_plan_resolved_missing_source_asks():
    orchestrator = TravelAgentOrchestrator()
    result = orchestrator.plan_resolved("", "Yadagirigutta")

    assert result.fallback_used is True
    assert result.route is None
    assert result.intent.source is None
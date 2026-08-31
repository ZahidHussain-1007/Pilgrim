"""Regression tests for the active FastAPI adapter contract."""

import os
import unittest

from fastapi.testclient import TestClient


os.environ.setdefault("RAG_AGENT_URL", "http://rag-agent.test")

from worker.main import app
from worker.routes.chat import get_rag_service
from worker.schemas.response import ChatResponse
from worker.services.rag_service import RagAgentError, RagAgentTimeoutError


class FakeRagService:
    def __init__(self, result: ChatResponse | Exception) -> None:
        self._result = result

    async def answer(self, _request):
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


class FastApiAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def _use_rag_result(self, result: ChatResponse | Exception) -> None:
        app.dependency_overrides[get_rag_service] = lambda: FakeRagService(result)

    def test_health(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_chat_rejects_invalid_request(self) -> None:
        response = self.client.post("/chat", json={"query": ""})

        self.assertEqual(response.status_code, 422)

    def test_chat_returns_public_response_contract(self) -> None:
        self._use_rag_result(
            ChatResponse(
                answer="Darshan starts at 6 AM.",
                sources=[{"name": "official schedule"}],
                language="en",
            )
        )

        response = self.client.post(
            "/chat",
            json={"query": "What are the darshan timings?", "temple": "Yadadri", "language": "en"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "answer": "Darshan starts at 6 AM.",
                "sources": [{"name": "official schedule"}],
                "language": "en",
            },
        )

    def test_chat_maps_rag_failure_to_502(self) -> None:
        self._use_rag_result(RagAgentError())

        response = self.client.post("/chat", json={"query": "hello", "language": "en"})

        self.assertEqual(response.status_code, 502)

    def test_chat_maps_rag_timeout_to_504(self) -> None:
        self._use_rag_result(RagAgentTimeoutError())

        response = self.client.post("/chat", json={"query": "hello", "language": "en"})

        self.assertEqual(response.status_code, 504)

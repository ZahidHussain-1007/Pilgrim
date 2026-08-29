"""Boundary between the worker API and the separately deployed RAG agent."""

import httpx

from worker.config.settings import Settings
from worker.schemas.chat import ChatRequest
from worker.schemas.response import ChatResponse


class RagAgentError(Exception):
    """A non-timeout failure returned by the RAG agent."""


class RagAgentTimeoutError(RagAgentError):
    """The RAG agent did not respond before the configured timeout."""


class RagService:
    """Forwards chat requests without depending on RAG implementation details."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def answer(self, request: ChatRequest) -> ChatResponse:
        url = f"{str(self._settings.rag_agent_url).rstrip('/')}{self._settings.rag_agent_chat_path}"
        payload = request.model_dump(exclude_none=True)

        try:
            async with httpx.AsyncClient(timeout=self._settings.rag_agent_timeout_seconds) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                body = response.json()
        except httpx.TimeoutException as error:
            raise RagAgentTimeoutError("RAG agent timed out") from error
        except (httpx.HTTPError, ValueError) as error:
            raise RagAgentError("RAG agent returned an invalid response") from error

        if not isinstance(body, dict):
            raise RagAgentError("RAG agent response must be a JSON object")

        # The legacy `reply` field is accepted only while the RAG Agent migrates
        # to the canonical `answer` field; the worker always exposes `answer`.
        answer = body.get("answer") or body.get("reply")
        if not isinstance(answer, str) or not answer.strip():
            raise RagAgentError("RAG agent response does not contain an answer")

        sources = body.get("sources", [])
        if not isinstance(sources, list):
            sources = []
        normalized_sources = [source for source in sources if isinstance(source, dict)]

        language = body.get("language", request.language)
        if language not in {"en", "te", "hi"}:
            language = request.language

        return ChatResponse(answer=answer, sources=normalized_sources, language=language)

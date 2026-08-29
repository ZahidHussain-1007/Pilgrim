"""Response models exposed by the worker API."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatResponse(BaseModel):
    """Normalized answer returned to the NestJS backend."""

    answer: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    language: Literal["en", "te", "hi"]


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"

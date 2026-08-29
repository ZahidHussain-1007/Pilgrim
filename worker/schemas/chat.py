"""Chat request validation."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """A chat message received from the application backend."""

    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(min_length=1, max_length=2_000)
    temple: str | None = Field(default=None, max_length=200)
    language: Literal["en", "te", "hi"] = "en"

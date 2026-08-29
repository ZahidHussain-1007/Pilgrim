"""Environment-backed configuration for the FastAPI worker."""

from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import AnyHttpUrl, BaseModel


WORKER_DIRECTORY = Path(__file__).resolve().parents[1]
PROJECT_DIRECTORY = WORKER_DIRECTORY.parent


class Settings(BaseModel):
    """Runtime settings. Values are supplied through environment variables."""

    app_name: str = "Pilgrim FastAPI Worker"
    app_environment: str = "development"
    rag_agent_url: AnyHttpUrl
    rag_agent_chat_path: str = "/api/chat"
    rag_agent_timeout_seconds: float = 40.0

@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance for dependency injection."""

    # Process environment always wins. The files are only local-development
    # convenience and are intentionally not required in a deployed service.
    load_dotenv(WORKER_DIRECTORY / ".env")
    load_dotenv(PROJECT_DIRECTORY / ".env")
    return Settings(
        app_name=os.getenv("APP_NAME", "Pilgrim FastAPI Worker"),
        app_environment=os.getenv("APP_ENVIRONMENT", "development"),
        rag_agent_url=os.getenv("RAG_AGENT_URL"),
        rag_agent_chat_path=os.getenv("RAG_AGENT_CHAT_PATH", "/api/chat"),
        rag_agent_timeout_seconds=os.getenv("RAG_AGENT_TIMEOUT_SECONDS", "40"),
    )

"""FastAPI worker that isolates the NestJS API from the RAG agent."""

import os

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="PilgrimAI RAG Worker")
RAG_AGENT_URL = os.getenv("RAG_AGENT_URL", "http://localhost:8100")


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    temple: str | None = None
    language: str = Field(pattern="^(en|te|hi)$")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat")
async def chat(payload: ChatRequest) -> dict:
    """Forward a validated request to the RAG agent without exposing it to the browser."""
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(f"{RAG_AGENT_URL.rstrip('/')}/api/chat", json=payload.model_dump())
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as error:
        raise HTTPException(status_code=503, detail="PilgrimAI RAG agent is unavailable") from error

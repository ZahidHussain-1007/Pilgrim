import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Setup path so we can import from rag and services
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "rag"))
sys.path.insert(0, str(ROOT / "services"))

from ask_service import ask
from rag.dependencies import lifespan, get_state

app = FastAPI(title="RAG Agent", version="1.0.0", lifespan=lifespan)

class ChatRequest(BaseModel):
    query: str
    temple: str | None = None
    language: str | None = "en"
    session_id: str | None = None

class Source(BaseModel):
    temple_id: str | None = None
    entity_type: str | None = None
    section: str | None = None
    chunk_id: str | None = None
    name: str | None = None

class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    language: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    app_state = get_state()
    session_id = request.session_id or "default_session"
    
    session = await app_state.session_store.get(session_id) if app_state.session_store else {}
    session = session or {}
    
    if request.temple:
        from query_router import QueryRouter
        router = QueryRouter()
        resolved = router.resolver.resolve(request.temple)
        if resolved and not resolved.get("ambiguous"):
            session["temple_id"] = resolved["temple_id"]
            session["temple_name"] = router.resolver.display_name(resolved["temple_id"])

    try:
        result, session = await ask(request.query, app_state, session)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred processing the request.")

    if app_state.session_store:
        await app_state.session_store.set(session_id, session)

    answer = result.get("answer", "I could not generate an answer.")
    sources = result.get("sources", [])
    
    return ChatResponse(
        answer=answer,
        sources=sources,
        language=request.language or "en"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)


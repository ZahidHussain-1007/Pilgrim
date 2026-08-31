import asyncio
from typing import Optional
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from qdrant_client import QdrantClient
from groq import AsyncGroq

from rag.config import settings

class AppState:
    qdrant: Optional[QdrantClient] = None
    groq: Optional[AsyncGroq] = None
    embedder = None
    reranker = None
    bm25_store = None
    session_store = None

state = AppState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Groq Client
    if settings.groq_api_key:
        state.groq = AsyncGroq(api_key=settings.groq_api_key)

    # 2. Qdrant Client (using local disk synchronously inside to_thread, or networked)
    def init_qdrant():
        if settings.qdrant_url:
            return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
        db_path = Path(__file__).resolve().parent.parent / "qdrant_data"
        return QdrantClient(path=str(db_path))
    state.qdrant = await asyncio.to_thread(init_qdrant)

    # 3. ML Models
    def init_models():
        from sentence_transformers import SentenceTransformer
        from FlagEmbedding import FlagReranker
        embedder = SentenceTransformer("BAAI/bge-m3")
        reranker = FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=False)
        return embedder, reranker
    state.embedder, state.reranker = await asyncio.to_thread(init_models)

    # 4. BM25 Index
    def init_bm25():
        from rag.bm25_index import BM25Store
        return BM25Store()
    state.bm25_store = await asyncio.to_thread(init_bm25)

    # 5. Session Store
    if settings.redis_url:
        import redis.asyncio as redis
        from rag.session_store import RedisSessionStore
        redis_client = redis.from_url(settings.redis_url)
        state.session_store = RedisSessionStore(redis_client)
    else:
        from rag.session_store import InMemorySessionStore
        state.session_store = InMemorySessionStore()

    yield

    # Teardown
    if state.qdrant:
        state.qdrant.close()
    if state.groq:
        await state.groq.close()
    if state.session_store and hasattr(state.session_store, "_redis"):
        await state.session_store._redis.close()

def get_state() -> AppState:
    return state

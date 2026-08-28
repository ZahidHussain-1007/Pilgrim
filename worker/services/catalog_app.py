"""Catalog-only HTTP server for budget + travel agents.

Does not open Qdrant. Does not call Groq.
Safe to run while chat.py is using qdrant_data.

From project root:
    .\\.venv\\Scripts\\Activate.ps1
    uvicorn services.catalog_app:app --host 0.0.0.0 --port 8001
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.catalog import get_catalog
from services.catalog_router import router

ROOT = Path(__file__).resolve().parent.parent
get_catalog(ROOT / "data")

app = FastAPI(title="PilgrimAI Catalog", version="v1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/health")
def health():
    return {"ok": True, "service": "catalog", "temples": 23}

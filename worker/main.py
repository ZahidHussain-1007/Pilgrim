"""ASGI entry point for the Pilgrim FastAPI worker."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from worker.config.settings import get_settings
from worker.routes.chat import router as chat_router
from worker.schemas.response import HealthResponse


logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(title=settings.app_name, version="1.0.0")
app.include_router(chat_router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    """Report that the worker process is ready to accept requests."""

    return HealthResponse()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, error: RequestValidationError) -> JSONResponse:
    """Return a stable validation envelope without leaking internals."""

    return JSONResponse(status_code=422, content={"detail": error.errors()})


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, error: Exception) -> JSONResponse:
    """Log unexpected failures and avoid exposing implementation details."""

    logger.exception("Unhandled worker error", exc_info=error)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})

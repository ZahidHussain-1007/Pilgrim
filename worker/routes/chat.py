"""Chat endpoints called by the NestJS application backend."""

from fastapi import APIRouter, Depends, HTTPException, status

from worker.config.settings import Settings, get_settings
from worker.schemas.chat import ChatRequest
from worker.schemas.response import ChatResponse
from worker.services.rag_service import RagAgentError, RagAgentTimeoutError, RagService


router = APIRouter(tags=["chat"])


def get_rag_service(settings: Settings = Depends(get_settings)) -> RagService:
    return RagService(settings)


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(
    request: ChatRequest,
    rag_service: RagService = Depends(get_rag_service),
) -> ChatResponse:
    """Forward a validated chat request to the configured RAG Agent."""

    try:
        return await rag_service.answer(request)
    except RagAgentTimeoutError as error:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The RAG agent timed out.",
        ) from error
    except RagAgentError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The RAG agent returned an invalid response.",
        ) from error

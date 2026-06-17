"""
routes/chat.py
--------------
Research Assistant chatbot endpoint.

Endpoint:
    POST /chat/query  → answer a natural-language research question

Access:
    Requires any authenticated user (admin + analyst).
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatError, answer_research_query

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "/query",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask the Research Assistant a multi-company question",
)
def chat_query(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    try:
        return answer_research_query(payload.query, max_tickers=payload.max_tickers)
    except ChatError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


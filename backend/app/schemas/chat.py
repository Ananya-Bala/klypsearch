"""
schemas/chat.py
---------------
Pydantic v2 schemas for the Research Assistant chatbot endpoint.

ChatRequest  → POST /chat/query  (what the user sends)
ChatResponse → the structured answer returned

The response includes:
- answer: the main AI-generated text
- tickers_analyzed: which companies were detected and fetched
- document_sources: which filing chunks were used for context
- sentiment_summary: quick per-ticker sentiment overview
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated


class ChatRequest(BaseModel):
    query: Annotated[str, Field(
        min_length=3,
        max_length=2000,
        description="Natural language research question, e.g. 'Compare NVDA and AMD risk-adjusted returns'",
    )]
    max_tickers: Annotated[int, Field(
        default=4,
        ge=1,
        le=6,
        description="Maximum number of tickers to analyze (more = slower, costlier)",
    )] = 4


class DocumentSource(BaseModel):
    """A single document chunk used as context."""
    company: str
    source: str
    score: float
    text_preview: str   # first 200 chars of the chunk


class TickerSentiment(BaseModel):
    """Quick per-ticker sentiment summary included in the response."""
    ticker: str
    company_name: str | None
    current_price: float | None
    currency: str | None = None  # e.g. "USD", "INR"
    sentiment: str          # "bullish" | "bearish" | "neutral"
    sentiment_score: float
    recommendation: str | None  # from analyst consensus if available


class ChatResponse(BaseModel):
    query: str
    answer: str                          # the full AI-generated research answer
    tickers_analyzed: list[str]          # e.g. ["NVDA", "AMD"]
    ticker_details: list[TickerSentiment]
    document_sources: list[DocumentSource]
    generated_at: datetime
    prompt_tokens: int = 0
    completion_tokens: int = 0

    model_config = ConfigDict(from_attributes=True)

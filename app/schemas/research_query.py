"""
schemas/research_query.py
--------------------------
Pydantic v2 schemas for Research Query endpoints.

QuerySubmit    → POST /research/query  (what the analyst sends)
QueryPublic    → response shape for all research endpoints

Note on `mock_response`:
    Exposed in QueryPublic so clients can display it.
    In Phase 3 replace this field (or add alongside it) with structured
    AI output (summary, sources, confidence score, etc.).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated

from app.models.research_query import QueryStatus


# ── Request schemas ───────────────────────────────────────────────────────────

class QuerySubmit(BaseModel):
    query_text: Annotated[str, Field(min_length=3, max_length=5000)]
    workspace_id: int


# ── Response schemas ──────────────────────────────────────────────────────────

class QueryPublic(BaseModel):
    id: int
    query_text: str
    mock_response: str | None
    status: QueryStatus
    workspace_id: int
    user_id: int | None
    organization_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

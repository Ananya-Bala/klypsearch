"""
schemas/document.py
---------------------
Phase 3C: request/response schemas for the Document Knowledge Base endpoints.
"""

from pydantic import BaseModel, Field


class DocumentSearchRequest(BaseModel):
    """Body for POST /documents/search."""

    query: str = Field(
        ...,
        min_length=1,
        description="Natural-language query to run against the document corpus.",
        examples=["What did NVIDIA say about AI demand?"],
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of chunks to return.",
    )
    ticker: str | None = Field(
        default=None,
        description="Optional ticker filter to scope results to one company (e.g. NVDA).",
    )


class DocumentSearchResult(BaseModel):
    """A single retrieved chunk."""

    company: str
    source: str
    text: str
    score: float


class DocumentSearchResponse(BaseModel):
    """Response for POST /documents/search."""

    results: list[DocumentSearchResult]


class IngestStats(BaseModel):
    """Response for POST /documents/ingest."""

    documents: int
    chunks: int
    skipped: bool
    files: list[str]

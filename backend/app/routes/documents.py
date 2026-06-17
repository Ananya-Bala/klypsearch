"""
routes/documents.py
---------------------
Phase 3C: Document Knowledge Base endpoints.

Endpoints:
    POST /documents/search   → semantic search over the earnings-report corpus
    POST /documents/ingest   → (re)run ingestion manually
    GET  /documents/status   → collection health / chunk count

Access:
    Endpoints require any authenticated user, consistent with the rest of the
    platform's multi-tenant security model. Authentication logic itself is
    untouched — these routes simply reuse the existing get_current_user
    dependency.
"""

import logging

from fastapi import APIRouter, Depends, status

from app.core.config import settings
from app.middleware.dependencies import get_current_user
from app.models.user import User
from app.schemas.document import (
    DocumentSearchRequest,
    DocumentSearchResponse,
    DocumentSearchResult,
    IngestStats,
)
from app.services import document_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Document Knowledge Base (Phase 3C)"])


# ── POST /documents/search ────────────────────────────────────────────────────

@router.post(
    "/search",
    response_model=DocumentSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic search over the earnings-report knowledge base",
)
def search_documents_route(
    payload: DocumentSearchRequest,
    current_user: User = Depends(get_current_user),
) -> DocumentSearchResponse:
    """
    Embed the query with the local sentence-transformers model, search the
    ChromaDB vector store, and return the most relevant document chunks.
    """
    results = document_service.search_documents(
        query=payload.query,
        top_k=payload.top_k,
        ticker=payload.ticker,
    )
    logger.info(
        "documents.search.route user=%s query=%r returned=%d",
        current_user.id,
        payload.query[:80],
        len(results),
    )
    return DocumentSearchResponse(
        results=[DocumentSearchResult(**r.to_dict()) for r in results]
    )


# ── POST /documents/ingest ────────────────────────────────────────────────────

@router.post(
    "/ingest",
    response_model=IngestStats,
    status_code=status.HTTP_200_OK,
    summary="Manually (re)ingest documents into the vector store",
)
def ingest_documents_route(
    force: bool = False,
    current_user: User = Depends(get_current_user),
) -> IngestStats:
    """
    Ingest documents from the configured documents directory.

    By default this is a no-op when the collection is already populated.
    Pass ``?force=true`` to wipe and re-ingest the entire corpus.
    """
    stats = document_service.ingest_documents(force=force)
    return IngestStats(**stats)


# ── GET /documents/status ─────────────────────────────────────────────────────

@router.get(
    "/status",
    summary="Vector store status and chunk count",
)
def documents_status_route(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Lightweight health probe for the knowledge base."""
    try:
        collection = document_service._get_collection()
        count = collection.count()
        empty = count == 0
    except Exception as exc:  # pragma: no cover
        logger.warning("documents.status failed: %s", exc)
        return {"available": False, "chunk_count": 0, "error": str(exc)}

    return {
        "available": True,
        "chunk_count": count,
        "empty": empty,
        "collection": settings.CHROMA_COLLECTION_NAME,
        "embedding_model": settings.EMBEDDING_MODEL_NAME,
    }

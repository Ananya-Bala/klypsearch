"""
routes/research.py
-------------------
Research query endpoints for analysts (and admins).

Endpoints:
    POST /research/query            → submit a new query (returns mock response)
    GET  /research/history          → list caller's query history (optional ?workspace_id=)
    GET  /research/{query_id}       → get a single query by id

Access:
    All three endpoints require any authenticated user (admin or analyst).
    Analysts see ONLY their own queries.
    Admins wanting org-wide visibility use GET /admin/activity instead.

The `workspace_id` query-param on GET /research/history is optional:
    omit it → all history for the user
    include it → filtered to that workspace
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.middleware.dependencies import get_current_user
from app.models.user import User
from app.schemas.research_query import QueryPublic, QuerySubmit
from app.services.research_service import (
    ResearchError,
    get_query_by_id,
    get_query_history,
    submit_query,
)

router = APIRouter(prefix="/research", tags=["Research"])


# ── POST /research/query ──────────────────────────────────────────────────────

@router.post(
    "/query",
    response_model=QueryPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a research query (returns mock response in Phase 2)",
)
def submit_query_route(
    payload: QuerySubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QueryPublic:
    """
    Saves the query and returns an immediate mock response.
    Phase 3 will replace mock_response with real AI analysis.
    """
    try:
        return submit_query(
            db=db,
            payload=payload,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
        )
    except ResearchError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


# ── GET /research/history ─────────────────────────────────────────────────────

@router.get(
    "/history",
    response_model=list[QueryPublic],
    summary="Get the current user's research query history",
)
def get_history_route(
    workspace_id: int | None = Query(
        default=None,
        description="Filter history to a specific workspace.",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[QueryPublic]:
    """
    Returns query history for the calling user only.
    Optionally filtered by `?workspace_id=<id>`.
    """
    return get_query_history(
        db=db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        workspace_id=workspace_id,
    )


# ── GET /research/{query_id} ──────────────────────────────────────────────────

@router.get(
    "/{query_id}",
    response_model=QueryPublic,
    summary="Get a single research query by ID",
)
def get_query_route(
    query_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QueryPublic:
    """
    Returns the query only if it belongs to the calling user and their org.
    Returns 404 for unknown ids or cross-user/cross-org access attempts.
    """
    try:
        return get_query_by_id(
            db=db,
            query_id=query_id,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
        )
    except ResearchError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)

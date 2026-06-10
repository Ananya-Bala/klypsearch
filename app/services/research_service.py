"""
services/research_service.py
-----------------------------
Business logic for submitting and retrieving research queries.

Phase 2 mock behaviour:
    `submit_query` saves the query and immediately populates `mock_response`
    with a templated placeholder string.  When Phase 3 adds AI processing,
    the flow becomes:
        1. Save query with status=PENDING, mock_response=None
        2. Enqueue to Celery / background task worker
        3. Worker updates status=COMPLETE + stores real AI response

Workspace validation:
    Before saving a query we verify the workspace exists AND belongs to
    the user's organization.  This prevents an analyst from submitting
    queries against a workspace they grabbed the id of from another org.
"""

from sqlalchemy.orm import Session

from app.models.research_query import QueryStatus, ResearchQuery
from app.models.workspace import Workspace
from app.schemas.research_query import QuerySubmit


# ── Domain exception ──────────────────────────────────────────────────────────

class ResearchError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# ── Mock response generator ───────────────────────────────────────────────────

def _build_mock_response(query_text: str) -> str:
    """
    Returns a deterministic placeholder so the frontend has something to render.
    Replace with an actual AI call in Phase 3.
    """
    return (
        f"[MOCK RESPONSE] Your query '{query_text[:80]}{'...' if len(query_text) > 80 else ''}' "
        f"has been recorded. AI analysis will be available in Phase 3."
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _validate_workspace(
    db: Session,
    workspace_id: int,
    organization_id: int,
) -> Workspace:
    """
    Ensure the workspace exists and belongs to the caller's organization.
    Raises ResearchError(404) if not found — same 404-not-403 policy as workspaces.
    """
    ws = (
        db.query(Workspace)
        .filter(
            Workspace.id == workspace_id,
            Workspace.organization_id == organization_id,
        )
        .first()
    )
    if not ws:
        raise ResearchError(
            "Workspace not found or does not belong to your organization.",
            status_code=404,
        )
    return ws


# ── CRUD ──────────────────────────────────────────────────────────────────────

def submit_query(
    db: Session,
    payload: QuerySubmit,
    user_id: int,
    organization_id: int,
) -> ResearchQuery:
    """
    Validate workspace membership, persist the query, return mock response.
    `user_id` and `organization_id` come from the JWT — never the request body.
    """
    _validate_workspace(db, payload.workspace_id, organization_id)

    rq = ResearchQuery(
        query_text=payload.query_text,
        workspace_id=payload.workspace_id,
        user_id=user_id,
        organization_id=organization_id,
        status=QueryStatus.PENDING,
        mock_response=_build_mock_response(payload.query_text),
    )
    db.add(rq)
    db.commit()
    db.refresh(rq)
    return rq


def get_query_history(
    db: Session,
    organization_id: int,
    user_id: int,
    workspace_id: int | None = None,
) -> list[ResearchQuery]:
    """
    Return query history for the calling user within their organization.

    Optional `workspace_id` filter lets analysts scope history to one workspace.
    The `organization_id` guard ensures analysts can only see their own org's data.

    Note: analysts see ONLY their own queries (user_id filter).
    Admins see all org queries — that logic lives in admin_service.py so
    this function stays focused on the analyst use-case.
    """
    q = (
        db.query(ResearchQuery)
        .filter(
            ResearchQuery.organization_id == organization_id,
            ResearchQuery.user_id == user_id,
        )
    )
    if workspace_id is not None:
        q = q.filter(ResearchQuery.workspace_id == workspace_id)

    return q.order_by(ResearchQuery.created_at.desc()).all()


def get_query_by_id(
    db: Session,
    query_id: int,
    user_id: int,
    organization_id: int,
) -> ResearchQuery:
    """
    Fetch a single query.
    Analysts can only retrieve their own queries (user_id match).
    The org check prevents cross-org access regardless of id guessing.
    """
    rq = (
        db.query(ResearchQuery)
        .filter(
            ResearchQuery.id == query_id,
            ResearchQuery.user_id == user_id,
            ResearchQuery.organization_id == organization_id,
        )
        .first()
    )
    if not rq:
        raise ResearchError("Research query not found.", status_code=404)
    return rq

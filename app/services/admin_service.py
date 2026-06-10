"""
services/admin_service.py
--------------------------
Business logic for admin activity monitoring.

Design: use explicit JOINs instead of lazy-loading relationships.
    Lazy loading would cause N+1 queries (one extra query per row to fetch
    the user and workspace names).  A single JOIN query scales to thousands
    of rows with no additional DB round-trips.

Multi-tenancy enforcement:
    Every query filters by `organization_id` from the admin's JWT.
    An admin from Org A cannot view Org B's activity regardless of
    which user_id they pass in the URL.

Authorization note:
    These functions don't check roles — that's the route layer's job.
    Services stay role-agnostic so they can be reused in other contexts
    (e.g., a scheduled report generator) without coupling to HTTP RBAC.
"""

from sqlalchemy.orm import Session

from app.models.research_query import ResearchQuery
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.admin import ActivityRecord


# ── Domain exception ──────────────────────────────────────────────────────────

class AdminError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# ── Internal query builder ────────────────────────────────────────────────────

def _activity_query(db: Session, organization_id: int):
    """
    Base SQLAlchemy query that JOINs research_queries → workspaces → users.
    Returns a query object that callers can further filter before executing.

    Columns projected:
        query_id, query_text, query_status,
        analyst_id, analyst_name, analyst_email,
        workspace_id, workspace_name,
        submitted_at
    """
    return (
        db.query(
            ResearchQuery.id.label("query_id"),
            ResearchQuery.query_text,
            ResearchQuery.status.label("query_status"),
            ResearchQuery.created_at.label("submitted_at"),
            User.id.label("analyst_id"),
            User.name.label("analyst_name"),
            User.email.label("analyst_email"),
            Workspace.id.label("workspace_id"),
            Workspace.name.label("workspace_name"),
        )
        .join(Workspace, ResearchQuery.workspace_id == Workspace.id)
        # outerjoin: preserve queries whose user was deleted (user_id nullable)
        .outerjoin(User, ResearchQuery.user_id == User.id)
        .filter(ResearchQuery.organization_id == organization_id)
        .order_by(ResearchQuery.created_at.desc())
    )


def _row_to_record(row) -> ActivityRecord:
    """Convert a SQLAlchemy named-tuple row to the ActivityRecord response model."""
    return ActivityRecord(
        query_id=row.query_id,
        query_text=row.query_text,
        query_status=row.query_status,
        analyst_id=row.analyst_id,
        analyst_name=row.analyst_name or "Deleted User",
        analyst_email=row.analyst_email or "—",
        workspace_id=row.workspace_id,
        workspace_name=row.workspace_name,
        submitted_at=row.submitted_at,
    )


# ── Public service functions ──────────────────────────────────────────────────

def get_org_activity(
    db: Session,
    organization_id: int,
    limit: int = 100,
) -> list[ActivityRecord]:
    """
    Return all recent research activity across the organization.
    `limit` caps the result set — add cursor-based pagination in Phase 3.
    """
    rows = _activity_query(db, organization_id).limit(limit).all()
    return [_row_to_record(r) for r in rows]


def get_user_activity(
    db: Session,
    target_user_id: int,
    organization_id: int,
) -> list[ActivityRecord]:
    """
    Return activity for a specific analyst within the admin's organization.

    `organization_id` guard is critical:
        Without it, an admin from Org A could query any user in the system
        by passing an arbitrary user_id in the URL.
    """
    # First verify the target user actually belongs to the admin's org
    target_user = (
        db.query(User)
        .filter(User.id == target_user_id, User.organization_id == organization_id)
        .first()
    )
    if not target_user:
        raise AdminError(
            "User not found in your organization.",
            status_code=404,
        )

    rows = (
        _activity_query(db, organization_id)
        .filter(ResearchQuery.user_id == target_user_id)
        .all()
    )
    return [_row_to_record(r) for r in rows]

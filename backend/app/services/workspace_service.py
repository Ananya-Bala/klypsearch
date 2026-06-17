"""
services/workspace_service.py
------------------------------
Business logic for workspace CRUD.
No FastAPI / HTTP concerns here — pure Python + SQLAlchemy.

All public functions accept `organization_id` derived from the caller's
JWT (passed in by the route layer).  This is the multi-tenancy enforcement
point: no route ever passes a client-supplied org id directly.

Domain exception:
    WorkspaceError mirrors AuthError from Phase 1 — carries a message and
    an HTTP status hint that routes translate into HTTPException.
"""

from sqlalchemy.orm import Session

from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate


# ── Domain exception ──────────────────────────────────────────────────────────

class WorkspaceError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_workspace_or_raise(
    db: Session,
    workspace_id: int,
    organization_id: int,
) -> Workspace:
    """
    Fetch a workspace by id AND organization_id.

    The dual-filter is the multi-tenancy guard: even if a user somehow
    knows a workspace id that belongs to another org, this query returns
    nothing — they get a 404, not a 403 (which would confirm existence).
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
        raise WorkspaceError("Workspace not found.", status_code=404)
    return ws


# ── CRUD operations ───────────────────────────────────────────────────────────

def create_workspace(
    db: Session,
    payload: WorkspaceCreate,
    organization_id: int,
    created_by_id: int,
) -> Workspace:
    """
    Create a new workspace scoped to the given organization.
    `created_by_id` is the admin's user id from the JWT — never from the request body.
    """
    ws = Workspace(
        name=payload.name,
        description=payload.description,
        organization_id=organization_id,
        created_by_id=created_by_id,
    )
    db.add(ws)
    db.commit()
    db.refresh(ws)
    return ws


def list_workspaces(db: Session, organization_id: int) -> list[Workspace]:
    """
    Return all workspaces for the given organization, newest first.
    Both admins and analysts call this — RBAC is enforced at the route level.
    """
    return (
        db.query(Workspace)
        .filter(Workspace.organization_id == organization_id)
        .order_by(Workspace.created_at.desc())
        .all()
    )


def get_workspace(
    db: Session,
    workspace_id: int,
    organization_id: int,
) -> Workspace:
    """Return a single workspace; raises 404 if not found or not in org."""
    return _get_workspace_or_raise(db, workspace_id, organization_id)


def update_workspace(
    db: Session,
    workspace_id: int,
    organization_id: int,
    payload: WorkspaceUpdate,
) -> Workspace:
    """
    Partial update — only fields present in the request body are modified.
    `model_fields_set` is the Pydantic v2 way to detect which fields the
    client actually sent (vs. fields that just have defaults).
    """
    ws = _get_workspace_or_raise(db, workspace_id, organization_id)

    # Update only explicitly-provided fields
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ws, field, value)

    db.commit()
    db.refresh(ws)
    return ws


def delete_workspace(
    db: Session,
    workspace_id: int,
    organization_id: int,
) -> None:
    """
    Hard-delete the workspace and cascade to its research queries.
    Cascade is defined at the model level (cascade="all, delete-orphan").
    """
    ws = _get_workspace_or_raise(db, workspace_id, organization_id)
    db.delete(ws)
    db.commit()

"""
routes/workspaces.py
---------------------
Workspace CRUD endpoints.

RBAC summary:
    POST   /workspaces          → admin only
    GET    /workspaces          → any authenticated user (admin + analyst)
    GET    /workspaces/{id}     → any authenticated user
    PUT    /workspaces/{id}     → admin only
    DELETE /workspaces/{id}     → admin only

Multi-tenancy:
    organization_id is ALWAYS sourced from `current_user.organization_id`
    (i.e., the verified JWT).  It is never taken from the URL or request body.

Routes are intentionally thin — no business logic here.
All validation and DB work is delegated to workspace_service.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.middleware.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.workspace import WorkspaceCreate, WorkspacePublic, WorkspaceUpdate
from app.services.workspace_service import (
    WorkspaceError,
    create_workspace,
    delete_workspace,
    get_workspace,
    list_workspaces,
    update_workspace,
)

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


# ── POST /workspaces ──────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=WorkspacePublic,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] Create a new workspace",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
def create_workspace_route(
    payload: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkspacePublic:
    """
    Admin-only. Creates a workspace inside the admin's organization.
    `organization_id` and `created_by_id` are taken from the JWT —
    the client cannot set these directly.
    """
    ws = create_workspace(
        db=db,
        payload=payload,
        organization_id=current_user.organization_id,
        created_by_id=current_user.id,
    )
    return ws


# ── GET /workspaces ───────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=list[WorkspacePublic],
    summary="List all workspaces in the current organization",
)
def list_workspaces_route(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[WorkspacePublic]:
    """Available to all authenticated users (admin + analyst)."""
    return list_workspaces(db, current_user.organization_id)


# ── GET /workspaces/{id} ──────────────────────────────────────────────────────

@router.get(
    "/{workspace_id}",
    response_model=WorkspacePublic,
    summary="Get a single workspace by ID",
)
def get_workspace_route(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkspacePublic:
    """
    Returns workspace if it belongs to the current user's organization.
    Returns 404 (not 403) for cross-org ids — avoids confirming existence.
    """
    try:
        return get_workspace(db, workspace_id, current_user.organization_id)
    except WorkspaceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


# ── PUT /workspaces/{id} ──────────────────────────────────────────────────────

@router.put(
    "/{workspace_id}",
    response_model=WorkspacePublic,
    summary="[Admin] Update a workspace (partial update supported)",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
def update_workspace_route(
    workspace_id: int,
    payload: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkspacePublic:
    """
    Admin-only partial update.
    Only fields included in the request body are changed.
    Omitting a field keeps its current value.
    """
    try:
        return update_workspace(db, workspace_id, current_user.organization_id, payload)
    except WorkspaceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


# ── DELETE /workspaces/{id} ───────────────────────────────────────────────────

@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] Delete a workspace and all its research queries",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
def delete_workspace_route(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Admin-only hard delete. Cascades to ResearchQuery rows.
    Returns 204 No Content on success (nothing to return after deletion).
    """
    try:
        delete_workspace(db, workspace_id, current_user.organization_id)
    except WorkspaceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)

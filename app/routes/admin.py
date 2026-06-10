"""
routes/admin.py
----------------
Admin-only monitoring endpoints.

All routes use `dependencies=[Depends(require_role(UserRole.ADMIN))]`
at the router level — every endpoint in this file is admin-gated without
needing to repeat it per route.

Endpoints:
    GET /admin/activity                      → all org query activity
    GET /admin/users/{user_id}/activity      → one analyst's activity

Security properties:
    - Analysts get 403 Forbidden on any /admin/* route
    - Admins can only see their own org's data (organization_id from JWT)
    - Passing a user_id from another org returns 404 (not 403)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.middleware.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.admin import ActivityRecord
from app.services.admin_service import AdminError, get_org_activity, get_user_activity

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    # ── Router-level RBAC ────────────────────────────────────────────────────
    # Applied to EVERY endpoint in this router. No per-route repetition needed.
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)


# ── GET /admin/activity ───────────────────────────────────────────────────────

@router.get(
    "/activity",
    response_model=list[ActivityRecord],
    summary="[Admin] View all research activity in the organization",
)
def get_activity_route(
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
        description="Maximum number of activity records to return.",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ActivityRecord]:
    """
    Returns all research queries submitted within the admin's organization,
    newest first.  Includes analyst name, workspace, and timestamp.
    `limit` defaults to 100; max 500 per request.
    """
    return get_org_activity(
        db=db,
        organization_id=current_user.organization_id,
        limit=limit,
    )


# ── GET /admin/users/{user_id}/activity ──────────────────────────────────────

@router.get(
    "/users/{user_id}/activity",
    response_model=list[ActivityRecord],
    summary="[Admin] View activity for a specific analyst in the organization",
)
def get_user_activity_route(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ActivityRecord]:
    """
    Returns query history for the specified user.
    The user must belong to the admin's organization — cross-org lookups
    return 404 (same as "not found") to avoid confirming user existence.
    """
    try:
        return get_user_activity(
            db=db,
            target_user_id=user_id,
            organization_id=current_user.organization_id,
        )
    except AdminError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)

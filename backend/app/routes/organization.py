"""
routes/organization.py
-----------------------
Organization-scoped endpoints.

Multi-tenancy enforcement:
    Every query uses `current_user.organization_id` from the verified JWT.
    A user cannot access another org's data by manipulating a URL param —
    there ARE no org-id URL params here; the JWT is the only source of truth.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.middleware.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.organization import OrganizationDetail
from app.schemas.user import UserPublic
from app.services.organization_service import (
    get_organization_by_id,
    get_users_in_organization,
)

router = APIRouter(prefix="/organization", tags=["Organization"])


@router.get(
    "/me",
    response_model=OrganizationDetail,
    summary="Get the current user's organization",
)
def get_my_organization(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationDetail:
    """
    Returns full organization details (including invite_code) for the
    authenticated user's organization.

    Note: invite_code is included so admins can share it. If you want to
    restrict it to admins only, swap `get_current_user` for `require_role(UserRole.ADMIN)`.
    """
    org = get_organization_by_id(db, current_user.organization_id)
    if not org:
        # This should never happen if the FK constraint is intact,
        # but we handle it defensively.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )
    return org


@router.get(
    "/users",
    response_model=list[UserPublic],
    summary="[Admin] List all users in the current organization",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
def list_organization_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[User]:
    """
    Admin-only endpoint.
    Returns all users within the admin's organization.
    The query is scoped to `current_user.organization_id` from the JWT —
    not from the URL — so there is no way to enumerate another org's users.
    """
    return get_users_in_organization(db, current_user.organization_id)
"""
services/organization_service.py
---------------------------------
Business logic for organization queries.
All DB access is scoped by organization_id from the JWT — never trust
a client-supplied org id for data access decisions.
"""

from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.user import User


def get_organization_by_id(db: Session, organization_id: int) -> Organization | None:
    return db.query(Organization).filter(Organization.id == organization_id).first()


def get_users_in_organization(db: Session, organization_id: int) -> list[User]:
    """
    Return all users belonging to the given organization.
    The organization_id comes from the verified JWT, not a URL param —
    a user cannot query another org's roster by manipulating the URL.
    """
    return (
        db.query(User)
        .filter(User.organization_id == organization_id)
        .order_by(User.created_at)
        .all()
    )

"""
schemas/organization.py
------------------------
Pydantic v2 schemas for Organization API responses.

We intentionally do NOT expose invite_code in OrganizationPublic —
that field is admin-only and returned only in OrganizationDetail.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrganizationPublic(BaseModel):
    """Minimal org info safe to embed in user responses."""
    id: int
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganizationDetail(OrganizationPublic):
    """Full org info returned to admins (includes invite code)."""
    invite_code: str
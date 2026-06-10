"""
schemas/user.py
---------------
Pydantic v2 schemas for auth and user API contracts.

Key principle: password_hash NEVER appears in any response schema.
The `UserPublic` schema is what every protected endpoint returns.
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.user import UserRole


# ── Shared base ───────────────────────────────────────────────────────────────

class UserPublic(BaseModel):
    """Safe user representation — no secrets, returned by /auth/me and org endpoints."""
    id: int
    name: str
    email: EmailStr
    role: UserRole
    organization_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Auth: signup ──────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    """
    Handles both signup modes in one schema.
    Validation rule: exactly one of `organization_name` or `invite_code` must be present.
    This is enforced by a model_validator so the error is clear and early.
    """
    name: Annotated[str, Field(min_length=1, max_length=120)]
    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=128)]

    # Create-org mode
    organization_name: Annotated[str | None, Field(default=None, max_length=120)]

    # Join-org mode
    invite_code: Annotated[str | None, Field(default=None, max_length=16)]

    @model_validator(mode="after")
    def _exactly_one_mode(self) -> "SignupRequest":
        has_org_name = bool(self.organization_name)
        has_invite = bool(self.invite_code)

        if has_org_name and has_invite:
            raise ValueError(
                "Provide either 'organization_name' (create) or 'invite_code' (join), not both."
            )
        if not has_org_name and not has_invite:
            raise ValueError(
                "Provide either 'organization_name' (create) or 'invite_code' (join)."
            )
        return self


# ── Auth: login ───────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: Annotated[str, Field(min_length=1)]


class TokenResponse(BaseModel):
    """Standard OAuth2-compatible token response."""
    access_token: str
    token_type: str = "bearer"
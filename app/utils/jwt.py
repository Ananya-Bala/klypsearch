"""
utils/jwt.py
------------
All JWT operations live here so routes and services never import
`python-jose` directly — one place to change algorithms or claims shape.

Token payload (claims):
    sub         : str(user_id)        — standard JWT subject
    org_id      : int                 — multi-tenant isolation key
    role        : str                 — RBAC role
    exp         : datetime            — expiry (added by python-jose)
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings


# ── Token creation ────────────────────────────────────────────────────────────

def create_access_token(
    user_id: int,
    organization_id: int,
    role: str,
) -> str:
    """
    Build and sign a JWT access token.
    The payload deliberately contains only what downstream services need
    (user_id, org_id, role) so we don't over-share PII in tokens.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload: dict[str, Any] = {
        "sub": str(user_id),        # standard claim; kept as str for RFC compliance
        "org_id": organization_id,  # custom claim for multi-tenancy
        "role": role,               # custom claim for RBAC
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


# ── Token verification ────────────────────────────────────────────────────────

class TokenPayload:
    """Typed wrapper around decoded JWT claims."""

    def __init__(self, raw: dict[str, Any]) -> None:
        self.user_id: int = int(raw["sub"])
        self.organization_id: int = int(raw["org_id"])
        self.role: str = raw["role"]


def decode_access_token(token: str) -> TokenPayload:
    """
    Decode and validate a JWT.
    Raises JWTError (caught by the auth dependency) on any failure:
    expired, bad signature, missing claims, etc.
    """
    raw = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    return TokenPayload(raw)

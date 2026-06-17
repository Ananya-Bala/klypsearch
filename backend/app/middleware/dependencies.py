"""
middleware/dependencies.py
---------------------------
FastAPI dependency injection for authentication and RBAC.

Architecture:
    get_current_user        → verifies the JWT, loads the User from DB
    require_admin()         → factory that returns a dependency enforcing admin role

Usage in routes:
    @router.get("/admin-only")
    def admin_route(user: User = Depends(require_admin())):
        ...

    @router.get("/any-authenticated")
    def protected_route(user: User = Depends(get_current_user)):
        ...

Why a factory for require_admin?
    Returning a Depends-compatible callable lets FastAPI's OpenAPI generator
    annotate security schemes correctly, and keeps the dependency chain clean.
    Extendable: `require_role(UserRole.ANALYST)` follows the same pattern.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User, UserRole
from app.utils.jwt import decode_access_token


# HTTPBearer extracts the token from `Authorization: Bearer <token>` headers.
# auto_error=True means FastAPI returns 403 automatically if the header is absent.
_bearer_scheme = HTTPBearer(auto_error=True)


# ── Core auth dependency ──────────────────────────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decode the JWT and load the corresponding User from the database.

    Two-step verification:
    1. JWT signature + expiry (cryptographic)
    2. User still exists in DB (prevents use of tokens after account deletion)

    Raises 401 on any auth failure — never 403, because 403 implies
    the identity is known but lacks permission.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == payload.user_id).first()
    if user is None:
        raise credentials_exception

    # Sanity-check: org in token must match org in DB.
    # Detects token reuse after an org transfer (future feature).
    if user.organization_id != payload.organization_id:
        raise credentials_exception

    return user


# ── RBAC dependency factory ───────────────────────────────────────────────────

def require_role(required_role: UserRole):
    """
    Generic role-enforcement factory.

    Example:
        require_admin  = require_role(UserRole.ADMIN)
        require_analyst = require_role(UserRole.ANALYST)
    """
    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role.value}.",
            )
        return current_user
    return _dependency


# ── Convenience aliases ───────────────────────────────────────────────────────

def require_admin() -> User:
    """
    Shorthand dependency for admin-only routes.
    Usage: `user: User = Depends(require_admin())`
    """
    return Depends(require_role(UserRole.ADMIN))


# For routes accessible to all authenticated users regardless of role
# just use `Depends(get_current_user)` directly.

"""
services/auth_service.py
-------------------------
Pure business logic for authentication.
No FastAPI imports here — this layer is HTTP-framework agnostic,
making it trivial to unit-test without spinning up a server.

Responsibilities:
- Password hashing / verification
- User creation (create-org and join-org modes)
- Login credential validation
"""

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.user import User, UserRole
from app.schemas.user import SignupRequest, LoginRequest
from app.utils.invite import generate_invite_code
from app.utils.jwt import create_access_token


# ── Password hashing ──────────────────────────────────────────────────────────

# bcrypt is the gold standard: slow by design, salted automatically.
# deprecated="auto" will auto-upgrade weaker hashes on next login.
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


# ── Signup ────────────────────────────────────────────────────────────────────

class AuthError(Exception):
    """
    Domain exception for auth failures.
    Routes translate this into appropriate HTTP responses.
    Keeping HTTP status codes OUT of the service layer preserves
    separation of concerns.
    """
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def signup(db: Session, payload: SignupRequest) -> tuple[User, str]:
    """
    Handle both signup modes and return (user, access_token).

    Mode A — create org:  payload.organization_name is set
    Mode B — join org:    payload.invite_code is set
    (Pydantic schema guarantees exactly one is set.)
    """
    # ── Global email uniqueness check ─────────────────────────────────────────
    if db.query(User).filter(User.email == payload.email).first():
        raise AuthError("Email already registered.", status_code=409)

    if payload.organization_name:
        return _create_org_and_admin(db, payload)
    else:
        return _join_org_as_analyst(db, payload)


def _create_org_and_admin(db: Session, payload: SignupRequest) -> tuple[User, str]:
    """
    Create a new organization, then create the first user as admin.
    The invite_code is generated here and stored on the org.
    """
    org = Organization(
        name=payload.organization_name,
        invite_code=generate_invite_code(),
    )
    db.add(org)
    db.flush()  # flush to get org.id before creating the user

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=UserRole.ADMIN,
        organization_id=org.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(
        user_id=user.id,
        organization_id=user.organization_id,
        role=user.role.value,
    )
    return user, token


def _join_org_as_analyst(db: Session, payload: SignupRequest) -> tuple[User, str]:
    """
    Validate the invite code, then create an analyst in that organization.
    """
    org = (
        db.query(Organization)
        .filter(Organization.invite_code == payload.invite_code)
        .first()
    )
    if not org:
        raise AuthError("Invalid invite code.", status_code=404)

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=UserRole.ANALYST,
        organization_id=org.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(
        user_id=user.id,
        organization_id=user.organization_id,
        role=user.role.value,
    )
    return user, token


# ── Login ─────────────────────────────────────────────────────────────────────

def login(db: Session, payload: LoginRequest) -> str:
    """
    Validate credentials and return an access token.

    Security note: we return the same vague error for "user not found"
    and "wrong password" to prevent user enumeration attacks.
    """
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise AuthError("Invalid email or password.", status_code=401)

    return create_access_token(
        user_id=user.id,
        organization_id=user.organization_id,
        role=user.role.value,
    )

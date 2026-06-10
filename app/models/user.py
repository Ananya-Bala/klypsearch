"""
models/user.py
--------------
Users are always scoped to an Organization (multi-tenant).

Design choices:
- UserRole is a Python Enum + PostgreSQL native enum type for DB-level
  constraint enforcement — invalid roles cannot be stored even via raw SQL.
- organization_id has a ForeignKey with ondelete="CASCADE" so orphaned
  users are impossible if an org is deleted at the DB level.
- email is UNIQUE globally — one account per email across all orgs.
  (For Phase 2 you might relax this to unique-per-org.)
- password_hash is never exposed via Pydantic schemas (see schemas/user.py).
"""

import enum
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class UserRole(str, enum.Enum):
    """
    Inheriting from str means role values serialise to plain strings in JSON,
    which avoids extra .value calls throughout the codebase.
    """
    ADMIN = "admin"
    ANALYST = "analyst"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(120), nullable=False)

    email: Mapped[str] = mapped_column(
        String(254),        # RFC 5321 max email length
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # PostgreSQL native enum; adding new roles requires an Alembic migration
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="userrole"),
        nullable=False,
        default=UserRole.ANALYST,
    )

    # ── Multi-tenancy foreign key ──────────────────────────────────────────────
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,     # queries like "all users in org X" hit this index
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization",
        back_populates="users",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role}>"

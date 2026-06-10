"""
models/organization.py
-----------------------
The Organization is the top-level tenant boundary.
Every resource in the system is scoped to an organization.

Design choices:
- invite_code is UNIQUE at the DB level — no application-level race condition.
- cascade="all, delete-orphan" on users means deleting an org cleans up its users.
  In production you'd soft-delete; for Phase 1 a hard cascade is fine.
"""

from datetime import datetime, timezone

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(120), nullable=False)

    # Unique code users share to join this org
    invite_code: Mapped[str] = mapped_column(
        String(16), unique=True, nullable=False, index=True
    )

    # server_default offloads timestamping to PostgreSQL — survives bulk inserts
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    users: Mapped[list["User"]] = relationship(  # noqa: F821
        "User",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="select",          # explicit loading; avoid N+1 in list endpoints
    )

    def __repr__(self) -> str:
        return f"<Organization id={self.id} name={self.name!r}>"
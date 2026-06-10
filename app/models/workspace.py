"""
models/workspace.py
--------------------
A Workspace is a named container inside an Organization.
Think of it as a project folder — analysts run research queries inside
a workspace, and admins organise work by grouping queries into workspaces.

Multi-tenancy: organization_id is set at creation and NEVER changes.
All queries against Workspace rows must filter by organization_id from
the JWT — never trust a client-supplied org id.

Soft-delete consideration:
    For Phase 2 we use hard deletes (simpler). When you add audit trails
    in Phase 3, add `is_deleted: bool` + `deleted_at: datetime | None`
    and replace DELETE with a soft-delete service method.

Relationship map:
    Organization  1──* Workspace  1──* ResearchQuery
"""

from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(120), nullable=False)

    # Optional freetext description of what the workspace is for
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Multi-tenancy FK ──────────────────────────────────────────────────────
    # Index here because the most common query is "all workspaces in org X"
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Track who created it — useful for audit trails and display in the UI
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,   # nullable so workspace survives if creator is deleted
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),    # auto-updated by SQLAlchemy on every UPDATE
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization",
        lazy="select",
    )

    created_by: Mapped["User"] = relationship(  # noqa: F821
        "User",
        foreign_keys=[created_by_id],
        lazy="select",
    )

    # Back-reference used by ResearchQuery; cascade cleans up queries on workspace delete
    research_queries: Mapped[list["ResearchQuery"]] = relationship(  # noqa: F821
        "ResearchQuery",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Workspace id={self.id} name={self.name!r} org={self.organization_id}>"

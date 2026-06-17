"""
models/research_query.py
-------------------------
Records every research query submitted by an analyst (or admin).

Phase 2 scope:
    Queries are persisted with their text, workspace, and submitting user.
    The `mock_response` field stores a placeholder string returned by the
    API — in Phase 3 this will be replaced with real AI output + vector
    search results.

Status enum:
    PENDING  → saved but not yet processed (default)
    COMPLETE → AI processing done (Phase 3)
    FAILED   → processing error (Phase 3)

Keeping status as a DB-level enum now means the Phase 3 AI worker can
update it without a schema migration.

Index strategy:
    - (workspace_id, created_at)  → "all queries in workspace, newest first"
    - (user_id, created_at)       → "all queries by user, for activity feed"
    - organization_id alone       → "all queries in org" (admin activity view)
"""

import enum
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, DateTime, Enum as SAEnum, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class QueryStatus(str, enum.Enum):
    PENDING  = "pending"
    COMPLETE = "complete"
    FAILED   = "failed"


class ResearchQuery(Base):
    __tablename__ = "research_queries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # The analyst's raw question
    query_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Placeholder response — swapped for real AI output in Phase 3
    mock_response: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[QueryStatus] = mapped_column(
        SAEnum(QueryStatus, name="querystatus"),
        nullable=False,
        default=QueryStatus.PENDING,
    )

    # ── FK references ─────────────────────────────────────────────────────────
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,   # preserve query history even if user is deleted
        index=True,
    )

    # Denormalized for fast org-scoped queries without joining through workspace
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    workspace: Mapped["Workspace"] = relationship(  # noqa: F821
        "Workspace",
        back_populates="research_queries",
        lazy="select",
    )

    user: Mapped["User"] = relationship(  # noqa: F821
        "User",
        foreign_keys=[user_id],
        lazy="select",
    )

    organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization",
        lazy="select",
    )

    # ── Composite indexes ─────────────────────────────────────────────────────
    __table_args__ = (
        # Fast "history for workspace" queries
        Index("ix_research_queries_workspace_created", "workspace_id", "created_at"),
        # Fast "activity by user" queries (admin monitoring)
        Index("ix_research_queries_user_created", "user_id", "created_at"),
        # Fast "all org activity" queries
        Index("ix_research_queries_org_created", "organization_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<ResearchQuery id={self.id} user={self.user_id} "
            f"workspace={self.workspace_id} status={self.status}>"
        )

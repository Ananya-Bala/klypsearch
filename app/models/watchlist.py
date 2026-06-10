"""
models/watchlist.py
--------------------
A WatchlistItem represents a single ticker/company a user wants to track.

Design decisions:
- Scoped to BOTH user_id and organization_id.
  User-scoped: each analyst's watchlist is personal.
  Org-scoped: org admins can see all watchlist items in their org (Phase 3 feature).
  Denormalizing organization_id avoids an extra join through users on every query.

- Unique constraint on (user_id, ticker): a user cannot add the same ticker twice.
  This is enforced at the DB level — no application-level duplicate check needed.

- ticker is stored UPPERCASE (enforced in service layer) for consistent lookups.
  "aapl" and "AAPL" are the same security; uppercase is the financial industry standard.
"""

from datetime import datetime

from sqlalchemy import ForeignKey, String, DateTime, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    ticker: Mapped[str] = mapped_column(
        String(20),     # longest tickers are ~10 chars; 20 gives headroom
        nullable=False,
    )

    company_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # ── Multi-tenancy + user scope ─────────────────────────────────────────────
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", lazy="select")  # noqa: F821
    organization: Mapped["Organization"] = relationship("Organization", lazy="select")  # noqa: F821

    # ── Constraints ───────────────────────────────────────────────────────────
    __table_args__ = (
        # Prevent a user from adding the same ticker twice
        UniqueConstraint("user_id", "ticker", name="uq_watchlist_user_ticker"),
    )

    def __repr__(self) -> str:
        return (
            f"<WatchlistItem id={self.id} ticker={self.ticker!r} user={self.user_id}>"
        )

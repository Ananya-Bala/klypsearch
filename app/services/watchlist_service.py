"""
services/watchlist_service.py
------------------------------
Business logic for personal watchlist management.

All queries filter on BOTH user_id AND organization_id:
- user_id  → personal scope (your watchlist, not a colleague's)
- organization_id → multi-tenancy guard (even if user_id was guessed)

Duplicate ticker handling:
    The DB has a unique constraint on (user_id, ticker).
    We catch the IntegrityError and convert it to a clean domain exception
    rather than leaking a raw DB error message to the client.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.watchlist import WatchlistItem
from app.schemas.watchlist import WatchlistItemCreate


# ── Domain exception ──────────────────────────────────────────────────────────

class WatchlistError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# ── CRUD ──────────────────────────────────────────────────────────────────────

def add_to_watchlist(
    db: Session,
    payload: WatchlistItemCreate,
    user_id: int,
    organization_id: int,
) -> WatchlistItem:
    """
    Add a ticker to the user's watchlist.
    Ticker is already normalised to uppercase by the Pydantic schema validator.
    """
    item = WatchlistItem(
        ticker=payload.ticker,          # already uppercase from schema validator
        company_name=payload.company_name,
        user_id=user_id,
        organization_id=organization_id,
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise WatchlistError(
            f"Ticker '{payload.ticker}' is already in your watchlist.",
            status_code=409,
        )
    db.refresh(item)
    return item


def get_watchlist(
    db: Session,
    user_id: int,
    organization_id: int,
) -> list[WatchlistItem]:
    """Return all watchlist items for the given user, alphabetically by ticker."""
    return (
        db.query(WatchlistItem)
        .filter(
            WatchlistItem.user_id == user_id,
            WatchlistItem.organization_id == organization_id,
        )
        .order_by(WatchlistItem.ticker)
        .all()
    )


def remove_from_watchlist(
    db: Session,
    item_id: int,
    user_id: int,
    organization_id: int,
) -> None:
    """
    Delete a watchlist item.
    The triple filter (id + user_id + org_id) prevents a user from deleting
    another user's items even if they know the item id.
    """
    item = (
        db.query(WatchlistItem)
        .filter(
            WatchlistItem.id == item_id,
            WatchlistItem.user_id == user_id,
            WatchlistItem.organization_id == organization_id,
        )
        .first()
    )
    if not item:
        raise WatchlistError("Watchlist item not found.", status_code=404)

    db.delete(item)
    db.commit()

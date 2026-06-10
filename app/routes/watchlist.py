"""
routes/watchlist.py
--------------------
Personal watchlist endpoints.

All endpoints are available to any authenticated user (admin + analyst).
Each user can only read/delete their own items — enforced in the service layer.

Endpoints:
    POST   /watchlist           → add a ticker
    GET    /watchlist           → list my watchlist
    DELETE /watchlist/{id}      → remove a ticker
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.middleware.dependencies import get_current_user
from app.models.user import User
from app.schemas.watchlist import WatchlistItemCreate, WatchlistItemPublic
from app.services.watchlist_service import (
    WatchlistError,
    add_to_watchlist,
    get_watchlist,
    remove_from_watchlist,
)

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])


# ── POST /watchlist ───────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=WatchlistItemPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Add a ticker to the current user's watchlist",
)
def add_watchlist_item(
    payload: WatchlistItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WatchlistItemPublic:
    """
    Ticker is normalised to uppercase automatically.
    Returns 409 if the ticker is already in the user's watchlist.
    """
    try:
        return add_to_watchlist(
            db=db,
            payload=payload,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
        )
    except WatchlistError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


# ── GET /watchlist ────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=list[WatchlistItemPublic],
    summary="Get the current user's watchlist",
)
def list_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[WatchlistItemPublic]:
    """Returns all tickers in the user's watchlist, sorted alphabetically."""
    return get_watchlist(
        db=db,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
    )


# ── DELETE /watchlist/{id} ────────────────────────────────────────────────────

@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a ticker from the current user's watchlist",
)
def delete_watchlist_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Removes the item if it belongs to the calling user.
    Returns 404 if the item doesn't exist or belongs to a different user.
    """
    try:
        remove_from_watchlist(
            db=db,
            item_id=item_id,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
        )
    except WatchlistError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)

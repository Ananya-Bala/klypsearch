"""
schemas/watchlist.py
---------------------
Pydantic v2 schemas for the Watchlist API.

WatchlistItemCreate  → POST /watchlist
WatchlistItemPublic  → response for GET /watchlist and DELETE /watchlist/{id}
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── Request schemas ───────────────────────────────────────────────────────────

class WatchlistItemCreate(BaseModel):
    ticker: Annotated[str, Field(min_length=1, max_length=20)]
    company_name: Annotated[str, Field(min_length=1, max_length=200)]

    @field_validator("ticker")
    @classmethod
    def uppercase_ticker(cls, v: str) -> str:
        """
        Normalise ticker to uppercase before it reaches the service layer.
        "aapl" → "AAPL". Keeps the DB consistent without relying on callers.
        """
        return v.strip().upper()


# ── Response schemas ──────────────────────────────────────────────────────────

class WatchlistItemPublic(BaseModel):
    id: int
    ticker: str
    company_name: str
    user_id: int
    organization_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

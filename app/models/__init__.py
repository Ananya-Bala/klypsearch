"""
models/__init__.py
------------------
Importing all models here ensures Alembic's env.py (which imports Base)
sees every table when running `alembic revision --autogenerate`.

Import ORDER matters for FK resolution:
    Organization → User → Workspace → ResearchQuery
    WatchlistItem depends on User + Organization (no dependency on Workspace)
"""

# Phase 1
from app.models.organization import Organization
from app.models.user import User, UserRole

# Phase 2
from app.models.workspace import Workspace
from app.models.research_query import ResearchQuery, QueryStatus
from app.models.watchlist import WatchlistItem

__all__ = [
    # Phase 1
    "Organization",
    "User",
    "UserRole",
    # Phase 2
    "Workspace",
    "ResearchQuery",
    "QueryStatus",
    "WatchlistItem",
]

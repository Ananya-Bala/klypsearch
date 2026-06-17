"""
database/session.py
--------------------
Database session management.

Design choices:
- Use SQLAlchemy 2.0-style engine creation with connection pooling defaults
  (pool_pre_ping eliminates "stale connection" errors after DB restarts).
- SessionLocal is a factory; each request gets its own session via the
  `get_db` FastAPI dependency, which guarantees commit/rollback/close.
- DeclarativeBase lives here so all models import from one place.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from typing import Generator

from app.core.config import settings


# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite")
    else {},
    echo=settings.APP_ENV == "development",
)

# ── Session factory ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,   # Explicit commits only — predictable transaction boundaries
    autoflush=False,    # Don't flush before every query; we control this manually
    class_=Session,
)


# ── ORM Base ──────────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """All SQLAlchemy models inherit from this."""
    pass


# ── FastAPI dependency ────────────────────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """
    Request-scoped DB session.
    Use as: `db: Session = Depends(get_db)`

    The try/finally ensures the session is always closed even if the
    route handler raises an exception.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

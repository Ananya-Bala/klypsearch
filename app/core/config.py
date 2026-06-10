"""
core/config.py
--------------
Single source of truth for all runtime configuration.
Uses pydantic-settings to validate env vars at startup — fail fast,
never silently run with bad config.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    APP_TITLE: str = "Investment Research Dashboard"
    APP_VERSION: str = "1.0.0"

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str

    # ── JWT ──────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── CORS ─────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Allow comma-separated strings to become lists in .env
        env_parse_none_str="None",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance — the lru_cache means this module is loaded
    once per process, not once per request.
    """
    return Settings()


# Convenience alias used throughout the app
settings = get_settings()

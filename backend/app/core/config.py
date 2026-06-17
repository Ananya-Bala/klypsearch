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
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]

    # ── Phase 3A: AI Research Engine ─────────────────────────────────────
    # Required for AI report generation. Set in .env.
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Optional — enables news enrichment. Leave blank to skip gracefully.
    NEWS_API_KEY: str = ""
    NEWS_API_BASE_URL: str = "https://newsapi.org/v2"

    # Max age of a cached report before re-analysis is triggered (minutes).
    # Prevents duplicate OpenAI calls on rapid repeated requests.
    REPORT_CACHE_MINUTES: int = 60

    # ── Phase 3C: Document Knowledge Base (RAG) ──────────────────────────
    # Local document corpus (PDF / TXT / Markdown earnings reports) that is
    # chunked, embedded, and stored in a persistent ChromaDB vector store.
    # All settings have safe defaults so no .env change is required.

    # Directory the ingestion pipeline reads source documents from.
    DOCUMENTS_DIR: str = "data/documents"

    # Directory ChromaDB persists its on-disk index to.
    CHROMA_PERSIST_DIR: str = "data/chroma"

    # Name of the ChromaDB collection holding all document chunks.
    CHROMA_COLLECTION_NAME: str = "earnings_documents"

    # Free, local embedding model (no API key, runs on CPU).
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Chunking parameters (characters).
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150

    # How many chunks to inject into the research prompt as DOCUMENT_CONTEXT.
    DOCUMENT_CONTEXT_TOP_K: int = 3

    # Run document ingestion automatically on FastAPI startup when the
    # collection is empty. Set to False to manage ingestion manually.
    DOCUMENT_INGEST_ON_STARTUP: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_parse_none_str="None",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance — lru_cache means one load per process,
    not one per request.
    """
    return Settings()


# Convenience alias used throughout the app
settings = get_settings()

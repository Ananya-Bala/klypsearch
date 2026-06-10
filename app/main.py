"""
main.py
-------
Application entry point and factory.

Using a `create_app()` factory (rather than a module-level `app`) is a
best practice that:
- Makes it easy to create test instances with different settings
- Prevents import-time side effects
- Keeps startup logic explicit and auditable
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routes.auth import router as auth_router
from app.routes.organization import router as organization_router

from app.database.session import Base, engine
from app.models.user import User
from app.models.organization import Organization


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.APP_TITLE,
        version=settings.APP_VERSION,
        # Disable docs in production to avoid leaking your API surface
        docs_url="/docs" if settings.APP_ENV == "development" else None,
        redoc_url="/redoc" if settings.APP_ENV == "development" else None,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    # In production, restrict ALLOWED_ORIGINS to your actual frontend domain(s).
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    application.include_router(auth_router)
    application.include_router(organization_router)

    # ── Health check ──────────────────────────────────────────────────────────
    @application.get("/health", tags=["Health"], include_in_schema=False)
    def health() -> dict:
        """Simple liveness probe for load balancers and container orchestrators."""
        return {"status": "ok", "version": settings.APP_VERSION}

    Base.metadata.create_all(bind=engine)

    return application


# Module-level app instance consumed by uvicorn
app = create_app()

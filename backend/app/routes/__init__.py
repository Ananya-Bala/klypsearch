from app.routes.auth import router as auth_router
from app.routes.organization import router as organization_router
from app.routes.workspaces import router as workspaces_router
from app.routes.research import router as research_router
from app.routes.watchlist import router as watchlist_router
from app.routes.admin import router as admin_router

# Phase 3A
from app.routes.analyze import router as analyze_router

# Phase 3C
from app.routes.documents import router as documents_router

# Chat
from app.routes.chat import router as chat_router

__all__ = [
    "auth_router",
    "organization_router",
    "workspaces_router",
    "research_router",
    "watchlist_router",
    "admin_router",
    "analyze_router",
    "documents_router",
    "chat_router",
]

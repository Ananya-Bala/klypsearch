from app.services.auth_service import signup, login, AuthError
from app.services.organization_service import get_organization_by_id, get_users_in_organization
from app.services.workspace_service import (
    create_workspace,
    list_workspaces,
    get_workspace,
    update_workspace,
    delete_workspace,
    WorkspaceError,
)
from app.services.research_service import (
    submit_query,
    get_query_history,
    get_query_by_id,
    ResearchError,
)
from app.services.watchlist_service import (
    add_to_watchlist,
    get_watchlist,
    remove_from_watchlist,
    WatchlistError,
)
from app.services.admin_service import (
    get_org_activity,
    get_user_activity,
    AdminError,
)

__all__ = [
    # Phase 1
    "signup", "login", "AuthError",
    "get_organization_by_id", "get_users_in_organization",
    # Phase 2
    "create_workspace", "list_workspaces", "get_workspace",
    "update_workspace", "delete_workspace", "WorkspaceError",
    "submit_query", "get_query_history", "get_query_by_id", "ResearchError",
    "add_to_watchlist", "get_watchlist", "remove_from_watchlist", "WatchlistError",
    "get_org_activity", "get_user_activity", "AdminError",
]

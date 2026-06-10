"""
schemas/workspace.py
---------------------
Pydantic v2 schemas for the Workspace API.

Schema hierarchy:
    WorkspaceCreate     → POST /workspaces   (admin only)
    WorkspaceUpdate     → PUT  /workspaces/{id}  (admin only, all fields optional)
    WorkspacePublic     → response shape for all workspace endpoints

Design notes:
- WorkspaceUpdate uses `model_fields_set` pattern: only fields explicitly
  sent by the client are updated. Unset fields keep their DB values.
  This is safer than a full PUT that would blank out omitted fields.
- `created_by_id` is NOT in WorkspaceCreate — it is injected by the
  service layer from the JWT (current_user.id), preventing a user from
  claiming a workspace was created by someone else.
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


# ── Request schemas ───────────────────────────────────────────────────────────

class WorkspaceCreate(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=120)]
    description: Annotated[str | None, Field(default=None, max_length=1000)]


class WorkspaceUpdate(BaseModel):
    """
    All fields optional — supports partial updates (PATCH semantics over PUT).
    The service layer checks `model_fields_set` to update only what was sent.
    """
    name: Annotated[str | None, Field(default=None, min_length=1, max_length=120)]
    description: Annotated[str | None, Field(default=None, max_length=1000)]


# ── Response schemas ──────────────────────────────────────────────────────────

class WorkspacePublic(BaseModel):
    """Full workspace representation returned to both admins and analysts."""
    id: int
    name: str
    description: str | None
    organization_id: int
    created_by_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

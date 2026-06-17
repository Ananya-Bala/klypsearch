"""
schemas/admin.py
-----------------
Response schemas for the admin activity monitoring endpoints.

ActivityRecord is a "read model" — it joins data from multiple tables
(users, research_queries, workspaces) into a flat structure that's
convenient for display.  We don't store it; it's assembled by the service.

Why a flat schema instead of nested objects?
    - Simpler for frontend tables (no deep property access)
    - Avoids N+1 pitfalls (service uses a JOIN, not lazy loads)
    - Matches the spec: analyst name, query text, workspace, timestamp
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActivityRecord(BaseModel):
    """One row in the admin activity feed."""
    query_id: int
    query_text: str
    query_status: str
    analyst_id: int | None
    analyst_name: str
    analyst_email: str
    workspace_id: int
    workspace_name: str
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)

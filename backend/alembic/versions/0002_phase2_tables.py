"""Phase 2: workspaces, research_queries, watchlist_items

Revision ID: 0002_phase2_tables
Revises: 0001_phase1_tables
Create Date: 2025-01-01 00:00:00

Tables added:
    workspaces          — org-scoped project containers (admin-managed)
    research_queries    — analyst query history with mock AI response
    watchlist_items     — personal ticker watchlists (unique per user+ticker)

New enum types:
    querystatus         — pending | complete | failed
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_phase2_tables"
down_revision: Union[str, None] = "0001_phase1_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── workspaces ────────────────────────────────────────────────────────────
    op.create_table(
        "workspaces",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_by_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_workspaces_id", "workspaces", ["id"])
    op.create_index("ix_workspaces_organization_id", "workspaces", ["organization_id"])

    # ── querystatus enum + research_queries ───────────────────────────────────
    querystatus_enum = sa.Enum("pending", "complete", "failed", name="querystatus")
    querystatus_enum.create(op.get_bind())

    op.create_table(
        "research_queries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("mock_response", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "complete", "failed", name="querystatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "workspace_id",
            sa.Integer(),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_research_queries_id", "research_queries", ["id"])
    op.create_index("ix_research_queries_workspace_id", "research_queries", ["workspace_id"])
    op.create_index("ix_research_queries_user_id", "research_queries", ["user_id"])
    op.create_index("ix_research_queries_organization_id", "research_queries", ["organization_id"])
    # Composite indexes for activity-feed queries
    op.create_index(
        "ix_research_queries_workspace_created",
        "research_queries",
        ["workspace_id", "created_at"],
    )
    op.create_index(
        "ix_research_queries_user_created",
        "research_queries",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_research_queries_org_created",
        "research_queries",
        ["organization_id", "created_at"],
    )

    # ── watchlist_items ───────────────────────────────────────────────────────
    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("company_name", sa.String(200), nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        # Unique per user+ticker — prevents duplicates at the DB level
        sa.UniqueConstraint("user_id", "ticker", name="uq_watchlist_user_ticker"),
    )
    op.create_index("ix_watchlist_items_id", "watchlist_items", ["id"])
    op.create_index("ix_watchlist_items_user_id", "watchlist_items", ["user_id"])
    op.create_index("ix_watchlist_items_organization_id", "watchlist_items", ["organization_id"])


def downgrade() -> None:
    op.drop_table("watchlist_items")
    op.drop_index("ix_research_queries_org_created", table_name="research_queries")
    op.drop_index("ix_research_queries_user_created", table_name="research_queries")
    op.drop_index("ix_research_queries_workspace_created", table_name="research_queries")
    op.drop_table("research_queries")
    sa.Enum(name="querystatus").drop(op.get_bind())
    op.drop_table("workspaces")

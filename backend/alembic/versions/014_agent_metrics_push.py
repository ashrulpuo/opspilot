"""server agent key hash, last_seen; push metrics samples

Revision ID: 014
Revises: 013
Create Date: 2026-04-16

"""
from alembic import op
import sqlalchemy as sa

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("servers", sa.Column("agent_api_key_hash", sa.String(), nullable=True))
    op.add_column("servers", sa.Column("agent_last_seen_at", sa.DateTime(), nullable=True))
    op.create_index("ix_servers_agent_api_key_hash", "servers", ["agent_api_key_hash"], unique=False)

    op.create_table(
        "server_metrics_push_samples",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("server_id", sa.String(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["server_id"], ["servers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_server_metrics_push_samples_server_recorded",
        "server_metrics_push_samples",
        ["server_id", "recorded_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_server_metrics_push_samples_server_recorded", table_name="server_metrics_push_samples")
    op.drop_table("server_metrics_push_samples")
    op.drop_index("ix_servers_agent_api_key_hash", table_name="servers")
    op.drop_column("servers", "agent_last_seen_at")
    op.drop_column("servers", "agent_api_key_hash")

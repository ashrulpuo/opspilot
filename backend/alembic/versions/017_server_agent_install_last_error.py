"""servers: last Salt minion SSH install error message

Revision ID: 017
Revises: 016_add_salt_tables
Create Date: 2026-04-16
"""

from alembic import op
import sqlalchemy as sa

revision = "017"
down_revision = "016_add_salt_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "servers",
        sa.Column("agent_install_last_error", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("servers", "agent_install_last_error")

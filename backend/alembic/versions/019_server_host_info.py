"""Add host_info JSON column to servers table."""
from alembic import op
import sqlalchemy as sa

revision = "019_server_host_info"
down_revision = "018_server_agent_reported_facts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("servers", sa.Column("host_info", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("servers", "host_info")

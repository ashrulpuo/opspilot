"""Add sub_state, enabled, description to salt_service_states."""
from alembic import op
import sqlalchemy as sa

revision = "020_service_state_fields"
down_revision = "019_server_host_info"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("salt_service_states", sa.Column("sub_state", sa.String(), nullable=True))
    op.add_column("salt_service_states", sa.Column("enabled", sa.String(), nullable=True))
    op.add_column("salt_service_states", sa.Column("description", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("salt_service_states", "description")
    op.drop_column("salt_service_states", "enabled")
    op.drop_column("salt_service_states", "sub_state")

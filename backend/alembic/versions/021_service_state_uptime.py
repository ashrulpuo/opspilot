"""Add status_changed_at to salt_service_states for uptime tracking."""
from alembic import op
import sqlalchemy as sa

revision = "021_service_state_uptime"
down_revision = "020_service_state_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("salt_service_states", sa.Column("status_changed_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("salt_service_states", "status_changed_at")

"""Add memory_mb to salt_processes for RSS display."""
from alembic import op
import sqlalchemy as sa

revision = "022_process_memory_mb"
down_revision = "021_service_state_uptime"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("salt_processes", sa.Column("memory_mb", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("salt_processes", "memory_mb")

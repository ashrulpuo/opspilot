"""Add severity, title, message, resolved_at to alerts table."""
from alembic import op
import sqlalchemy as sa

revision = "023_alert_fields"
down_revision = "022_process_memory_mb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("alerts", sa.Column("severity", sa.String(), nullable=True))
    op.add_column("alerts", sa.Column("title", sa.String(), nullable=True))
    op.add_column("alerts", sa.Column("message", sa.String(), nullable=True))
    op.add_column("alerts", sa.Column("resolved_at", sa.DateTime(), nullable=True))
    # Backfill for existing rows
    op.execute("UPDATE alerts SET severity = 'warning', title = type, message = '' WHERE severity IS NULL")


def downgrade() -> None:
    op.drop_column("alerts", "resolved_at")
    op.drop_column("alerts", "message")
    op.drop_column("alerts", "title")
    op.drop_column("alerts", "severity")

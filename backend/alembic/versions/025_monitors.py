"""Add monitors, monitor_checks, monitor_incidents tables."""
from alembic import op
import sqlalchemy as sa

revision = "025_monitors"
down_revision = "024_notification_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "monitors",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("organization_id", sa.String(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("server_id", sa.String(), sa.ForeignKey("servers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False, server_default=""),
        sa.Column("type", sa.String(), nullable=False, server_default="https"),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("interval_seconds", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_status", sa.String(), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(), nullable=True),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("heartbeat_api_key", sa.String(), nullable=True),
        sa.Column("ssl_days_remaining", sa.Float(), nullable=True),
        sa.Column("avg_response_time_ms", sa.Float(), nullable=True),
        sa.Column("uptime_7d", sa.Float(), nullable=True),
        sa.Column("uptime_30d", sa.Float(), nullable=True),
        sa.Column("dns_resolve_type", sa.String(), nullable=True),
        sa.Column("dns_resolve_expected", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_monitors_org_id", "monitors", ["organization_id"])
    op.create_index("ix_monitors_heartbeat_key", "monitors", ["heartbeat_api_key"], unique=True)

    op.create_table(
        "monitor_checks",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("monitor_id", sa.String(), sa.ForeignKey("monitors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("checked_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("response_time_ms", sa.Float(), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("ssl_days_remaining", sa.Float(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_monitor_checks_monitor_id", "monitor_checks", ["monitor_id"])
    op.create_index("ix_monitor_checks_checked_at", "monitor_checks", ["checked_at"])

    op.create_table(
        "monitor_incidents",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("monitor_id", sa.String(), sa.ForeignKey("monitors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_monitor_incidents_monitor_id", "monitor_incidents", ["monitor_id"])


def downgrade() -> None:
    op.drop_table("monitor_incidents")
    op.drop_table("monitor_checks")
    op.drop_table("monitors")

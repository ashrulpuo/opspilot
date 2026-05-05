"""Add notification_smtp_configs and notification_recipients tables."""
from alembic import op
import sqlalchemy as sa

revision = "024_notification_settings"
down_revision = "023_alert_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_smtp_configs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("organization_id", sa.String(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("host", sa.String(), nullable=False, server_default=""),
        sa.Column("port", sa.Integer(), nullable=False, server_default="587"),
        sa.Column("username", sa.String(), nullable=False, server_default=""),
        sa.Column("password", sa.String(), nullable=False, server_default=""),
        sa.Column("from_address", sa.String(), nullable=False, server_default=""),
        sa.Column("use_tls", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", name="uq_smtp_config_org"),
    )

    op.create_table(
        "notification_recipients",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("organization_id", sa.String(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("severity_filter", sa.String(), nullable=False, server_default="all"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "email", name="uq_recipient_org_email"),
    )


def downgrade() -> None:
    op.drop_table("notification_recipients")
    op.drop_table("notification_smtp_configs")

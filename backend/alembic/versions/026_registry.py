"""Add infrastructure registry tables."""
from alembic import op
import sqlalchemy as sa

revision = "026_registry"
down_revision = "025_monitors"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "registry_domains",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("organization_id", sa.String(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("server_id", sa.String(), sa.ForeignKey("servers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("registrar", sa.String(), nullable=True),
        sa.Column("registered_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("nameservers", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_registry_domains_org", "registry_domains", ["organization_id"])

    op.create_table(
        "registry_ssl_certs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("organization_id", sa.String(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("domain_id", sa.String(), sa.ForeignKey("registry_domains.id", ondelete="SET NULL"), nullable=True),
        sa.Column("domain_name", sa.String(), nullable=False),
        sa.Column("common_name", sa.String(), nullable=True),
        sa.Column("issuer", sa.String(), nullable=True),
        sa.Column("issued_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("fingerprint", sa.String(), nullable=True),
        sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_registry_ssl_certs_org", "registry_ssl_certs", ["organization_id"])

    op.create_table(
        "registry_db_services",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("organization_id", sa.String(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("server_id", sa.String(), sa.ForeignKey("servers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("db_type", sa.String(), nullable=False, server_default="postgres"),
        sa.Column("host", sa.String(), nullable=False),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("database_name", sa.String(), nullable=True),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("password_enc", sa.Text(), nullable=True),
        sa.Column("environment", sa.String(), nullable=False, server_default="prod"),
        sa.Column("ssl_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_registry_db_services_org", "registry_db_services", ["organization_id"])

    op.create_table(
        "registry_credentials",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("organization_id", sa.String(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("server_id", sa.String(), sa.ForeignKey("servers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("credential_type", sa.String(), nullable=False, server_default="web_login"),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("secret_enc", sa.Text(), nullable=True),
        sa.Column("environment", sa.String(), nullable=False, server_default="prod"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_registry_credentials_org", "registry_credentials", ["organization_id"])

    op.create_table(
        "registry_audit_log",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("organization_id", sa.String(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("asset_type", sa.String(), nullable=False),
        sa.Column("asset_id", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_registry_audit_log_org", "registry_audit_log", ["organization_id"])
    op.create_index("ix_registry_audit_log_asset", "registry_audit_log", ["asset_id"])


def downgrade() -> None:
    op.drop_table("registry_audit_log")
    op.drop_table("registry_credentials")
    op.drop_table("registry_db_services")
    op.drop_table("registry_ssl_certs")
    op.drop_table("registry_domains")

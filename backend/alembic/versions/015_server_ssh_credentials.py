"""servers: SSH credentials for OpsPilot-initiated sessions (encrypted password)

Revision ID: 015
Revises: 014
Create Date: 2026-04-16

"""
from alembic import op
import sqlalchemy as sa

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("servers", sa.Column("ssh_username", sa.String(), nullable=True))
    op.add_column("servers", sa.Column("ssh_port", sa.Integer(), nullable=True))
    op.add_column("servers", sa.Column("ssh_password_encrypted", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("servers", "ssh_password_encrypted")
    op.drop_column("servers", "ssh_port")
    op.drop_column("servers", "ssh_username")

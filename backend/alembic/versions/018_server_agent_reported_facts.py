"""Add agent-reported host facts columns for Server Overview.

Revision ID: 018
Revises: 017
"""

from alembic import op
import sqlalchemy as sa


revision = "018_server_agent_reported_facts"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "servers",
        sa.Column("display_name", sa.String(), nullable=True),
    )
    op.add_column(
        "servers",
        sa.Column("agent_reported_hostname", sa.String(), nullable=True),
    )
    op.add_column(
        "servers",
        sa.Column("agent_reported_ip", sa.String(), nullable=True),
    )
    op.add_column(
        "servers",
        sa.Column("agent_os_name", sa.String(), nullable=True),
    )
    op.add_column(
        "servers",
        sa.Column("agent_os_version", sa.String(), nullable=True),
    )
    op.add_column(
        "servers",
        sa.Column("agent_architecture", sa.String(), nullable=True),
    )
    op.add_column(
        "servers",
        sa.Column("agent_cpu_cores", sa.Integer(), nullable=True),
    )
    op.add_column(
        "servers",
        sa.Column("agent_memory_mb", sa.Integer(), nullable=True),
    )
    op.add_column(
        "servers",
        sa.Column("agent_facts_synced_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_column("servers", "agent_facts_synced_at")
    op.drop_column("servers", "agent_memory_mb")
    op.drop_column("servers", "agent_cpu_cores")
    op.drop_column("servers", "agent_architecture")
    op.drop_column("servers", "agent_os_version")
    op.drop_column("servers", "agent_os_name")
    op.drop_column("servers", "agent_reported_ip")
    op.drop_column("servers", "agent_reported_hostname")
    op.drop_column("servers", "display_name")

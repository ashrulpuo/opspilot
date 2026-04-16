"""Create deployments table

Revision ID: 009_create_deployments
Revises: 008_create_logs
Create Date: 2026-04-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '009_create_deployments'
down_revision: Union[str, None] = '008_create_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create deployments table
    op.create_table(
        'deployments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('server_id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('deployment_type', sa.String(), nullable=False),  # 'manual', 'scheduled', 'git', 'docker'
        sa.Column('status', sa.String(), nullable=False),  # 'pending', 'queued', 'running', 'completed', 'failed', 'rolled_back'
        sa.Column('config', sa.JSON(), nullable=True),  # Deployment configuration
        sa.Column('schedule_type', sa.String(), nullable=True),  # 'immediate', 'scheduled'
        sa.Column('schedule_value', sa.String(), nullable=True),  # Cron expression or ISO timestamp
        sa.Column('current_version', sa.String(), nullable=True),
        sa.Column('target_version', sa.String(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['server_id'], ['servers.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_deployments_server_id', 'deployments', ['server_id'])
    op.create_index('ix_deployments_organization_id', 'deployments', ['organization_id'])
    op.create_index('ix_deployments_deployment_type', 'deployments', ['deployment_type'])
    op.create_index('ix_deployments_status', 'deployments', ['status'])
    op.create_index('ix_deployments_schedule_type', 'deployments', ['schedule_type'])


def downgrade() -> None:
    op.drop_table('deployments')

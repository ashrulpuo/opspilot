"""Create deployment executions table

Revision ID: 010_create_deployment_executions
Revises: 009_create_deployments
Create Date: 2026-04-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '010_create_deployment_executions'
down_revision: Union[str, None] = '009_create_deployments'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create deployment_executions table
    op.create_table(
        'deployment_executions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('deployment_id', sa.String(), nullable=False),
        sa.Column('server_id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),  # 'pending', 'queued', 'running', 'completed', 'failed'
        sa.Column('dry_run', sa.Boolean(), nullable=False, default=False),
        sa.Column('current_version', sa.String(), nullable=True),
        sa.Column('target_version', sa.String(), nullable=True),
        sa.Column('output', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('rollback_available', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['deployment_id'], ['deployments.id'], ),
        sa.ForeignKeyConstraint(['server_id'], ['servers.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_deployment_executions_deployment_id', 'deployment_executions', ['deployment_id'])
    op.create_index('ix_deployment_executions_server_id', 'deployment_executions', ['server_id'])
    op.create_index('ix_deployment_executions_organization_id', 'deployment_executions', ['organization_id'])
    op.create_index('ix_deployment_executions_status', 'deployment_executions', ['status'])
    op.create_index('ix_deployment_executions_started_at', 'deployment_executions', ['started_at'])


def downgrade() -> None:
    op.drop_table('deployment_executions')

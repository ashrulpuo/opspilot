"""Create backup schedules table

Revision ID: 004_create_backup_schedules
Revises: 20ada5292351
Create Date: 2026-04-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_create_backup_schedules'
down_revision: Union[str, None] = '20ada5292351'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create backup_schedules table
    op.create_table(
        'backup_schedules',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('server_id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('schedule_type', sa.String(), nullable=False),  # 'hourly', 'daily', 'weekly', 'monthly'
        sa.Column('schedule_value', sa.String(), nullable=True),  # Cron expression or time
        sa.Column('source_paths', sa.JSON(), nullable=True),  # List of paths to backup
        sa.Column('destination', sa.JSON(), nullable=True),  # Destination config
        sa.Column('retention_days', sa.Integer(), nullable=True),  # Days to keep backups
        sa.Column('compression', sa.Boolean(), nullable=True, default=True),
        sa.Column('encryption', sa.Boolean(), nullable=True, default=False),
        sa.Column('enabled', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['server_id'], ['servers.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_backup_schedules_server_id', 'backup_schedules', ['server_id'])
    op.create_index('ix_backup_schedules_organization_id', 'backup_schedules', ['organization_id'])
    op.create_index('ix_backup_schedules_enabled', 'backup_schedules', ['enabled'])


def downgrade() -> None:
    op.drop_table('backup_schedules')

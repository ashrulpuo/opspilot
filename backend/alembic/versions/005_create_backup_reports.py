"""Create backup reports/history table

Revision ID: 005_create_backup_reports
Revises: 004_create_backup_schedules
Create Date: 2026-04-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005_create_backup_reports'
down_revision: Union[str, None] = '004_create_backup_schedules'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create backup_reports table
    op.create_table(
        'backup_reports',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('backup_schedule_id', sa.String(), nullable=True),
        sa.Column('server_id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),  # 'pending', 'running', 'completed', 'failed'
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('files_transferred', sa.Integer(), nullable=True),
        sa.Column('bytes_transferred', sa.BigInteger(), nullable=True),
        sa.Column('checksum', sa.String(), nullable=True),  # MD5/SHA256 checksum
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['backup_schedule_id'], ['backup_schedules.id'], ),
        sa.ForeignKeyConstraint(['server_id'], ['servers.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_backup_reports_backup_schedule_id', 'backup_reports', ['backup_schedule_id'])
    op.create_index('ix_backup_reports_server_id', 'backup_reports', ['server_id'])
    op.create_index('ix_backup_reports_organization_id', 'backup_reports', ['organization_id'])
    op.create_index('ix_backup_reports_status', 'backup_reports', ['status'])
    op.create_index('ix_backup_reports_started_at', 'backup_reports', ['started_at'])


def downgrade() -> None:
    op.drop_table('backup_reports')

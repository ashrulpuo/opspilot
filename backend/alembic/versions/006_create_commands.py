"""Create commands table

Revision ID: 006_create_commands
Revises: 005_create_backup_reports
Create Date: 2026-04-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006_create_commands'
down_revision: Union[str, None] = '005_create_backup_reports'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create commands table
    op.create_table(
        'commands',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('server_id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('command', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),  # 'pending', 'running', 'completed', 'failed'
        sa.Column('exit_code', sa.Integer(), nullable=True),
        sa.Column('output', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['server_id'], ['servers.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_commands_server_id', 'commands', ['server_id'])
    op.create_index('ix_commands_organization_id', 'commands', ['organization_id'])
    op.create_index('ix_commands_user_id', 'commands', ['user_id'])
    op.create_index('ix_commands_status', 'commands', ['status'])
    op.create_index('ix_commands_created_at', 'commands', ['created_at'])


def downgrade() -> None:
    op.drop_table('commands')

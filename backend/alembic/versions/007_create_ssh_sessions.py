"""Create SSH sessions table

Revision ID: 007_create_ssh_sessions
Revises: 006_create_commands
Create Date: 2026-04-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '007_create_ssh_sessions'
down_revision: Union[str, None] = '006_create_commands'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Replace initial-schema ssh_sessions with the extended schema (String IDs to match servers/users/orgs).
    op.execute(sa.text('DROP TABLE IF EXISTS ssh_sessions CASCADE'))

    # Create ssh_sessions table
    op.create_table(
        'ssh_sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('server_id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),  # 'active', 'terminated', 'error'
        sa.Column('client_id', sa.String(), nullable=True),  # WebSocket client ID
        sa.Column('terminal_width', sa.Integer(), nullable=True),
        sa.Column('terminal_height', sa.Integer(), nullable=True),
        sa.Column('last_activity_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('terminated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('terminated_reason', sa.String(), nullable=True),  # 'user', 'timeout', 'error'
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['server_id'], ['servers.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_ssh_sessions_server_id', 'ssh_sessions', ['server_id'])
    op.create_index('ix_ssh_sessions_organization_id', 'ssh_sessions', ['organization_id'])
    op.create_index('ix_ssh_sessions_user_id', 'ssh_sessions', ['user_id'])
    op.create_index('ix_ssh_sessions_status', 'ssh_sessions', ['status'])
    op.create_index('ix_ssh_sessions_created_at', 'ssh_sessions', ['created_at'])


def downgrade() -> None:
    op.drop_table('ssh_sessions')

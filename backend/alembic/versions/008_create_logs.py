"""Create logs table

Revision ID: 008_create_logs
Revises: 007_create_ssh_sessions
Create Date: 2026-04-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '008_create_logs'
down_revision: Union[str, None] = '007_create_ssh_sessions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create logs table
    op.create_table(
        'logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('server_id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('log_level', sa.String(), nullable=False),  # 'error', 'warning', 'info', 'debug'
        sa.Column('log_type', sa.String(), nullable=False),  # 'system', 'application', 'security'
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('source', sa.String(), nullable=True),  # 'nginx', 'mysql', etc.
        sa.Column('extra', sa.JSON(), nullable=True),  # Additional metadata
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['server_id'], ['servers.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_logs_server_id', 'logs', ['server_id'])
    op.create_index('ix_logs_organization_id', 'logs', ['organization_id'])
    op.create_index('ix_logs_log_level', 'logs', ['log_level'])
    op.create_index('ix_logs_log_type', 'logs', ['log_type'])
    op.create_index('ix_logs_timestamp', 'logs', ['timestamp'])
    op.create_index('ix_logs_source', 'logs', ['source'])

    # Create full-text search index (PostgreSQL GIN index)
    op.execute('CREATE INDEX ix_logs_message_fts ON logs USING gin(to_tsvector(\'english\', message))')


def downgrade() -> None:
    # Drop full-text search index
    op.execute('DROP INDEX IF EXISTS ix_logs_message_fts')

    op.drop_table('logs')

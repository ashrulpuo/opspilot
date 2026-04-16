"""Create password_resets table for password reset functionality

Revision ID: 011
Revises: 010_create_deployment_executions
Create Date: 2026-04-14 09:15:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010_create_deployment_executions'
branch_labels = None
depends_on = None


def upgrade():
    """Create password_resets table."""
    op.create_table(
        'password_resets',
        sa.Column('id', sa.String(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.String(), nullable=False, index=True, comment='User ID who requested reset'),
        sa.Column('token', sa.String(), nullable=False, index=True, unique=True, comment='Password reset token'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, index=True, comment='Token expiration time'),
        sa.Column('used', sa.Boolean(), nullable=False, default=False, index=True, comment='Whether token has been used'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), comment='Token creation time'),
    )

    # Create indexes for PostgreSQL
    if op.get_context().dialect.name == 'postgresql':
        op.execute('CREATE INDEX idx_password_resets_user_id ON password_resets(user_id)')
        op.execute('CREATE INDEX idx_password_resets_token ON password_resets(token)')
        op.execute('CREATE INDEX idx_password_resets_expires_at ON password_resets(expires_at)')
        op.execute('CREATE INDEX idx_password_resets_used ON password_resets(used)')


def downgrade():
    """Drop password_resets table."""
    op.drop_table('password_resets')

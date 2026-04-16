"""configure_timescale_hypertable

Revision ID: 20ada5292351
Revises: d192139266e7
Create Date: 2026-04-13 21:43:08.744170

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20ada5292351'
down_revision: Union[str, None] = 'd192139266e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create TimescaleDB extension if not exists
    op.execute('CREATE EXTENSION IF NOT EXISTS timescaledb;')

    # Convert metrics table to hypertable
    op.execute("""
        SELECT create_hypertable('metrics', 'timestamp',
            chunk_time_interval => INTERVAL '1 day'
        );
    """)

    # Set up 90-day retention policy for metrics
    op.execute("""
        SELECT add_retention_policy('metrics', INTERVAL '90 days');
    """)


def downgrade() -> None:
    # Remove retention policy
    op.execute("""
        SELECT remove_retention_policy('metrics', if_exists => TRUE);
    """)

    # Convert hypertable back to regular table
    op.execute("""
        SELECT remove_hypertable('metrics', if_exists => TRUE);
    """)

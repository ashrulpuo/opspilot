"""Add SaltStack tables for minions, events, processes, packages, and logs (excludes service states for now).

Revision ID: 017
Revises: 015
Create Date: 2026-04-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '017_add_salt_tables_basic'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade():
    # ============================================================
    # Salt Minions Table
    # ============================================================
    op.create_table(
        'salt_minions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('minion_id', sa.String(), nullable=False, index=True),
        sa.Column('server_id', sa.String(), sa.ForeignKey('servers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('last_seen', sa.DateTime(), nullable=False, index=True),
        sa.Column('last_highstate', sa.DateTime(), nullable=True),
        sa.Column('os_info', postgresql.JSONB(), nullable=False),
        sa.Column('grains_info', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_salt_minions_minion_id', 'salt_minions', ['minion_id'])
    op.create_index('idx_salt_minions_server_id', 'salt_minions', ['server_id'])
    op.create_index('idx_salt_minions_last_seen', 'salt_minions', ['last_seen'])

    # ============================================================
    # Salt Events Table (for beacon alerts and events)
    # ============================================================
    op.create_table(
        'salt_events',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('server_id', sa.String(), sa.ForeignKey('servers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('event_tag', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False, index=True),  # 'cpu_alert', 'memory_alert', etc.
        sa.Column('event_data', postgresql.JSONB(), nullable=False),
        sa.Column('processed', sa.Boolean(), nullable=False, default=False, index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, index=True),
    )
    op.create_index('idx_salt_events_server_id', 'salt_events', ['server_id'])
    op.create_index('idx_salt_events_type', 'salt_events', ['event_type'])
    op.create_index('idx_salt_events_processed', 'salt_events', ['processed'])
    op.create_index('idx_salt_events_created_at', 'salt_events', ['created_at'])

    # ============================================================
    # Salt Processes Table (NEW)
    # ============================================================
    op.create_table(
        'salt_processes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('server_id', sa.String(), sa.ForeignKey('servers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('pid', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('command', sa.Text(), nullable=True),  # Full command line
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('cpu_percent', sa.Float(), nullable=True),  # CPU usage
        sa.Column('memory_percent', sa.Float(), nullable=True),  # Memory usage
        sa.Column('state', sa.String(), nullable=False),  # R, S, D, Z, T, W
        sa.Column('start_time', sa.DateTime(), nullable=True),  # Process start time
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_processes_server_id', 'salt_processes', ['server_id'])
    op.create_index('idx_processes_pid', 'salt_processes', ['pid'])
    op.create_index('idx_processes_state', 'salt_processes', ['state', 'created_at'])

    # ============================================================
    # Salt Packages Table (NEW)
    # ============================================================
    op.create_table(
        'salt_packages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('server_id', sa.String(), sa.ForeignKey('servers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('architecture', sa.String(), nullable=True),  # amd64, arm64, x86_64
        sa.Column('source', sa.String(), nullable=True),  # apt, yum, dnf, pacman, etc.
        sa.Column('is_update_available', sa.Boolean(), nullable=False, default=False),
        sa.Column('installed_date', sa.DateTime(), nullable=True),
        sa.Column('update_version', sa.String(), nullable=True),  # Latest available version
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_packages_server_id', 'salt_packages', ['server_id'])
    op.create_index('idx_packages_name', 'salt_packages', ['name'])
    op.create_index('idx_packages_source', 'salt_packages', ['source'])
    op.create_index('idx_packages_update', 'salt_packages', ['is_update_available'])

    # ============================================================
    # Salt Logs Table (NEW)
    # ============================================================
    op.create_table(
        'salt_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('server_id', sa.String(), sa.ForeignKey('servers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, index=True),
        sa.Column('log_level', sa.String(), nullable=False),  # INFO, WARN, ERROR, DEBUG
        sa.Column('source', sa.String(), nullable=False),  # nginx, mysql, redis, cron, etc.
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),  # Additional structured data
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_logs_server_id', 'salt_logs', ['server_id'])
    op.create_index('idx_logs_timestamp', 'salt_logs', ['timestamp'])
    op.create_index('idx_logs_level', 'salt_logs', ['log_level', 'created_at'])
    op.create_index('idx_logs_source', 'salt_logs', ['source'])

    # ============================================================
    # Update Existing Metrics Table
    # ============================================================
    # Add unit and metadata columns to existing metrics table
    op.add_column('metrics', 'unit', sa.String(), nullable=True)
    op.add_column('metrics', 'metadata', postgresql.JSONB(), nullable=True)

    # ============================================================
    # Add TimescaleDB Retention Policies
    # ============================================================
    # Note: These policies are managed by TimescaleDB, not by application
    # They're documented here for reference and can be added to
    # a cron job or initialization script

    # Retention policies (best practices):
    # - 90 days for CPU, Memory, Load metrics
    # - 365 days for Disk Usage, Service States
    # - 30 days for Network I/O, Processes
    # - 365 days for Alerts, Events
    # - Permanent for Grains (update on refresh only)

    # Example SQL for setting retention (to be run manually):
    # SELECT add_retention_policy('metrics', INTERVAL '90 days')
    # SELECT add_retention_policy('disk_metrics', INTERVAL '365 days')
    # SELECT add_retention_policy('service_states', INTERVAL '365 days')
    # SELECT add_retention_policy('salt_events', INTERVAL '365 days')
    # SELECT add_retention_policy('salt_logs', INTERVAL '7 days')
    # SELECT add_retention_policy('salt_packages', INTERVAL '365 days')


def downgrade():
    # ============================================================
    # Drop Tables in Reverse Order
    # ============================================================

    # Drop indexes first
    op.drop_index('idx_logs_source', 'salt_logs')
    op.drop_index('idx_logs_level', 'salt_logs')
    op.drop_index('idx_logs_timestamp', 'salt_logs')
    op.drop_index('idx_logs_server_id', 'salt_logs')

    op.drop_index('idx_packages_update', 'salt_packages')
    op.drop_index('idx_packages_source', 'salt_packages')
    op.drop_index('idx_packages_name', 'salt_packages')
    op.drop_index('idx_packages_server_id', 'salt_packages')

    op.drop_index('idx_processes_state', 'salt_processes')
    op.drop_index('idx_processes_pid', 'salt_processes')
    op.drop_index('idx_processes_server_id', 'salt_processes')

    op.drop_index('idx_salt_events_created_at', 'salt_events')
    op.drop_index('idx_salt_events_processed', 'salt_events')
    op.drop_index('idx_salt_events_type', 'salt_events')
    op.drop_index('idx_salt_events_server_id', 'salt_events')

    op.drop_index('idx_salt_minions_last_seen', 'salt_minions')
    op.drop_index('idx_salt_minions_server_id', 'salt_minions')
    op.drop_index('idx_salt_minions_minion_id', 'salt_minions')

    # Drop tables
    op.drop_table('salt_logs')
    op.drop_table('salt_packages')
    op.drop_table('salt_processes')
    op.drop_table('salt_events')
    op.drop_table('salt_minions')

    # ============================================================
    # Remove Added Columns
    # ============================================================
    op.drop_column('metrics', 'metadata')
    op.drop_column('metrics', 'unit')

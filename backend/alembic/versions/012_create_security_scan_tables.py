"""Create security_scan and security_scan_report tables

Revision ID: 012
Revises: 011
Create Date: 2026-04-14 10:10:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade():
    """Create security_scan and security_scan_report tables."""
    # Create security_scans table
    op.create_table(
        'security_scans',
        sa.Column('id', sa.String(), nullable=False, primary_key=True),
        sa.Column('server_id', sa.String(), sa.ForeignKey('servers.id'), nullable=False, index=True),
        sa.Column('scan_type', sa.String(), nullable=False, index=True),
        sa.Column('status', sa.String(), nullable=False, default='pending', index=True),
        sa.Column('scan_metadata', sa.JSON(), default={}, nullable=False),
        sa.Column('results', sa.JSON(), default={}, nullable=False),
        sa.Column('summary', sa.JSON(), default={}, nullable=False),
        sa.Column('severity_counts', sa.JSON(), default={}, nullable=False),
        sa.Column('total_vulnerabilities', sa.Integer(), default=0, nullable=False),
        sa.Column('critical_vulnerabilities', sa.Integer(), default=0, nullable=False),
        sa.Column('high_vulnerabilities', sa.Integer(), default=0, nullable=False),
        sa.Column('medium_vulnerabilities', sa.Integer(), default=0, nullable=False),
        sa.Column('low_vulnerabilities', sa.Integer(), default=0, nullable=False),
        sa.Column('info_vulnerabilities', sa.Integer(), default=0, nullable=False),
        sa.Column('scan_duration', sa.Integer(), default=0, nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), index=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), onupdate=sa.text('now()'), index=True),
    )

    # Create security_scan_reports table
    op.create_table(
        'security_scan_reports',
        sa.Column('id', sa.String(), nullable=False, primary_key=True),
        sa.Column('scan_id', sa.String(), sa.ForeignKey('security_scans.id'), nullable=False, index=True),
        sa.Column('report_type', sa.String(), nullable=False, default='html'),
        sa.Column('report_format', sa.String(), nullable=False, default='detailed'),
        sa.Column('report_content', sa.JSON(), default={}, nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), index=True),
    )

    # Create indexes for PostgreSQL
    if op.get_context().dialect.name == 'postgresql':
        # Security scans indexes
        op.execute('CREATE INDEX idx_security_scans_server_id ON security_scans(server_id)')
        op.execute('CREATE INDEX idx_security_scans_scan_type ON security_scans(scan_type)')
        op.execute('CREATE INDEX idx_security_scans_status ON security_scans(status)')
        op.execute('CREATE INDEX idx_security_scans_started_at ON security_scans(started_at)')
        op.execute('CREATE INDEX idx_security_scans_completed_at ON security_scans(completed_at)')
        
        # Security scan reports indexes
        op.execute('CREATE INDEX idx_security_scan_reports_scan_id ON security_scan_reports(scan_id)')
        op.execute('CREATE INDEX idx_security_scan_reports_report_type ON security_scan_reports(report_type)')
        op.execute('CREATE INDEX idx_security_scan_reports_generated_at ON security_scan_reports(generated_at)')


def downgrade():
    """Drop security_scan and security_scan_report tables."""
    op.drop_table('security_scan_reports')
    op.drop_table('security_scans')
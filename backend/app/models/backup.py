"""Database models for backup management."""

from sqlalchemy import Column, String, Text, Boolean, Integer, BigInteger, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class BackupSchedule(Base):
    """Backup schedule model."""

    __tablename__ = "backup_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    server_id = Column(UUID(as_uuid=True), ForeignKey("servers.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    schedule_type = Column(String, nullable=False)  # 'hourly', 'daily', 'weekly', 'monthly'
    schedule_value = Column(String, nullable=True)  # Cron expression or time
    source_paths = Column(JSON, nullable=True)  # List of paths to backup
    destination = Column(JSON, nullable=True)  # Destination config
    retention_days = Column(Integer, nullable=True)  # Days to keep backups
    compression = Column(Boolean, default=True, nullable=False)
    encryption = Column(Boolean, default=False, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(String, nullable=False, server_default="NOW()")
    updated_at = Column(String, nullable=False, server_default="NOW()")

    # Relationships
    server = relationship("Server", foreign_keys=[server_id])
    organization = relationship("Organization")
    backup_reports = relationship("BackupReport", back_populates="backup_schedule", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_backup_schedules_server_id", "server_id"),
        Index("ix_backup_schedules_organization_id", "organization_id"),
        Index("ix_backup_schedules_enabled", "enabled"),
    )

    def __repr__(self) -> str:
        return f"<BackupSchedule(id={self.id}, name={self.name}, server_id={self.server_id})>"


class BackupReport(Base):
    """Backup execution report model."""

    __tablename__ = "backup_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    backup_schedule_id = Column(UUID(as_uuid=True), ForeignKey("backup_schedules.id"), nullable=True)
    server_id = Column(UUID(as_uuid=True), ForeignKey("servers.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    status = Column(String, nullable=False)  # 'pending', 'running', 'completed', 'failed'
    started_at = Column(String, nullable=True)
    completed_at = Column(String, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    files_transferred = Column(Integer, nullable=True)
    bytes_transferred = Column(BigInteger, nullable=True)
    checksum = Column(String, nullable=True)  # MD5/SHA256 checksum
    error = Column(Text, nullable=True)
    created_at = Column(String, nullable=False, server_default="NOW()")
    updated_at = Column(String, nullable=False, server_default="NOW()")

    # Relationships
    backup_schedule = relationship("BackupSchedule", back_populates="backup_reports")
    server = relationship("Server")
    organization = relationship("Organization")

    # Indexes
    __table_args__ = (
        Index("ix_backup_reports_backup_schedule_id", "backup_schedule_id"),
        Index("ix_backup_reports_server_id", "server_id"),
        Index("ix_backup_reports_organization_id", "organization_id"),
        Index("ix_backup_reports_status", "status"),
        Index("ix_backup_reports_started_at", "started_at"),
    )

    def __repr__(self) -> str:
        return f"<BackupReport(id={self.id}, status={self.status}, server_id={self.server_id})>"

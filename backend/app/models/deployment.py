"""Database models for logs and deployments."""

from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class Log(Base):
    """Log model with full-text search support."""

    __tablename__ = "logs"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    server_id = Column(UUID(as_uuid=True), ForeignKey("servers.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    log_level = Column(String, nullable=False)  # 'error', 'warning', 'info', 'debug'
    log_type = Column(String, nullable=False)  # 'system', 'application', 'security'
    message = Column(Text, nullable=False)
    timestamp = Column(String, nullable=False)  # ISO timestamp
    source = Column(String, nullable=True)  # 'nginx', 'mysql', etc.
    extra = Column(JSON, nullable=True)  # Additional metadata
    created_at = Column(String, nullable=False, server_default="NOW()")

    # Relationships
    server = relationship("Server")
    organization = relationship("Organization")

    # Indexes
    __table_args__ = (
        Index("ix_logs_server_id", "server_id"),
        Index("ix_logs_organization_id", "organization_id"),
        Index("ix_logs_log_level", "log_level"),
        Index("ix_logs_log_type", "log_type"),
        Index("ix_logs_timestamp", "timestamp"),
        Index("ix_logs_source", "source"),
    )

    def __repr__(self) -> str:
        return f"<Log(id={self.id}, level={self.log_level}, server_id={self.server_id})>"


class Deployment(Base):
    """Deployment configuration model."""

    __tablename__ = "deployments"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    server_id = Column(UUID(as_uuid=True), ForeignKey("servers.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    deployment_type = Column(String, nullable=False)  # 'manual', 'scheduled', 'git', 'docker'
    status = Column(String, nullable=False)  # 'pending', 'queued', 'running', 'completed', 'failed', 'rolled_back'
    config = Column(JSON, nullable=True)  # Deployment configuration
    schedule_type = Column(String, nullable=True)  # 'immediate', 'scheduled'
    schedule_value = Column(String, nullable=True)  # Cron expression or ISO timestamp
    current_version = Column(String, nullable=True)
    target_version = Column(String, nullable=True)
    created_at = Column(String, nullable=False, server_default="NOW()")
    updated_at = Column(String, nullable=False, server_default="NOW()")

    # Relationships
    server = relationship("Server")
    organization = relationship("Organization")
    executions = relationship("DeploymentExecution", back_populates="deployment", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_deployments_server_id", "server_id"),
        Index("ix_deployments_organization_id", "organization_id"),
        Index("ix_deployments_deployment_type", "deployment_type"),
        Index("ix_deployments_status", "status"),
        Index("ix_deployments_schedule_type", "schedule_type"),
    )

    def __repr__(self) -> str:
        return f"<Deployment(id={self.id}, name={self.name}, status={self.status})>"


class DeploymentExecution(Base):
    """Deployment execution model."""

    __tablename__ = "deployment_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    deployment_id = Column(UUID(as_uuid=True), ForeignKey("deployments.id"), nullable=False)
    server_id = Column(UUID(as_uuid=True), ForeignKey("servers.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    status = Column(String, nullable=False)  # 'pending', 'queued', 'running', 'completed', 'failed'
    dry_run = Column(Boolean, default=False, nullable=False)
    current_version = Column(String, nullable=True)
    target_version = Column(String, nullable=True)
    output = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    started_at = Column(String, nullable=True)
    completed_at = Column(String, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    rollback_available = Column(Boolean, default=False, nullable=False)
    created_at = Column(String, nullable=False, server_default="NOW()")
    updated_at = Column(String, nullable=False, server_default="NOW()")

    # Relationships
    deployment = relationship("Deployment", back_populates="executions")
    server = relationship("Server")
    organization = relationship("Organization")

    # Indexes
    __table_args__ = (
        Index("ix_deployment_executions_deployment_id", "deployment_id"),
        Index("ix_deployment_executions_server_id", "server_id"),
        Index("ix_deployment_executions_organization_id", "organization_id"),
        Index("ix_deployment_executions_status", "status"),
        Index("ix_deployment_executions_started_at", "started_at"),
    )

    def __repr__(self) -> str:
        return f"<DeploymentExecution(id={self.id}, status={self.status}, deployment_id={self.deployment_id})>"

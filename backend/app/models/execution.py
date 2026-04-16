"""Database models for command execution and SSH sessions."""

from sqlalchemy import Column, String, Text, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class Command(Base):
    """Command execution model."""

    __tablename__ = "commands"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    server_id = Column(UUID(as_uuid=True), ForeignKey("servers.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    command = Column(Text, nullable=False)
    status = Column(String, nullable=False)  # 'pending', 'running', 'completed', 'failed'
    exit_code = Column(Integer, nullable=True)
    output = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    started_at = Column(String, nullable=True)
    completed_at = Column(String, nullable=True)
    created_at = Column(String, nullable=False, server_default="NOW()")
    updated_at = Column(String, nullable=False, server_default="NOW()")

    # Relationships
    server = relationship("Server")
    organization = relationship("Organization")
    user = relationship("User")

    # Indexes
    __table_args__ = (
        Index("ix_commands_server_id", "server_id"),
        Index("ix_commands_organization_id", "organization_id"),
        Index("ix_commands_user_id", "user_id"),
        Index("ix_commands_status", "status"),
        Index("ix_commands_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Command(id={self.id}, status={self.status}, server_id={self.server_id})>"


class SSHSession(Base):
    """SSH session model."""

    __tablename__ = "ssh_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    server_id = Column(UUID(as_uuid=True), ForeignKey("servers.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(String, nullable=False)  # 'active', 'terminated', 'error'
    client_id = Column(String, nullable=True)  # WebSocket client ID
    terminal_width = Column(Integer, nullable=True)
    terminal_height = Column(Integer, nullable=True)
    last_activity_at = Column(String, nullable=True)
    terminated_at = Column(String, nullable=True)
    terminated_reason = Column(String, nullable=True)  # 'user', 'timeout', 'error'
    created_at = Column(String, nullable=False, server_default="NOW()")
    updated_at = Column(String, nullable=False, server_default="NOW()")

    # Relationships
    server = relationship("Server")
    organization = relationship("Organization")
    user = relationship("User")

    # Indexes
    __table_args__ = (
        Index("ix_ssh_sessions_server_id", "server_id"),
        Index("ix_ssh_sessions_organization_id", "organization_id"),
        Index("ix_ssh_sessions_user_id", "user_id"),
        Index("ix_ssh_sessions_status", "status"),
        Index("ix_ssh_sessions_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<SSHSession(id={self.id}, status={self.status}, server_id={self.server_id})>"

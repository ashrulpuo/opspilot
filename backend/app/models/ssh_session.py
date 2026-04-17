"""SSH session model."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class SSHSesion(Base):
    """SSH session model (aligned with Alembic `007_create_ssh_sessions`)."""

    __tablename__ = "ssh_sessions"

    id = Column(String, primary_key=True, index=True)
    server_id = Column(String, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, nullable=False)  # active, terminated, error, etc.
    client_id = Column(String, nullable=True)
    terminal_width = Column(Integer, nullable=True)
    terminal_height = Column(Integer, nullable=True)
    last_activity_at = Column(DateTime(timezone=True), nullable=True)
    terminated_at = Column(DateTime(timezone=True), nullable=True)
    terminated_reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="ssh_sessions")
    server = relationship("Server", back_populates="ssh_sessions")

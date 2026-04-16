"""SSH session model."""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class SSHSesion(Base):
    """SSH session model."""

    __tablename__ = "ssh_sessions"

    id = Column(String, primary_key=True, index=True)  # UUID
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    server_id = Column(String, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    commands = Column(Text, nullable=True)  # JSON array of commands

    # Relationships
    user = relationship("User", back_populates="ssh_sessions")
    server = relationship("Server", back_populates="ssh_sessions")

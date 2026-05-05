"""Salt log model."""
from datetime import datetime
from sqlalchemy import Column, DateTime, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects import postgresql

from app.core.database import Base


class SaltLog(Base):
    """Salt log model."""
    
    __tablename__ = "salt_logs"
    
    id = Column(String, primary_key=True)
    server_id = Column(String, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    log_level = Column(String, nullable=False)  # INFO, WARN, ERROR, DEBUG
    source = Column(String, nullable=False)  # nginx, mysql, redis, cron, etc.
    message = Column(Text, nullable=False)
    # Python name cannot be `metadata` (reserved on Declarative base); DB column stays "metadata".
    extra = Column("metadata", postgresql.JSONB(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    server = relationship("Server", back_populates="salt_logs")

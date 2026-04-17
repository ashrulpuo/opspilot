"""Salt log model."""
from datetime import datetime
from sqlalchemy import Column, DateTime, String, ForeignKey
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
    metadata = Column(postgresql.JSONB(), nullable=True)  # Additional structured data
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    server = relationship("Server", back_populates="logs")

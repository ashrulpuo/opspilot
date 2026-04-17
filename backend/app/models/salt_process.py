"""Salt process model."""
from datetime import datetime
from sqlalchemy import Column, DateTime, String, Integer, ForeignKey, Float, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects import postgresql

from app.core.database import Base


class SaltProcess(Base):
    """Salt process model."""
    
    __tablename__ = "salt_processes"
    
    id = Column(String, primary_key=True)
    server_id = Column(String, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    pid = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    command = Column(Text, nullable=True)  # Full command line
    username = Column(String, nullable=True)
    cpu_percent = Column(Float, nullable=True)  # CPU usage
    memory_percent = Column(Float, nullable=True)  # Memory usage
    state = Column(String, nullable=False)  # R, S, D, Z, T, W
    start_time = Column(DateTime, nullable=True)  # Process start time
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    server = relationship("Server", back_populates="processes")

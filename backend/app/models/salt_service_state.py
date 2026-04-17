"""Salt service state model."""
from datetime import datetime
from sqlalchemy import Column, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects import postgresql

from app.core.database import Base


class SaltServiceState(Base):
    """Salt service state model."""
    
    __tablename__ = "salt_service_states"
    
    id = Column(String, primary_key=True)
    server_id = Column(String, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    service_name = Column(String, nullable=False)
    status = Column(String, nullable=False)  # 'running', 'stopped', 'unknown'
    previous_status = Column(String, nullable=True)
    last_checked = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    server = relationship("Server", back_populates="service_states")

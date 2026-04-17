"""Salt event model."""
from datetime import datetime
from sqlalchemy import Column, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects import postgresql

from app.core.database import Base


class SaltEvent(Base):
    """Salt event (beacon alerts and system events)."""
    
    __tablename__ = "salt_events"
    
    id = Column(BigInteger, primary_key=True)
    server_id = Column(String, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    event_tag = Column(String, nullable=False)
    event_type = Column(String, nullable=False, index=True)  # 'cpu_alert', 'memory_alert', etc.
    event_data = Column(postgresql.JSONB(), nullable=False)
    processed = Column(String, nullable=False, default=False, index=True)
    created_at = Column(DateTime, nullable=False, index=True)
    
    # Relationships
    server = relationship("Server", back_populates="events")

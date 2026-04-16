"""Alert model."""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Float, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Alert(Base):
    """Alert model."""

    __tablename__ = "alerts"

    id = Column(String, primary_key=True, index=True)  # UUID
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    server_id = Column(String, ForeignKey("servers.id", ondelete="SET NULL"), nullable=True)
    type = Column(String, nullable=False)  # 'cpu', 'memory', 'disk', 'response_time'
    threshold = Column(Float, nullable=False)
    value = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="open")  # 'open', 'acknowledged', 'resolved'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="alerts")
    server = relationship("Server", back_populates="alerts")

"""Push metrics samples from OpsPilot host agents."""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, String, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class ServerMetricsPushSample(Base):
    """Single ingested metrics payload from an agent (append-only MVP)."""

    __tablename__ = "server_metrics_push_samples"

    id = Column(String, primary_key=True)
    server_id = Column(String, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    payload = Column(JSON, nullable=False)

    server = relationship("Server", back_populates="metrics_push_samples")

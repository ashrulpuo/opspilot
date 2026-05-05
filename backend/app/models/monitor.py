"""Monitor models."""
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Monitor(Base):
    __tablename__ = "monitors"

    id = Column(String, primary_key=True, index=True)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    server_id = Column(String, ForeignKey("servers.id", ondelete="SET NULL"), nullable=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, default="")
    type = Column(String, nullable=False, default="https")  # http/https/tcp/dns/push
    port = Column(Integer, nullable=True)
    interval_seconds = Column(Integer, nullable=False, default=300)
    timeout_seconds = Column(Integer, nullable=False, default=10)
    enabled = Column(Boolean, nullable=False, default=True)
    last_status = Column(String, nullable=True)  # up/down/pending
    last_checked_at = Column(DateTime, nullable=True)
    consecutive_failures = Column(Integer, nullable=False, default=0)
    heartbeat_api_key = Column(String, nullable=True, unique=True)
    ssl_days_remaining = Column(Float, nullable=True)
    avg_response_time_ms = Column(Float, nullable=True)
    uptime_7d = Column(Float, nullable=True)
    uptime_30d = Column(Float, nullable=True)
    dns_resolve_type = Column(String, nullable=True)
    dns_resolve_expected = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    checks = relationship("MonitorCheck", back_populates="monitor", cascade="all, delete-orphan")
    incidents = relationship("MonitorIncident", back_populates="monitor", cascade="all, delete-orphan")


class MonitorCheck(Base):
    __tablename__ = "monitor_checks"

    id = Column(String, primary_key=True, index=True)
    monitor_id = Column(String, ForeignKey("monitors.id", ondelete="CASCADE"), nullable=False)
    checked_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    status = Column(String, nullable=False)  # up/down
    response_time_ms = Column(Float, nullable=True)
    status_code = Column(Integer, nullable=True)
    ssl_days_remaining = Column(Float, nullable=True)
    error = Column(Text, nullable=True)

    monitor = relationship("Monitor", back_populates="checks")


class MonitorIncident(Base):
    __tablename__ = "monitor_incidents"

    id = Column(String, primary_key=True, index=True)
    monitor_id = Column(String, ForeignKey("monitors.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    monitor = relationship("Monitor", back_populates="incidents")

"""Metrics model (TimescaleDB hypertable)."""
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, PrimaryKeyConstraint, String, Index

from app.core.database import Base


class Metric(Base):
    """Metric model for time-series data."""

    __tablename__ = "metrics"

    id = Column(String, nullable=False)  # UUID
    server_id = Column(String, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    metric_name = Column(String, nullable=False, index=True)  # 'cpu_usage', 'memory_usage', 'disk_usage'
    metric_value = Column(Float, nullable=False)
    unit = Column(String, nullable=True)  # '%', 'GB', 'MB', 'seconds'

    # Composite primary key (required for TimescaleDB hypertables)
    __table_args__ = (
        PrimaryKeyConstraint('id', 'timestamp'),
        Index("idx_metrics_server_timestamp", "server_id", "timestamp"),
        Index("idx_metrics_name_timestamp", "metric_name", "timestamp"),
    )

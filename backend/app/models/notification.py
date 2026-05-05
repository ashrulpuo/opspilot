"""Notification settings models."""
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class NotificationSmtpConfig(Base):
    __tablename__ = "notification_smtp_configs"

    id = Column(String, primary_key=True, index=True)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True)
    host = Column(String, nullable=False, default="")
    port = Column(Integer, nullable=False, default=587)
    username = Column(String, nullable=False, default="")
    password = Column(String, nullable=False, default="")
    from_address = Column(String, nullable=False, default="")
    use_tls = Column(Boolean, nullable=False, default=True)
    enabled = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    organization = relationship("Organization", back_populates="smtp_config")


class NotificationRecipient(Base):
    __tablename__ = "notification_recipients"

    id = Column(String, primary_key=True, index=True)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    email = Column(String, nullable=False)
    name = Column(String, nullable=True)
    severity_filter = Column(String, nullable=False, default="all")  # 'all', 'critical', 'warning'
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    organization = relationship("Organization", back_populates="notification_recipients")

"""Singleton row tracking first-time installation / initial onboarding."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String

from app.core.database import Base


class InstallationState(Base):
    """One row (`id='default'`) — whether the one-time initial admin setup has finished."""

    __tablename__ = "installation_state"

    ROW_ID = "default"

    id = Column(String, primary_key=True)
    initial_setup_completed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

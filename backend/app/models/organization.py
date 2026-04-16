"""Organization models."""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Organization(Base):
    """Organization model."""

    __tablename__ = "organizations"

    id = Column(String, primary_key=True, index=True)  # UUID
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    servers = relationship("Server", back_populates="organization", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="organization", cascade="all, delete-orphan")


class OrganizationMember(Base):
    """Organization member model."""

    __tablename__ = "organization_members"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True)
    role = Column(String, nullable=False)  # 'owner', 'admin', 'member', 'viewer'

    # Relationships
    user = relationship("User", back_populates="organization_members")
    organization = relationship("Organization", back_populates="members")

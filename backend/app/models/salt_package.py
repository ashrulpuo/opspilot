"""Salt package model."""
from datetime import datetime
from sqlalchemy import Column, DateTime, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects import postgresql

from app.core.database import Base


class SaltPackage(Base):
    """Salt package model."""
    
    __tablename__ = "salt_packages"
    
    id = Column(String, primary_key=True)
    server_id = Column(String, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    architecture = Column(String, nullable=True)  # amd64, arm64, x86_64
    source = Column(String, nullable=False)  # apt, yum, dnf, pacman, etc.
    is_update_available = Column(Boolean, nullable=False, default=False)
    installed_date = Column(DateTime, nullable=True)
    update_version = Column(String, nullable=True)  # Latest available version
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    server = relationship("Server", back_populates="packages")

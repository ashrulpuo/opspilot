"""Credentials vault path model for OpsPilot."""
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base


class CredentialsVaultPath(Base):
    """Credentials vault path model for storing credential paths."""
    
    __tablename__ = "credentials_vault_paths"
    
    id = Column(String, primary_key=True)
    server_id = Column(String, ForeignKey("servers.id"), nullable=False, index=True)
    system_name = Column(String, nullable=True, index=True)
    vault_path = Column(String, nullable=True)
    description = Column(String, nullable=True)
    created_at = Column(String, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(String, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    server = relationship("Server", back_populates="credentials_vault_paths")
    
    def __repr__(self) -> str:
        return f"<CredentialsVaultPath(id={self.id}, server_id={self.server_id}, system_name={self.system_name})>"
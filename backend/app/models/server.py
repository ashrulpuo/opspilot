"""Server models."""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Server(Base):
    """Server model."""

    __tablename__ = "servers"

    id = Column(String, primary_key=True, index=True)  # UUID
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    hostname = Column(String, nullable=False)
    ip_address = Column(String, nullable=False)
    os_type = Column(String, nullable=False)  # 'linux', 'windows', 'macos'
    web_server_type = Column(String)  # 'nginx', 'apache', 'caddy', 'none'
    domain_name = Column(String)
    status = Column(String, nullable=False, default="active")  # 'active', 'inactive', 'error'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="servers")
    credentials = relationship("CredentialsVaultPath", back_populates="server", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="server", cascade="all, delete-orphan")
    ssh_sessions = relationship("SSHSesion", back_populates="server", cascade="all, delete-orphan")


class CredentialsVaultPath(Base):
    """Credentials vault path model."""

    __tablename__ = "credentials_vault_paths"

    id = Column(String, primary_key=True, index=True)  # UUID
    server_id = Column(String, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False)
    vault_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    server = relationship("Server", back_populates="credentials")

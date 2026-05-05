"""Server models."""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
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
    status = Column(String, nullable=False, default="offline")  # 'provisioning'|'installing_agent'|'offline'|'online'|'error'|'warning'
    agent_api_key_hash = Column(String, nullable=True, index=True)
    # Last Salt minion SSH auto-install / reinstall failure (cleared on success); not a stack trace.
    agent_install_last_error = Column(Text, nullable=True)
    agent_last_seen_at = Column(DateTime, nullable=True)
    display_name = Column(String, nullable=True)
    agent_reported_hostname = Column(String, nullable=True)
    agent_reported_ip = Column(String, nullable=True)
    agent_os_name = Column(String, nullable=True)
    agent_os_version = Column(String, nullable=True)
    agent_architecture = Column(String, nullable=True)
    agent_cpu_cores = Column(Integer, nullable=True)
    agent_memory_mb = Column(Integer, nullable=True)
    agent_facts_synced_at = Column(DateTime, nullable=True)
    host_info = Column(JSON, nullable=True)
    # OpsPilot-initiated SSH (password stored Fernet-encrypted; never expose via public API)
    ssh_username = Column(String, nullable=True)
    ssh_port = Column(Integer, nullable=True)
    ssh_password_encrypted = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="servers")
    credentials = relationship("CredentialsVaultPath", back_populates="server", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="server", cascade="all, delete-orphan")
    ssh_sessions = relationship("SSHSesion", back_populates="server", cascade="all, delete-orphan")
    metrics_push_samples = relationship(
        "ServerMetricsPushSample",
        back_populates="server",
        cascade="all, delete-orphan",
    )
    
    # SaltStack relationships
    salt_minion = relationship("SaltMinion", back_populates="server", uselist=False)
    salt_events = relationship("SaltEvent", back_populates="server", cascade="all, delete-orphan")
    salt_service_states = relationship("SaltServiceState", back_populates="server", cascade="all, delete-orphan")
    salt_processes = relationship("SaltProcess", back_populates="server", cascade="all, delete-orphan")
    salt_packages = relationship("SaltPackage", back_populates="server", cascade="all, delete-orphan")
    salt_logs = relationship("SaltLog", back_populates="server", cascade="all, delete-orphan")


class CredentialsVaultPath(Base):
    """Credentials vault path model."""

    __tablename__ = "credentials_vault_paths"

    id = Column(String, primary_key=True, index=True)  # UUID
    server_id = Column(String, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False)
    vault_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    server = relationship("Server", back_populates="credentials")

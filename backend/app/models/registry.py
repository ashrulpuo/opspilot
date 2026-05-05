"""Infrastructure Registry models."""
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class RegistryDomain(Base):
    __tablename__ = "registry_domains"

    id = Column(String, primary_key=True)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    server_id = Column(String, ForeignKey("servers.id", ondelete="SET NULL"), nullable=True)
    name = Column(String, nullable=False)
    registrar = Column(String, nullable=True)
    registered_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    auto_renew = Column(Boolean, nullable=False, default=False)
    nameservers = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    ssl_certs = relationship("RegistrySslCert", back_populates="domain", cascade="all, delete-orphan")


class RegistrySslCert(Base):
    __tablename__ = "registry_ssl_certs"

    id = Column(String, primary_key=True)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    domain_id = Column(String, ForeignKey("registry_domains.id", ondelete="SET NULL"), nullable=True)
    domain_name = Column(String, nullable=False)
    common_name = Column(String, nullable=True)
    issuer = Column(String, nullable=True)
    issued_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    fingerprint = Column(String, nullable=True)
    auto_renew = Column(Boolean, nullable=False, default=False)
    provider = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    domain = relationship("RegistryDomain", back_populates="ssl_certs")


class RegistryDbService(Base):
    __tablename__ = "registry_db_services"

    id = Column(String, primary_key=True)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    server_id = Column(String, ForeignKey("servers.id", ondelete="SET NULL"), nullable=True)
    name = Column(String, nullable=False)
    db_type = Column(String, nullable=False, default="postgres")
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=True)
    database_name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    password_enc = Column(Text, nullable=True)
    environment = Column(String, nullable=False, default="prod")
    ssl_enabled = Column(Boolean, nullable=False, default=False)
    notes = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class RegistryCredential(Base):
    __tablename__ = "registry_credentials"

    id = Column(String, primary_key=True)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    server_id = Column(String, ForeignKey("servers.id", ondelete="SET NULL"), nullable=True)
    name = Column(String, nullable=False)
    credential_type = Column(String, nullable=False, default="web_login")
    url = Column(String, nullable=True)
    username = Column(String, nullable=True)
    secret_enc = Column(Text, nullable=True)
    environment = Column(String, nullable=False, default="prod")
    notes = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class RegistryAuditLog(Base):
    __tablename__ = "registry_audit_log"

    id = Column(String, primary_key=True)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    asset_type = Column(String, nullable=False)
    asset_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

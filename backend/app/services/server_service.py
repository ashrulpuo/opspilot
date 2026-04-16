"""Server service for managing servers and Salt minion operations."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.agent_keys import generate_agent_api_key, hash_agent_api_key
from app.core.ssh_credential_crypto import decrypt_ssh_password, encrypt_ssh_password
from app.models.server import Server, CredentialsVaultPath
from app.models.organization import OrganizationMember
from app.core.config import get_settings
from app.services.salt_service import salt_service

logger = logging.getLogger(__name__)


@dataclass
class AutoInstallParams:
    username: str
    password: str
    port: int = 22


@dataclass
class CreateServerOutcome:
    server: Server
    agent_api_key_plaintext: str
    auto_install: Optional[AutoInstallParams] = None


class ServerService:
    """Service for managing servers."""

    async def create_server(
        self,
        db: AsyncSession,
        organization_id: str,
        user_id: str,
        hostname: str,
        ip_address: str,
        os_type: str,
        domain_name: Optional[str] = None,
        web_server_type: Optional[str] = None,
        *,
        auto_install_agent: bool = False,
        ssh_username: Optional[str] = None,
        ssh_password: Optional[str] = None,
        ssh_port: int = 22,
    ) -> CreateServerOutcome:
        """Create a new server, register agent API key hash, and configure Salt pillar.

        Raises:
            ValueError: If user doesn't have permission
        """
        # Check if user is member of organization
        result = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user_id,
            )
        )
        member = result.scalar_one_or_none()

        if not member:
            raise ValueError("User is not a member of this organization")

        server_id = str(uuid4())
        agent_key = generate_agent_api_key()

        ssh_user_stored: Optional[str] = None
        ssh_port_stored: Optional[int] = None
        ssh_pw_enc: Optional[str] = None
        if ssh_username and ssh_password:
            ssh_user_stored = ssh_username.strip()
            ssh_port_stored = int(ssh_port or 22)
            ssh_pw_enc = encrypt_ssh_password(ssh_password)

        server = Server(
            id=server_id,
            organization_id=organization_id,
            hostname=hostname,
            ip_address=ip_address,
            os_type=os_type,
            domain_name=domain_name,
            web_server_type=web_server_type,
            status="provisioning",
            agent_api_key_hash=hash_agent_api_key(agent_key),
            ssh_username=ssh_user_stored,
            ssh_port=ssh_port_stored,
            ssh_password_encrypted=ssh_pw_enc,
        )

        db.add(server)
        await db.commit()
        await db.refresh(server)

        try:
            await self._setup_salt_minion(server_id, hostname, ip_address, organization_id, agent_key)
        except Exception as e:
            logger.warning("Salt pillar setup failed for %s: %s", server_id, e)

        if auto_install_agent and ssh_username and ssh_password:
            server.status = "installing_agent"
        else:
            server.status = "online"
        await db.commit()
        await db.refresh(server)

        auto: Optional[AutoInstallParams] = None
        if auto_install_agent and ssh_username and ssh_password:
            auto = AutoInstallParams(username=ssh_username, password=ssh_password, port=ssh_port or 22)

        logger.info("Created server %s for organization %s", server_id, organization_id)
        return CreateServerOutcome(server=server, agent_api_key_plaintext=agent_key, auto_install=auto)

    async def _setup_salt_minion(
        self,
        server_id: str,
        hostname: str,
        ip_address: str,
        organization_id: str,
        api_key: str,
    ) -> None:
        """Set Salt pillar for minion (same API key as push agent when configured)."""
        minion = f"opspilot-minion-{server_id}"
        settings = get_settings()
        try:
            await salt_service.set_pillar(minion, "opspilot:api_key", api_key)
            await salt_service.set_pillar(minion, "opspilot:organization_id", organization_id)
            await salt_service.set_pillar(minion, "opspilot:server_id", server_id)
            await salt_service.set_pillar(minion, "opspilot:api_base_url", settings.PUBLIC_API_BASE_URL)
        except Exception as e:
            logger.warning("Salt pillar API error for server %s: %s", server_id, e)
            raise

        logger.info("Salt minion pillar setup for server %s completed", server_id)

    async def get_server(
        self,
        db: AsyncSession,
        server_id: str,
        user_id: str,
    ) -> Optional[Server]:
        """Get a server by ID.

        Args:
            db: Database session
            server_id: Server ID
            user_id: User ID (for permission check)

        Returns:
            Server if found and user has permission, None otherwise
        """
        result = await db.execute(
            select(Server).where(Server.id == server_id)
        )
        server = result.scalar_one_or_none()

        if not server:
            return None

        # Check permission
        result = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == server.organization_id,
                OrganizationMember.user_id == user_id,
            )
        )
        member = result.scalar_one_or_none()

        if not member:
            return None

        return server

    async def list_servers(
        self,
        db: AsyncSession,
        organization_id: str,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Server]:
        """List all servers for an organization.

        Args:
            db: Database session
            organization_id: Organization ID
            user_id: User ID (for permission check)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of servers

        Raises:
            ValueError: If user doesn't have permission
        """
        # Check permission
        result = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user_id,
            )
        )
        member = result.scalar_one_or_none()

        if not member:
            raise ValueError("User is not a member of this organization")

        # List servers
        result = await db.execute(
            select(Server)
            .where(Server.organization_id == organization_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update_server(
        self,
        db: AsyncSession,
        server_id: str,
        user_id: str,
        updates: Dict[str, Any],
    ) -> Optional[Server]:
        """Update a server.

        Args:
            db: Database session
            server_id: Server ID
            user_id: User ID (for permission check)
            updates: Dictionary of fields to update

        Returns:
            Updated server if found and user has permission, None otherwise
        """
        server = await self.get_server(db, server_id, user_id)

        if not server:
            return None

        # Update fields
        for field, value in updates.items():
            if hasattr(server, field):
                setattr(server, field, value)

        server.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(server)

        return server

    async def delete_server(
        self,
        db: AsyncSession,
        server_id: str,
        user_id: str,
    ) -> bool:
        """Delete a server.

        Args:
            db: Database session
            server_id: Server ID
            user_id: User ID (for permission check)

        Returns:
            True if deleted, False otherwise
        """
        server = await self.get_server(db, server_id, user_id)

        if not server:
            return False

        # Delete Salt minion key
        try:
            await salt_service.delete_key(f"opspilot-minion-{server_id}")
        except Exception as e:
            logger.warning(f"Failed to delete Salt key for server {server_id}: {e}")

        # Delete server (cascade will delete credentials, alerts, etc.)
        await db.delete(server)
        await db.commit()

        logger.info(f"Deleted server {server_id}")
        return True

    async def get_metrics_for_dashboard(
        self,
        db: AsyncSession,
        server_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Prefer fresh push-agent metrics; otherwise Salt pull; else stale push payload."""
        from app.services.metrics_push_service import get_fresh_push_metrics, get_latest_push_sample

        fresh = await get_fresh_push_metrics(db, server_id)
        if fresh is not None:
            return fresh
        try:
            return await self.collect_metrics(db, server_id, user_id)
        except ValueError as e:
            if str(e) == "Server not found":
                raise
            logger.warning("Salt collect_metrics failed for %s: %s", server_id, e)
            latest = await get_latest_push_sample(db, server_id)
            if latest is not None:
                return latest[1]
            raise ValueError("Failed to collect metrics") from e
        except Exception as e:
            logger.warning("Salt collect_metrics failed for %s: %s", server_id, e)
            latest = await get_latest_push_sample(db, server_id)
            if latest is not None:
                return latest[1]
            raise ValueError("Failed to collect metrics") from e

    async def collect_metrics(
        self,
        db: AsyncSession,
        server_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Collect metrics from a server via Salt.

        Args:
            db: Database session
            server_id: Server ID
            user_id: User ID (for permission check)

        Returns:
            Metrics data

        Raises:
            ValueError: If server not found or no permission
        """
        server = await self.get_server(db, server_id, user_id)

        if not server:
            raise ValueError("Server not found")

        minion_id = f"opspilot-minion-{server_id}"

        try:
            metrics = await salt_service.collect_metrics(minion_id)
            return metrics
        except Exception as e:
            logger.error(f"Failed to collect metrics from server {server_id}: {e}")
            raise ValueError(f"Failed to collect metrics: {e}")

    async def execute_backup(
        self,
        db: AsyncSession,
        server_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Execute backup on a server via Salt.

        Args:
            db: Database session
            server_id: Server ID
            user_id: User ID (for permission check)

        Returns:
            Backup result

        Raises:
            ValueError: If server not found or no permission
        """
        server = await self.get_server(db, server_id, user_id)

        if not server:
            raise ValueError("Server not found")

        minion_id = f"opspilot-minion-{server_id}"

        try:
            result = await salt_service.execute_backup(minion_id)
            return result
        except Exception as e:
            logger.error(f"Failed to execute backup on server {server_id}: {e}")
            raise ValueError(f"Failed to execute backup: {e}")

    async def health_check(
        self,
        db: AsyncSession,
        server_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Perform health check on a server via Salt.

        Args:
            db: Database session
            server_id: Server ID
            user_id: User ID (for permission check)

        Returns:
            Health check result

        Raises:
            ValueError: If server not found or no permission
        """
        server = await self.get_server(db, server_id, user_id)

        if not server:
            raise ValueError("Server not found")

        minion_id = f"opspilot-minion-{server_id}"

        try:
            result = await salt_service.health_check(minion_id)
            return result
        except Exception as e:
            logger.error(f"Failed to perform health check on server {server_id}: {e}")
            raise ValueError(f"Failed to perform health check: {e}")

    async def apply_salt_state(
        self,
        db: AsyncSession,
        server_id: str,
        user_id: str,
        state: str,
        test: bool = False,
    ) -> Dict[str, Any]:
        """Apply Salt state to a server.

        Args:
            db: Database session
            server_id: Server ID
            user_id: User ID (for permission check)
            state: State to apply (e.g., 'opspilot.setup')
            test: Test mode (no changes)

        Returns:
            State application result

        Raises:
            ValueError: If server not found or no permission
        """
        server = await self.get_server(db, server_id, user_id)

        if not server:
            raise ValueError("Server not found")

        minion_id = f"opspilot-minion-{server_id}"

        try:
            result = await salt_service.apply_state(minion_id, state, test)
            return result
        except Exception as e:
            logger.error(f"Failed to apply state {state} on server {server_id}: {e}")
            raise ValueError(f"Failed to apply state: {e}")

    async def get_decrypted_ssh_credentials(
        self,
        db: AsyncSession,
        server_id: str,
        user_id: str,
    ) -> Optional[Tuple[str, int, str]]:
        """Return (username, port, plaintext_password) for OpsPilot-initiated SSH. None if unset."""
        server = await self.get_server(db, server_id, user_id)
        if not server or not server.ssh_username or not server.ssh_password_encrypted:
            return None
        port = int(server.ssh_port or 22)
        password = decrypt_ssh_password(server.ssh_password_encrypted)
        return server.ssh_username, port, password


# Global server service instance
server_service = ServerService()

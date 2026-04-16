"""Server service for managing servers and Salt minion operations."""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.server import Server, CredentialsVaultPath
from app.models.organization import OrganizationMember
from app.services.salt_service import salt_service

logger = logging.getLogger(__name__)


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
    ) -> Server:
        """Create a new server and set up Salt minion.

        Args:
            db: Database session
            organization_id: Organization ID
            user_id: User ID (for permission check)
            hostname: Server hostname
            ip_address: Server IP address
            os_type: Operating system type
            domain_name: Domain name (optional)
            web_server_type: Web server type (optional)

        Returns:
            Created server

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

        # Create server
        server_id = str(uuid4())
        server = Server(
            id=server_id,
            organization_id=organization_id,
            hostname=hostname,
            ip_address=ip_address,
            os_type=os_type,
            domain_name=domain_name,
            web_server_type=web_server_type,
            status="provisioning",
        )

        db.add(server)
        await db.commit()
        await db.refresh(server)

        # Set up Salt minion configuration
        await self._setup_salt_minion(server_id, hostname, ip_address, organization_id)

        # Update server status to active
        server.status = "active"
        await db.commit()

        logger.info(f"Created server {server_id} for organization {organization_id}")
        return server

    async def _setup_salt_minion(
        self,
        server_id: str,
        hostname: str,
        ip_address: str,
        organization_id: str,
    ) -> None:
        """Set up Salt minion for server.

        This would typically involve:
        1. Installing Salt minion on the server
        2. Configuring the minion
        3. Accepting the minion key on the master

        Args:
            server_id: Server ID
            hostname: Server hostname
            ip_address: Server IP address
            organization_id: Organization ID
        """
        # Generate API key for server
        api_key = str(uuid4())

        # Set pillar data for server
        await salt_service.set_pillar(
            f"opspilot-minion-{server_id}",
            "opspilot:api_key",
            api_key,
        )

        await salt_service.set_pillar(
            f"opspilot-minion-{server_id}",
            "opspilot:organization_id",
            organization_id,
        )

        # TODO: Implement actual minion setup (SSH to server, install Salt, etc.)
        logger.info(f"Salt minion setup for server {server_id} completed")

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


# Global server service instance
server_service = ServerService()

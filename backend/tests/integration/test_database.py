"""Integration tests for database operations."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.organization import Organization
from app.models.server import Server


@pytest.mark.integration
class TestDatabaseOperations:
    """Test database operations."""

    async def test_create_user(self, db_session: AsyncSession):
        """Test creating a user in the database."""
        user = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password="hashed_password_here",
        )

        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert user.email == "test@example.com"

    async def test_create_organization(self, db_session: AsyncSession):
        """Test creating an organization in the database."""
        org = Organization(
            name="Test Organization",
            description="Test description",
        )

        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)

        assert org.id is not None
        assert org.name == "Test Organization"

    async def test_create_server(self, db_session: AsyncSession):
        """Test creating a server in the database."""
        # First create organization
        org = Organization(name="Test Org")
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)

        # Now create server
        server = Server(
            hostname="test-server",
            ip_address="192.168.1.100",
            port=22,
            organization_id=org.id,
        )

        db_session.add(server)
        await db_session.commit()
        await db_session.refresh(server)

        assert server.id is not None
        assert server.hostname == "test-server"
        assert server.organization_id == org.id

    async def test_user_organization_relationship(self, db_session: AsyncSession):
        """Test user-organization relationship."""
        # Create user
        user = User(
            email="user@example.com",
            full_name="User",
            hashed_password="hashed",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create organization
        org = Organization(
            name="User Org",
            created_by=user.id,
        )
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)

        # Verify relationship
        assert org.created_by == user.id

    async def test_server_organization_relationship(self, db_session: AsyncSession):
        """Test server-organization relationship."""
        # Create organization
        org = Organization(name="Server Org")
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)

        # Create servers
        server1 = Server(
            hostname="server-1",
            ip_address="192.168.1.101",
            port=22,
            organization_id=org.id,
        )
        server2 = Server(
            hostname="server-2",
            ip_address="192.168.1.102",
            port=22,
            organization_id=org.id,
        )

        db_session.add_all([server1, server2])
        await db_session.commit()

        # Query servers by organization
        result = await db_session.execute(
            select(Server).where(Server.organization_id == org.id)
        )
        servers = result.scalars().all()

        assert len(servers) == 2
        assert all(s.organization_id == org.id for s in servers)

    async def test_update_user(self, db_session: AsyncSession):
        """Test updating a user."""
        user = User(
            email="update@example.com",
            full_name="Update User",
            hashed_password="hashed",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Update user
        user.full_name = "Updated User"
        await db_session.commit()
        await db_session.refresh(user)

        assert user.full_name == "Updated User"

    async def test_delete_server(self, db_session: AsyncSession):
        """Test deleting a server."""
        # Create organization
        org = Organization(name="Delete Org")
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)

        # Create server
        server = Server(
            hostname="delete-server",
            ip_address="192.168.1.104",
            port=22,
            organization_id=org.id,
        )
        db_session.add(server)
        await db_session.commit()
        await db_session.refresh(server)

        server_id = server.id

        # Delete server
        await db_session.delete(server)
        await db_session.commit()

        # Verify deletion
        result = await db_session.execute(
            select(Server).where(Server.id == server_id)
        )
        deleted_server = result.scalar_one_or_none()

        assert deleted_server is None

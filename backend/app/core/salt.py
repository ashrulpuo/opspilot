"""SaltStack client wrapper for OpsPilot."""
import logging
from typing import Dict, Any, List, Optional
import httpx
import json

from app.core.config import settings

logger = logging.getLogger(__name__)


class SaltClient:
    """Salt API client wrapper for interacting with Salt master."""

    def __init__(self):
        """Initialize Salt client."""
        self.base_url = settings.salt_api_url
        self.username = settings.salt_api_username
        self.password = settings.salt_api_password
        self.token = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Salt API and get token."""
        try:
            response = httpx.post(
                f"{self.base_url}/login",
                json={
                    "username": self.username,
                    "password": self.password,
                    "eauth": "pam"
                },
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data["return"][0]["token"]
                logger.info("Successfully authenticated with Salt API")
            else:
                logger.error(f"Failed to authenticate with Salt API: {response.status_code}")
                self.token = None

        except Exception as e:
            logger.error(f"Salt API authentication error: {e}")
            self.token = None

    def is_authenticated(self) -> bool:
        """Check if client is authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        return self.token is not None

    async def execute_command(
        self,
        target: str,
        command: str,
        arg: List[str] = None,
        client: str = "local",
        timeout: int = 300
    ) -> Optional[Dict[str, Any]]:
        """Execute a Salt command on target minions.

        Args:
            target: Target specification (minion ID, glob, etc.)
            command: Salt command (e.g., "cmd.run", "test.ping")
            arg: Command arguments
            client: Salt client type (local, local_async, runner, wheel)
            timeout: Command timeout in seconds

        Returns:
            Command result, or None if failed
        """
        if not self.is_authenticated():
            logger.error("Not authenticated with Salt API")
            return None

        try:
            headers = {
                "X-Auth-Token": self.token
            }

            payload = {
                "client": client,
                "tgt": target,
                "fun": command,
            }

            if arg:
                payload["arg"] = arg

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.base_url}/",
                    headers=headers,
                    json=payload
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["return"][0]

                logger.error(f"Salt command failed: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Salt command execution error: {e}")
            return None

    async def ping(self, target: str = "*") -> Dict[str, bool]:
        """Ping all or specific minions.

        Args:
            target: Target specification (default: all minions)

        Returns:
            Dictionary mapping minion IDs to ping status
        """
        result = await self.execute_command(
            target=target,
            command="test.ping",
            client="local",
            timeout=30
        )

        if result is None:
            return {}

        return result

    async def get_grains(self, target: str = "*") -> Dict[str, Dict[str, Any]]:
        """Get grains for all or specific minions.

        Args:
            target: Target specification (default: all minions)

        Returns:
            Dictionary mapping minion IDs to grains
        """
        result = await self.execute_command(
            target=target,
            command="grains.items",
            client="local",
            timeout=30
        )

        if result is None:
            return {}

        return result

    async def list_minions(self) -> List[str]:
        """List all connected minions.

        Returns:
            List of minion IDs
        """
        result = await self.execute_command(
            target="*",
            command="wheel.key.list_all",
            client="wheel",
            timeout=10
        )

        if result is None:
            return []

        # Return both accepted and pending minions
        minions = set()
        if "minions" in result:
            minions.update(result["minions"])
        if "minions_pre" in result:
            minions.update(result["minions_pre"])

        return list(minions)

    async def accept_key(self, minion_id: str) -> bool:
        """Accept a pending minion key.

        Args:
            minion_id: Minion ID to accept

        Returns:
            True if successful, False otherwise
        """
        result = await self.execute_command(
            target=minion_id,
            command="wheel.key.accept",
            client="wheel",
            timeout=10
        )

        return result is not None

    async def delete_key(self, minion_id: str) -> bool:
        """Delete a minion key.

        Args:
            minion_id: Minion ID to delete

        Returns:
            True if successful, False otherwise
        """
        result = await self.execute_command(
            target=minion_id,
            command="wheel.key.delete",
            client="wheel",
            timeout=10
        )

        return result is not None

    async def get_metrics(self, minion_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics from a specific minion using custom module.

        Args:
            minion_id: Minion ID

        Returns:
            Metrics dictionary, or None if failed
        """
        result = await self.execute_command(
            target=minion_id,
            command="metrics_collector.collect",
            client="local",
            timeout=60
        )

        if result and minion_id in result:
            return result[minion_id]

        return None

    async def run_backup(
        self,
        minion_id: str,
        backup_config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Run backup on a specific minion.

        Args:
            minion_id: Minion ID
            backup_config: Backup configuration

        Returns:
            Backup result, or None if failed
        """
        result = await self.execute_command(
            target=minion_id,
            command="backup_runner.run",
            arg=[json.dumps(backup_config)],
            client="local",
            timeout=3600  # 1 hour timeout
        )

        if result and minion_id in result:
            return result[minion_id]

        return None

    async def check_health(self, minion_id: str) -> Optional[Dict[str, Any]]:
        """Run health checks on a specific minion.

        Args:
            minion_id: Minion ID

        Returns:
            Health check results, or None if failed
        """
        result = await self.execute_command(
            target=minion_id,
            command="health_checker.check",
            client="local",
            timeout=120
        )

        if result and minion_id in result:
            return result[minion_id]

        return None

    async def apply_state(
        self,
        minion_id: str,
        state: str,
        test: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Apply a Salt state to a minion.

        Args:
            minion_id: Minion ID
            state: State name (e.g., "opspilot.monitoring")
            test: Run in test mode (dry run)

        Returns:
            State application result, or None if failed
        """
        arg = ["test=True"] if test else []

        result = await self.execute_command(
            target=minion_id,
            command="state.apply",
            arg=[state] + arg,
            client="local",
            timeout=600
        )

        if result and minion_id in result:
            return result[minion_id]

        return None

    async def execute_shell_command(
        self,
        minion_id: str,
        command: str,
        timeout: int = 300
    ) -> Optional[Dict[str, Any]]:
        """Execute a shell command on a minion.

        Args:
            minion_id: Minion ID
            command: Shell command to execute
            timeout: Command timeout in seconds

        Returns:
            Command result (stdout, stderr, retcode), or None if failed
        """
        result = await self.execute_command(
            target=minion_id,
            command="cmd.run_all",
            arg=[command],
            client="local",
            timeout=timeout
        )

        if result and minion_id in result:
            return result[minion_id]

        return None


# Global Salt client instance
salt_client = SaltClient()

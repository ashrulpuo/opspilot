"""SaltStack integration service."""
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class SaltService:
    """SaltStack API client for OpsPilot."""

    def __init__(self):
        """Initialize Salt service."""
        self.base_url = settings.salt_api_url
        self.username = settings.salt_api_username
        self.password = settings.salt_api_password
        self.eauth = "pam"
        self.token: Optional[str] = None
        self.token_expires: Optional[datetime] = None

    async def _get_token(self) -> str:
        """Get or renew Salt API token."""
        if self.token and self.token_expires and self.token_expires > datetime.utcnow():
            return self.token

        # Authenticate with Salt API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/login",
                json={
                    "username": self.username,
                    "password": self.password,
                    "eauth": self.eauth,
                },
            )
            response.raise_for_status()
            data = response.json()

            self.token = data["return"][0]["token"]
            self.token_expires = datetime.utcnow().replace(hour=23, minute=59, second=59)
            logger.info("Salt API token obtained")
            return self.token

    async def _execute(
        self,
        client_type: str,
        client: str,
        function: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None,
    ) -> Any:
        """Execute Salt command.

        Args:
            client_type: 'local', 'local_async', 'runner', etc.
            client: Target minion or '*'
            function: Salt module.function
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Command result

        Raises:
            httpx.HTTPError: If Salt API request fails
        """
        token = await self._get_token()

        payload = {
            "token": token,
            "client": client_type,
            "tgt": client,
            "fun": function,
        }

        if args:
            payload["arg"] = args
        if kwargs:
            payload["kwarg"] = kwargs

        async with httpx.AsyncClient(timeout=300.0) as http_client:
            response = await http_client.post(
                f"{self.base_url}",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["return"][0]

    async def ping_minion(self, minion_id: str) -> Dict[str, Any]:
        """Ping a minion to check connectivity.

        Args:
            minion_id: Target minion ID

        Returns:
            Ping result
        """
        result = await self._execute("local", minion_id, "test.ping")
        return {minion_id: result}

    async def get_grains(self, minion_id: str) -> Dict[str, Any]:
        """Get grains from a minion.

        Args:
            minion_id: Target minion ID

        Returns:
            Grains data
        """
        result = await self._execute("local", minion_id, "grains.items")
        return result

    async def collect_metrics(self, minion_id: str) -> Dict[str, Any]:
        """Collect metrics from a minion using Salt module.

        Args:
            minion_id: Target minion ID

        Returns:
            Metrics data
        """
        result = await self._execute("local", minion_id, "metrics_collector.collect")
        return result

    async def execute_backup(self, minion_id: str) -> Dict[str, Any]:
        """Execute backup on a minion.

        Args:
            minion_id: Target minion ID

        Returns:
            Backup result
        """
        result = await self._execute("local", minion_id, "backup_runner.execute")
        return result

    async def health_check(self, minion_id: str) -> Dict[str, Any]:
        """Perform health check on a minion.

        Args:
            minion_id: Target minion ID

        Returns:
            Health check result
        """
        result = await self._execute("local", minion_id, "health_checker.perform_checks")
        return result

    async def apply_state(self, minion_id: str, state: str, test: bool = False) -> Dict[str, Any]:
        """Apply Salt state to a minion.

        Args:
            minion_id: Target minion ID
            state: State to apply (e.g., 'opspilot.setup')
            test: Test mode (no changes)

        Returns:
            State application result
        """
        result = await self._execute(
            "local",
            minion_id,
            "state.apply",
            args=[state],
            kwargs={"test": test},
        )
        return result

    async def run_command(self, minion_id: str, command: str) -> Dict[str, Any]:
        """Run shell command on a minion.

        Args:
            minion_id: Target minion ID
            command: Command to execute

        Returns:
            Command output
        """
        result = await self._execute(
            "local",
            minion_id,
            "cmd.run",
            args=[command],
        )
        return {minion_id: result}

    async def get_active_jobs(self) -> List[Dict[str, Any]]:
        """Get list of active Salt jobs.

        Returns:
            List of active jobs
        """
        result = await self._execute("runner", "", "jobs.active")
        return result

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a Salt job.

        Args:
            job_id: Job ID

        Returns:
            Job status
        """
        result = await self._execute("runner", "", "jobs.lookup_jid", args=[job_id])
        return result

    async def accept_key(self, minion_id: str) -> Dict[str, Any]:
        """Accept a new minion key.

        Args:
            minion_id: Minion ID

        Returns:
            Key acceptance result
        """
        result = await self._execute("wheel", "", "key.accept", args=[minion_id])
        return result

    async def delete_key(self, minion_id: str) -> Dict[str, Any]:
        """Delete a minion key.

        Args:
            minion_id: Minion ID

        Returns:
            Key deletion result
        """
        result = await self._execute("wheel", "", "key.delete", args=[minion_id])
        return result

    async def list_keys(self) -> Dict[str, List[str]]:
        """List all minion keys.

        Returns:
            Dict with 'minions', 'minions_pre', 'minions_rejected', 'minions_denied'
        """
        result = await self._execute("wheel", "", "key.list_all")
        return result

    async def get_pillar(self, minion_id: str) -> Dict[str, Any]:
        """Get pillar data for a minion.

        Args:
            minion_id: Target minion ID

        Returns:
            Pillar data
        """
        result = await self._execute("local", minion_id, "pillar.items")
        return result

    async def set_pillar(self, minion_id: str, key: str, value: Any) -> Dict[str, Any]:
        """Set pillar data for a minion.

        Args:
            minion_id: Target minion ID
            key: Pillar key
            value: Pillar value

        Returns:
            Pillar update result
        """
        result = await self._execute(
            "local",
            minion_id,
            "pillar.set",
            args=[key, value],
        )
        return result


# Global salt service instance
salt_service = SaltService()

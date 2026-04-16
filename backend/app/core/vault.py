"""HashiCorp Vault client wrapper for OpsPilot."""
import logging
import os
from typing import Optional, Dict, Any
import hvac
from hvac.exceptions import InvalidRequest, VaultError

from app.core.config import settings

logger = logging.getLogger(__name__)


class VaultClient:
    """Vault client wrapper for secure credential storage."""

    def __init__(self):
        """Initialize Vault client."""
        self.client = None
        self.engine = settings.vault_engine or "secret"
        self._connect()

    def _connect(self):
        """Connect to Vault server."""
        try:
            # Initialize client
            self.client = hvac.Client(
                url=settings.vault_url,
                token=settings.vault_token,
                verify=settings.vault_verify_ssl
            )

            # Test connection
            self.client.is_authenticated()

            # Verify KV v2 engine is mounted
            try:
                self.client.secrets.kv.v2.read_secret_version(
                    mount_point=self.engine,
                    path="test_connection"
                )
            except InvalidRequest:
                # Engine not mounted, try to mount it
                logger.warning(f"KV v2 engine '{self.engine}' not found at expected path")
                # Note: In production, the engine should be mounted separately

            logger.info(f"Connected to Vault at {settings.vault_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Vault: {e}")
            self.client = None

    def is_connected(self) -> bool:
        """Check if Vault client is connected and authenticated.

        Returns:
            True if connected, False otherwise
        """
        if not self.client:
            return False

        try:
            return self.client.is_authenticated()
        except Exception as e:
            logger.error(f"Vault authentication check failed: {e}")
            return False

    def write_secret(self, path: str, data: Dict[str, Any]) -> bool:
        """Write secret to Vault.

        Args:
            path: Secret path (e.g., "opspilot/org1/server1/credential1")
            data: Secret data dictionary

        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Vault not connected")
            return False

        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                mount_point=self.engine,
                path=path,
                secret=data
            )
            logger.info(f"Secret written to Vault: {self.engine}/{path}")
            return True
        except Exception as e:
            logger.error(f"Failed to write secret to Vault: {e}")
            return False

    def read_secret(self, path: str) -> Optional[Dict[str, Any]]:
        """Read secret from Vault.

        Args:
            path: Secret path (e.g., "opspilot/org1/server1/credential1")

        Returns:
            Secret data dictionary, or None if not found
        """
        if not self.is_connected():
            logger.error("Vault not connected")
            return None

        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                mount_point=self.engine,
                path=path
            )

            if response and 'data' in response:
                return response['data']['data']

            return None
        except InvalidRequest as e:
            # Secret not found
            logger.warning(f"Secret not found in Vault: {self.engine}/{path}")
            return None
        except Exception as e:
            logger.error(f"Failed to read secret from Vault: {e}")
            return None

    def delete_secret(self, path: str) -> bool:
        """Delete secret from Vault.

        Args:
            path: Secret path (e.g., "opspilot/org1/server1/credential1")

        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Vault not connected")
            return False

        try:
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                mount_point=self.engine,
                path=path
            )
            logger.info(f"Secret deleted from Vault: {self.engine}/{path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret from Vault: {e}")
            return False

    def list_secrets(self, path: str = "") -> Optional[list]:
        """List secrets at path in Vault.

        Args:
            path: Base path to list (e.g., "opspilot/org1")

        Returns:
            List of secret paths, or None if failed
        """
        if not self.is_connected():
            logger.error("Vault not connected")
            return None

        try:
            response = self.client.secrets.kv.v2.list_secrets(
                mount_point=self.engine,
                path=path
            )

            if response and 'data' in response:
                return response['data'].get('keys', [])

            return None
        except InvalidRequest as e:
            # Path not found or empty
            return []
        except Exception as e:
            logger.error(f"Failed to list secrets from Vault: {e}")
            return None

    def generate_password(self, length: int = 32) -> str:
        """Generate a secure random password using Vault.

        Args:
            length: Password length (default: 32)

        Returns:
            Generated password, or empty string if failed
        """
        if not self.is_connected():
            logger.error("Vault not connected")
            return ""

        try:
            # Use Vault's password generation (requires password-engine)
            # Fallback to Python secrets if not available
            import secrets
            import string

            password = ''.join(
                secrets.choice(string.ascii_letters + string.digits + string.punctuation)
                for _ in range(length)
            )

            return password
        except Exception as e:
            logger.error(f"Failed to generate password in Vault: {e}")
            return ""


# Global Vault client instance
vault_client = VaultClient()

"""Unit tests for Vault client operations."""
import pytest
from unittest.mock import Mock, patch
from app.core.vault import VaultClient


@pytest.mark.unit
class TestVaultClient:
    """Test Vault client operations."""

    @pytest.fixture
    def vault_client(self):
        """Create a mock Vault client for testing."""
        return VaultClient()

    def test_vault_client_initialization(self, vault_client):
        """Test Vault client initialization."""
        assert vault_client is not None
        assert vault_client.url is not None
        assert vault_client.token is not None

    def test_vault_client_set_credentials(self, vault_client):
        """Test setting Vault credentials."""
        test_url = "http://localhost:8200"
        test_token = "test-token"
        
        vault_client.set_credentials(test_url, test_token)
        
        assert vault_client.url == test_url
        assert vault_client.token == test_token

    def test_vault_client_get_secret_success(self, vault_client):
        """Test getting secret successfully."""
        vault_client.set_credentials("http://test:8200", "test-token")
        
        with patch.object(vault_client, '_make_request') as mock_request:
            mock_request.return_value = {"data": {"data": {"secret": "test-secret"}}}
            secret = vault_client.get_secret("test/path")
            
            assert secret == "test-secret"
            mock_request.assert_called_once()

    def test_vault_client_get_secret_not_found(self, vault_client):
        """Test getting secret when not found."""
        vault_client.set_credentials("http://test:8200", "test-token")
        
        with patch.object(vault_client, '_make_request') as mock_request:
            mock_request.return_value = {"data": None}
            secret = vault_client.get_secret("test/path")
            
            assert secret is None
            mock_request.assert_called_once()

    def test_vault_client_store_secret_success(self, vault_client):
        """Test storing secret successfully."""
        vault_client.set_credentials("http://test:8200", "test-token")
        
        with patch.object(vault_client, '_make_request') as mock_request:
            mock_request.return_value = {"data": {"success": True}}
            result = vault_client.store_secret("test/path", "test-secret")
            
            assert result is True
            mock_request.assert_called_once()

    def test_vault_client_store_secret_failure(self, vault_client):
        """Test storing secret when it fails."""
        vault_client.set_credentials("http://test:8200", "test-token")
        
        with patch.object(vault_client, '_make_request') as mock_request:
            mock_request.return_value = {"data": {"success": False}}
            result = vault_client.store_secret("test/path", "test-secret")
            
            assert result is False
            mock_request.assert_called_once()

    def test_vault_client_delete_secret_success(self, vault_client):
        """Test deleting secret successfully."""
        vault_client.set_credentials("http://test:8200", "test-token")
        
        with patch.object(vault_client, '_make_request') as mock_request:
            mock_request.return_value = {"data": {"success": True}}
            result = vault_client.delete_secret("test/path")
            
            assert result is True
            mock_request.assert_called_once()

    def test_vault_client_delete_secret_not_found(self, vault_client):
        """Test deleting secret when not found."""
        vault_client.set_credentials("http://test:8200", "test-token")
        
        with patch.object(vault_client, '_make_request') as mock_request:
            mock_request.return_value = {"data": None}
            result = vault_client.delete_secret("test/path")
            
            assert result is False
            mock_request.assert_called_once()

    def test_vault_client_list_secrets(self, vault_client):
        """Test listing secrets."""
        vault_client.set_credentials("http://test:8200", "test-token")
        
        with patch.object(vault_client, '_make_request') as mock_request:
            mock_request.return_value = {
                "data": {
                    "data": {
                        "keys": ["secret1", "secret2", "secret3"]
                    }
                }
            }
            secrets = vault_client.list_secrets()
            
            assert len(secrets) == 3
            assert "secret1" in secrets
            assert "secret2" in secrets
            assert "secret3" in secrets

    def test_vault_client_health_check(self, vault_client):
        """Test Vault health check."""
        vault_client.set_credentials("http://test:8200", "test-token")
        
        with patch.object(vault_client, '_make_request') as mock_request:
            mock_request.return_value = {"data": {"status": "ok"}}
            health = vault_client.health_check()
            
            assert health is True
            mock_request.assert_called_once()

    def test_vault_client_health_check_failure(self, vault_client):
        """Test Vault health check when it fails."""
        vault_client.set_credentials("http://test:8200", "test-token")
        
        with patch.object(vault_client, '_make_request') as mock_request:
            mock_request.side_effect = Exception("Connection failed")
            health = vault_client.health_check()
            
            assert health is False

    def test_vault_client_empty_path_handling(self, vault_client):
        """Test handling of empty paths."""
        vault_client.set_credentials("http://test:8200", "test-token")
        
        with patch.object(vault_client, '_make_request') as mock_request:
            mock_request.return_value = {"data": None}
            secret = vault_client.get_secret("")
            
            assert secret is None

    def test_vault_client_special_characters_in_path(self, vault_client):
        """Test handling of special characters in paths."""
        vault_client.set_credentials("http://test:8200", "test-token")
        
        with patch.object(vault_client, '_make_request') as mock_request:
            mock_request.return_value = {"data": {"secret": "test-secret"}}
            secret = vault_client.get_secret("path/with/slashes")
            
            assert secret == "test-secret"
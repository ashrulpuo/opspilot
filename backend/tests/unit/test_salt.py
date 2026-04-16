"""Unit tests for Salt API client operations."""
import pytest
from unittest.mock import Mock, patch
from app.core.salt import SaltClient


@pytest.mark.unit
class TestSaltClient:
    """Test Salt API client operations."""

    @pytest.fixture
    def salt_client(self):
        """Create a mock Salt client for testing."""
        return SaltClient()

    def test_salt_client_initialization(self, salt_client):
        """Test Salt client initialization."""
        assert salt_client is not None
        assert salt_client.base_url is not None
        assert salt_client.username is not None
        assert salt_client.password is not None

    def test_salt_client_set_credentials(self, salt_client):
        """Test setting Salt credentials."""
        test_url = "http://localhost:8000"
        test_username = "saltapi"
        test_password = "testpass"
        
        salt_client.set_credentials(test_url, test_username, test_password)
        
        assert salt_client.base_url == test_url
        assert salt_client.username == test_username
        assert salt_client.password == test_password

    def test_salt_client_execute_command_success(self, salt_client):
        """Test executing Salt command successfully."""
        salt_client.set_credentials("http://localhost:8000", "saltapi", "testpass")
        
        with patch.object(salt_client, '_make_request') as mock_request:
            mock_request.return_value = {
                "return": [
                    {"minions": ["minion1"], "success": True}
                ]
            }
            result = salt_client.execute_command("test.minion", "test.run", ["arg1", "arg2"])
            
            assert result is True
            mock_request.assert_called_once()

    def test_salt_client_execute_command_failure(self, salt_client):
        """Test executing Salt command when it fails."""
        salt_client.set_credentials("http://localhost:8000", "saltapi", "testpass")
        
        with patch.object(salt_client, '_make_request') as mock_request:
            mock_request.return_value = {
                "return": [
                    {"minions": [], "success": False}
                ]
            }
            result = salt_client.execute_command("test.minion", "test.run", ["arg1"])
            
            assert result is False
            mock_request.assert_called_once()

    def test_salt_client_execute_command_multiple_minions(self, salt_client):
        """Test executing Salt command on multiple minions."""
        salt_client.set_credentials("http://localhost:8000", "saltapi", "testpass")
        
        with patch.object(salt_client, '_make_request') as mock_request:
            mock_request.return_value = {
                "return": [
                    {"minions": ["minion1", "minion2", "minion3"], "success": True}
                ]
            }
            result = salt_client.execute_command("test.minion", "test.run", ["arg1"])
            
            assert result is True
            mock_request.assert_called_once()

    def test_salt_client_get_status_success(self, salt_client):
        """Test getting minion status successfully."""
        salt_client.set_credentials("http://localhost:8000", "saltapi", "testpass")
        
        with patch.object(salt_client, '_make_request') as mock_request:
            mock_request.return_value = {
                "return": [
                    {"minion1": True, "minion2": True}
                ]
            }
            status = salt_client.get_status(["minion1", "minion2"])
            
            assert len(status) == 2
            assert status["minion1"] is True
            assert status["minion2"] is True

    def test_salt_client_get_status_no_minions(self, salt_client):
        """Test getting status with no minions."""
        salt_client.set_credentials("http://localhost:8000", "saltapi", "testpass")
        
        with patch.object(salt_client, '_make_request') as mock_request:
            mock_request.return_value = {"return": [{}]}
            status = salt_client.get_status([])
            
            assert status == {}

    def test_salt_client_run_job_success(self, salt_client):
        """Test running a Salt job successfully."""
        salt_client.set_credentials("http://localhost:8000", "saltapi", "testpass")
        
        with patch.object(salt_client, '_make_request') as mock_request:
            mock_request.return_value = {
                "return": [{"jids": ["20250414123456789"]}]
            }
            job_id = salt_client.run_job("test.minion", "state.apply", ["test"])
            
            assert job_id is not None
            mock_request.assert_called_once()

    def test_salt_client_run_job_failure(self, salt_client):
        """Test running a Salt job when it fails."""
        salt_client.set_credentials("http://localhost:8000", "saltapi", "testpass")
        
        with patch.object(salt_client, '_make_request') as mock_request:
            mock_request.side_effect = Exception("Connection failed")
            job_id = salt_client.run_job("test.minion", "state.apply", ["test"])
            
            assert job_id is None

    def test_salt_client_check_job_status_success(self, salt_client):
        """Test checking job status successfully."""
        salt_client.set_credentials("http://localhost:8000", "saltapi", "testpass")
        
        with patch.object(salt_client, '_make_request') as mock_request:
            mock_request.return_value = {
                "return": [
                    {"jid": "20250414123456789", "result": True}
                ]
            }
            status = salt_client.check_job_status("20250414123456789")
            
            assert status is not None
            mock_request.assert_called_once()

    def test_salt_client_check_job_status_running(self, salt_client):
        """Test checking job status when still running."""
        salt_client.set_credentials("http://localhost:8000", "saltapi", "testpass")
        
        with patch.object(salt_client, '_make_request') as mock_request:
            mock_request.return_value = {
                "return": [
                    {"jid": "20250414123456789", "result": None}
                ]
            }
            status = salt_client.check_job_status("20250414123456789")
            
            assert status is not None

    def test_salt_client_list_keys_success(self, salt_client):
        """Test listing Salt keys successfully."""
        salt_client.set_credentials("http://localhost:8000", "saltapi", "testpass")
        
        with patch.object(salt_client, '_make_request') as mock_request:
            mock_request.return_value = {
                "return": {
                    "minions": {
                        "minion1": ["key1", "key2"],
                        "minion2": ["key3"]
                    }
                }
            }
            keys = salt_client.list_keys(["minion1", "minion2"])
            
            assert len(keys) == 3
            assert "key1" in keys
            assert "key2" in keys
            assert "key3" in keys

    def test_salt_client_health_check(self, salt_client):
        """Test Salt API health check."""
        salt_client.set_credentials("http://localhost:8000", "saltapi", "testpass")
        
        with patch.object(salt_client, '_make_request') as mock_request:
            mock_request.return_value = {"return": [{"local": True}]}
            health = salt_client.health_check()
            
            assert health is True
            mock_request.assert_called_once()

    def test_salt_client_health_check_failure(self, salt_client):
        """Test Salt API health check when it fails."""
        salt_client.set_credentials("http://localhost:8000", "saltapi", "testpass")
        
        with patch.object(salt_client, '_make_request') as mock_request:
            mock_request.side_effect = Exception("Salt API unavailable")
            health = salt_client.health_check()
            
            assert health is False

    def test_salt_client_empty_minion_list(self, salt_client):
        """Test handling of empty minion list."""
        salt_client.set_credentials("http://localhost:8000", "saltapi", "testpass")
        
        with patch.object(salt_client, '_make_request') as mock_request:
            mock_request.return_value = {"return": [{}]}
            status = salt_client.get_status([])
            
            assert status == {}

    def test_salt_client_command_with_special_args(self, salt_client):
        """Test executing commands with special arguments."""
        salt_client.set_credentials("http://localhost:8000", "saltapi", "testpass")
        
        with patch.object(salt_client, '_make_request') as mock_request:
            mock_request.return_value = {
                "return": [{"minions": ["minion1"], "success": True}]
            }
            result = salt_client.execute_command("test.minion", "test.run", ["arg;with;special", "chars"])
            
            assert result is True
            mock_request.assert_called_once()
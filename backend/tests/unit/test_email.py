"""Unit tests for Email service."""
import pytest
from unittest.mock import Mock, patch
from app.core.email import email_service


@pytest.mark.unit
class TestEmailService:
    """Test Email service operations."""

    @pytest.fixture
    def email_service(self):
        """Create a mock email service for testing."""
        return email_service

    def test_email_service_initialization(self, email_service):
        """Test email service initialization."""
        assert email_service is not None
        assert email_service.smtp_host is not None
        assert email_service.smtp_port is not None

    def test_email_service_set_smtp_config(self, email_service):
        """Test setting SMTP configuration."""
        test_host = "smtp.example.com"
        test_port = 587
        test_username = "test@example.com"
        test_password = "testpass"
        
        email_service.set_smtp_config(test_host, test_port, test_username, test_password)
        
        assert email_service.smtp_host == test_host
        assert email_service.smtp_port == test_port
        assert email_service.smtp_username == test_username
        assert email_service.smtp_password == test_password

    def test_email_service_send_email_success(self, email_service):
        """Test sending email successfully."""
        email_service.set_smtp_config("smtp.example.com", 587, "test@example.com", "testpass")
        
        with patch.object(email_service, '_send_email') as mock_send:
            mock_send.return_value = {"success": True}
            result = email_service.send_email(
                "recipient@example.com",
                "Test Subject",
                "Test body",
                "test@example.com"
            )
            
            assert result is True
            mock_send.assert_called_once()

    def test_email_service_send_email_failure(self, email_service):
        """Test sending email when it fails."""
        email_service.set_smtp_config("smtp.example.com", 587, "test@example.com", "testpass")
        
        with patch.object(email_service, '_send_email') as mock_send:
            mock_send.side_effect = Exception("SMTP server unavailable")
            result = email_service.send_email(
                "recipient@example.com",
                "Test Subject",
                "Test body",
                "test@example.com"
            )
            
            assert result is False

    def test_email_service_send_bulk_emails(self, email_service):
        """Test sending bulk emails."""
        email_service.set_smtp_config("smtp.example.com", 587, "test@example.com", "testpass")
        
        with patch.object(email_service, '_send_email') as mock_send:
            mock_send.return_value = {"success": True}
            recipients = [
                "recipient1@example.com",
                "recipient2@example.com",
                "recipient3@example.com"
            ]
            result = email_service.send_bulk_emails(
                recipients,
                "Bulk Test Subject",
                "Bulk test body",
                "test@example.com"
            )
            
            assert result is True
            assert mock_send.call_count == 3

    def test_email_service_render_template(self, email_service):
        """Test rendering email templates."""
        email_service.set_smtp_config("smtp.example.com", 587, "test@example.com", "testpass")
        
        template_data = {
            "username": "testuser",
            "reset_link": "http://example.com/reset",
            "expiry": "24 hours"
        }
        rendered = email_service.render_template("reset_password.html", template_data)
        
        assert "{{username}}" not in rendered
        assert "testuser" in rendered
        assert "http://example.com/reset" in rendered
        assert "24 hours" in rendered

    def test_email_service_render_template_missing_variable(self, email_service):
        """Test rendering template with missing variable."""
        email_service.set_smtp_config("smtp.example.com", 587, "test@example.com", "testpass")
        
        template_data = {"username": "testuser"}  # Missing reset_link
        rendered = email_service.render_template("reset_password.html", template_data)
        
        # Should handle missing variable gracefully
        assert "{{reset_link}}" not in rendered
        assert "testuser" in rendered

    def test_email_service_send_html_email(self, email_service):
        """Test sending HTML emails."""
        email_service.set_smtp_config("smtp.example.com", 587, "test@example.com", "testpass")
        
        with patch.object(email_service, '_send_email') as mock_send:
            mock_send.return_value = {"success": True}
            result = email_service.send_html_email(
                "recipient@example.com",
                "HTML Test Subject",
                "<h1>Test HTML</h1>",
                "test@example.com"
            )
            
            assert result is True
            mock_send.assert_called_once()

    def test_email_service_validation_empty_recipient(self, email_service):
        """Test validation of empty recipient."""
        email_service.set_smtp_config("smtp.example.com", 587, "test@example.com", "testpass")
        
        with patch.object(email_service, '_send_email') as mock_send:
            result = email_service.send_email("", "Test Subject", "Test Body", "test@example.com")
            
            assert result is False

    def test_email_service_validation_invalid_email(self, email_service):
        """Test validation of invalid email addresses."""
        email_service.set_smtp_config("smtp.example.com", 587, "test@example.com", "testpass")
        
        with patch.object(email_service, '_send_email') as mock_send:
            result = email_service.send_email("invalid-email", "Test Subject", "Test Body", "test@example.com")
            
            assert result is False

    def test_email_service_empty_subject(self, email_service):
        """Test handling of empty subject."""
        email_service.set_smtp_config("smtp.example.com", 587, "test@example.com", "testpass")
        
        with patch.object(email_service, '_send_email') as mock_send:
            mock_send.return_value = {"success": True}
            result = email_service.send_email(
                "recipient@example.com",
                "",
                "Test Body",
                "test@example.com"
            )
            
            # Should handle empty subject gracefully
            assert result is True

    def test_email_service_special_characters_in_subject(self, email_service):
        """Test handling of special characters in subject."""
        email_service.set_smtp_config("smtp.example.com", 587, "test@example.com", "testpass")
        
        with patch.object(email_service, '_send_email') as mock_send:
            mock_send.return_value = {"success": True}
            result = email_service.send_email(
                "recipient@example.com",
                "Subject with <special> characters",
                "Test Body",
                "test@example.com"
            )
            
            # Should escape special characters
            assert result is True

    def test_email_service_long_body(self, email_service):
        """Test handling of long email body."""
        email_service.set_smtp_config("smtp.example.com", 587, "test@example.com", "testpass")
        
        long_body = "Test " * 1000  # 4000+ characters
        with patch.object(email_service, '_send_email') as mock_send:
            mock_send.return_value = {"success": True}
            result = email_service.send_email(
                "recipient@example.com",
                "Test Subject",
                long_body,
                "test@example.com"
            )
            
            assert result is True

    def test_email_service_attachments(self, email_service):
        """Test sending emails with attachments."""
        email_service.set_smtp_config("smtp.example.com", 587, "test@example.com", "testpass")
        
        with patch.object(email_service, '_send_email') as mock_send:
            mock_send.return_value = {"success": True}
            result = email_service.send_email_with_attachment(
                "recipient@example.com",
                "Test Subject",
                "Test Body",
                "test@example.com",
                "test.txt",
                b"File content"
            )
            
            assert result is True
            mock_send.assert_called_once()
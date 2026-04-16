"""Email notification service for OpsPilot."""
import logging
from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from jinja2 import Template

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending notifications."""

    def __init__(self):
        """Initialize email service."""
        self.smtp_host = settings.email_smtp_host
        self.smtp_port = settings.email_smtp_port
        self.smtp_username = settings.email_smtp_username
        self.smtp_password = settings.email_smtp_password
        self.smtp_from = settings.email_smtp_from or settings.email_smtp_username
        self.smtp_use_tls = settings.email_smtp_use_tls

    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send email.

        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            html_content: HTML content
            text_content: Plain text content (fallback)

        Returns:
            True if successful, False otherwise
        """
        if not self.smtp_host:
            logger.warning("SMTP not configured, skipping email send")
            return False

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.smtp_from
            msg["To"] = ", ".join(to_emails)

            # Add HTML content
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            # Add plain text content if provided
            if text_content:
                msg.attach(MIMEText(text_content, "plain", "utf-8"))

            # Connect to SMTP server and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()

                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)

                server.send_message(msg)

            logger.info(f"Email sent to {len(to_emails)} recipients: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_alert_notification(
        self,
        to_emails: List[str],
        alert_data: dict
    ) -> bool:
        """Send alert notification email.

        Args:
            to_emails: List of recipient email addresses
            alert_data: Alert data dictionary

        Returns:
            True if successful, False otherwise
        """
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #f44336; color: white; padding: 20px; border-radius: 5px 5px 0 0; }
                .content { background: #f9f9f9; padding: 20px; border-radius: 0 0 5px 5px; }
                .alert-details { background: white; padding: 15px; margin: 15px 0; border-left: 4px solid #f44336; }
                .label { font-weight: bold; color: #666; }
                .value { color: #333; }
                .severity-critical { color: #d32f2f; font-weight: bold; }
                .severity-warning { color: #f57c00; font-weight: bold; }
                .severity-info { color: #1976d2; font-weight: bold; }
                .button { display: inline-block; padding: 10px 20px; background: #1976d2; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px; }
                .footer { text-align: center; color: #666; font-size: 12px; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚨 OpsPilot Alert</h1>
                </div>
                <div class="content">
                    <p>An alert has been triggered on your OpsPilot system.</p>

                    <div class="alert-details">
                        <p><span class="label">Server:</span> <span class="value">{{ server_hostname }}</span></p>
                        <p><span class="label">Alert Type:</span> <span class="value">{{ alert_type }}</span></p>
                        <p><span class="label">Severity:</span> <span class="value severity-{{ severity }}">{{ severity|upper }}</span></p>
                        <p><span class="label">Message:</span> <span class="value">{{ message }}</span></p>
                        {% if threshold %}
                        <p><span class="label">Threshold:</span> <span class="value">{{ threshold }}</span></p>
                        {% endif %}
                        {% if actual_value %}
                        <p><span class="label">Actual Value:</span> <span class="value">{{ actual_value }}</span></p>
                        {% endif %}
                        <p><span class="label">Triggered At:</span> <span class="value">{{ triggered_at }}</span></p>
                    </div>

                    <p>Please investigate and resolve this alert as soon as possible.</p>

                    <a href="{{ dashboard_url }}" class="button">View in Dashboard</a>

                    <div class="footer">
                        <p>This is an automated notification from OpsPilot.</p>
                        <p>To manage your notification preferences, visit your account settings.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """)

        html_content = template.render(
            server_hostname=alert_data.get("server_hostname", "Unknown"),
            alert_type=alert_data.get("type", "Unknown"),
            severity=alert_data.get("severity", "info"),
            message=alert_data.get("message", ""),
            threshold=alert_data.get("threshold"),
            actual_value=alert_data.get("actual_value"),
            triggered_at=alert_data.get("triggered_at", ""),
            dashboard_url=f"{settings.app_url}/alerts/{alert_data.get('id', '')}"
        )

        text_content = f"""
OpsPilot Alert

Server: {alert_data.get("server_hostname", "Unknown")}
Alert Type: {alert_data.get("type", "Unknown")}
Severity: {alert_data.get("severity", "info").upper()}
Message: {alert_data.get("message", "")}
Triggered At: {alert_data.get("triggered_at", "")}

Please investigate and resolve this alert as soon as possible.

View in Dashboard: {settings.app_url}/alerts/{alert_data.get('id', '')}

This is an automated notification from OpsPilot.
        """

        subject = f"[ALERT] {alert_data.get('severity', 'INFO').upper()} - {alert_data.get('server_hostname', 'Unknown')} - {alert_data.get('type', 'Unknown')}"

        return self.send_email(to_emails, subject, html_content, text_content)

    def send_backup_notification(
        self,
        to_emails: List[str],
        backup_data: dict
    ) -> bool:
        """Send backup notification email.

        Args:
            to_emails: List of recipient email addresses
            backup_data: Backup data dictionary

        Returns:
            True if successful, False otherwise
        """
        status_color = "green" if backup_data.get("status") == "completed" else "red"
        status_text = "✅ Success" if backup_data.get("status") == "completed" else "❌ Failed"

        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: {{ status_color }}; color: white; padding: 20px; border-radius: 5px 5px 0 0; }
                .content { background: #f9f9f9; padding: 20px; border-radius: 0 0 5px 5px; }
                .backup-details { background: white; padding: 15px; margin: 15px 0; border-left: 4px solid {{ status_color }}; }
                .label { font-weight: bold; color: #666; }
                .value { color: #333; }
                .footer { text-align: center; color: #666; font-size: 12px; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>💾 Backup {{ status_text }}</h1>
                </div>
                <div class="content">
                    <p>A backup operation has {{ 'completed successfully' if status == 'completed' else 'failed' }}.</p>

                    <div class="backup-details">
                        <p><span class="label">Server:</span> <span class="value">{{ server_hostname }}</span></p>
                        <p><span class="label">Backup Type:</span> <span class="value">{{ backup_type }}</span></p>
                        <p><span class="label">Status:</span> <span class="value">{{ status_text }}</span></p>
                        {% if duration %}
                        <p><span class="label">Duration:</span> <span class="value">{{ duration }}</span></p>
                        {% endif %}
                        {% if size %}
                        <p><span class="label">Size:</span> <span class="value">{{ size }}</span></p>
                        {% endif %}
                        {% if error %}
                        <p><span class="label">Error:</span> <span class="value" style="color: red;">{{ error }}</span></p>
                        {% endif %}
                        <p><span class="label">Started At:</span> <span class="value">{{ started_at }}</span></p>
                    </div>

                    {% if status == 'failed' %}
                    <p>Please investigate the backup failure and retry if necessary.</p>
                    {% endif %}

                    <div class="footer">
                        <p>This is an automated notification from OpsPilot.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """)

        html_content = template.render(
            status=backup_data.get("status", "unknown"),
            status_text=status_text,
            status_color=status_color,
            server_hostname=backup_data.get("server_hostname", "Unknown"),
            backup_type=backup_data.get("type", "Unknown"),
            duration=backup_data.get("duration"),
            size=backup_data.get("size"),
            error=backup_data.get("error"),
            started_at=backup_data.get("started_at", "")
        )

        subject = f"[BACKUP] {status_text} - {backup_data.get('server_hostname', 'Unknown')} - {backup_data.get('type', 'Unknown')}"

        return self.send_email(to_emails, subject, html_content)

    def send_deployment_notification(
        self,
        to_emails: List[str],
        deployment_data: dict
    ) -> bool:
        """Send deployment notification email.

        Args:
            to_emails: List of recipient email addresses
            deployment_data: Deployment data dictionary

        Returns:
            True if successful, False otherwise
        """
        status_color = "green" if deployment_data.get("status") == "completed" else "orange"
        status_text = "✅ Success" if deployment_data.get("status") == "completed" else "⏳ In Progress"

        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: {{ status_color }}; color: white; padding: 20px; border-radius: 5px 5px 0 0; }
                .content { background: #f9f9f9; padding: 20px; border-radius: 0 0 5px 5px; }
                .deployment-details { background: white; padding: 15px; margin: 15px 0; border-left: 4px solid {{ status_color }}; }
                .label { font-weight: bold; color: #666; }
                .value { color: #333; }
                .footer { text-align: center; color: #666; font-size: 12px; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Deployment {{ status_text }}</h1>
                </div>
                <div class="content">
                    <p>A deployment has {{ 'completed successfully' if status == 'completed' else 'started' }}.</p>

                    <div class="deployment-details">
                        <p><span class="label">Application:</span> <span class="value">{{ app_name }}</span></p>
                        <p><span class="label">Version:</span> <span class="value">{{ version }}</span></p>
                        <p><span class="label">Environment:</span> <span class="value">{{ environment }}</span></p>
                        <p><span class="label">Status:</span> <span class="value">{{ status_text }}</span></p>
                        {% if duration %}
                        <p><span class="label">Duration:</span> <span class="value">{{ duration }}</span></p>
                        {% endif %}
                        {% if servers %}
                        <p><span class="label">Servers:</span> <span class="value">{{ servers }}</span></p>
                        {% endif %}
                        <p><span class="label">Started At:</span> <span class="value">{{ started_at }}</span></p>
                    </div>

                    <div class="footer">
                        <p>This is an automated notification from OpsPilot.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """)

        html_content = template.render(
            status=deployment_data.get("status", "unknown"),
            status_text=status_text,
            status_color=status_color,
            app_name=deployment_data.get("app_name", "Unknown"),
            version=deployment_data.get("version", "Unknown"),
            environment=deployment_data.get("environment", "Unknown"),
            duration=deployment_data.get("duration"),
            servers=deployment_data.get("servers"),
            started_at=deployment_data.get("started_at", "")
        )

        subject = f"[DEPLOYMENT] {status_text} - {deployment_data.get('app_name', 'Unknown')} - {deployment_data.get('version', 'Unknown')}"

        return self.send_email(to_emails, subject, html_content)

    def send_password_reset_email(
        self,
        to_email: str,
        user_name: str,
        reset_url: str
    ) -> bool:
        """Send password reset email.

        Args:
            to_email: Recipient email address
            user_name: User's full name
            reset_url: Password reset URL with token

        Returns:
            True if successful, False otherwise
        """
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #1976d2; color: white; padding: 20px; border-radius: 5px 5px 0 0; text-align: center; }
                .content { background: #f9f9f9; padding: 20px; border-radius: 0 0 5px 5px; }
                .info-box { background: white; padding: 15px; margin: 15px 0; border-left: 4px solid #ff9800; }
                .button { display: inline-block; padding: 12px 24px; background: #1976d2; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; font-weight: bold; }
                .button:hover { background: #1565c0; }
                .security-note { background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107; }
                .footer { text-align: center; color: #666; font-size: 12px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Password Reset Request</h1>
                </div>
                <div class="content">
                    <p>Hi <strong>{{ user_name }}</strong>,</p>

                    <p>We received a request to reset your password for your OpsPilot account.</p>

                    <div class="info-box">
                        <p>If you didn't request this password reset, you can safely ignore this email.</p>
                    </div>

                    <p>To reset your password, click the button below:</p>

                    <div style="text-align: center;">
                        <a href="{{ reset_url }}" class="button">Reset My Password</a>
                    </div>

                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #1976d2;">{{ reset_url }}</p>

                    <div class="security-note">
                        <p><strong>⚠️ Security Notice:</strong></p>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            <li>This link will expire in 15 minutes</li>
                            <li>The link can only be used once</li>
                            <li>Never share this link with anyone</li>
                            <li>OpsPilot will never ask for your password</li>
                        </ul>
                    </div>

                    <p>If you have any questions or concerns, please contact our support team.</p>

                    <div class="footer">
                        <p>This is an automated email from OpsPilot.</p>
                        <p>© 2024 OpsPilot. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """)

        html_content = template.render(
            user_name=user_name,
            reset_url=reset_url
        )

        text_content = f"""
Password Reset Request

Hi {user_name},

We received a request to reset your password for your OpsPilot account.

If you didn't request this password reset, you can safely ignore this email.

To reset your password, visit the following link:
{reset_url}

Security Notice:
- This link will expire in 15 minutes
- The link can only be used once
- Never share this link with anyone
- OpsPilot will never ask for your password

If you have any questions or concerns, please contact our support team.

This is an automated email from OpsPilot.
© 2024 OpsPilot. All rights reserved.
        """

        subject = "[OpsPilot] Reset Your Password"

        return self.send_email([to_email], subject, html_content, text_content)


# Global email service instance
email_service = EmailService()

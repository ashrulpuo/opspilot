"""E2E tests for OpsPilot critical user flows using Playwright."""
import pytest
from playwright.sync_api import Page, expect
import time


class TestAuthenticationFlow:
    """Test authentication flow: login, logout, forgot password."""
    
    def test_user_login_success(self, page: Page, base_url: str):
        """Test successful user login."""
        page.goto(f"{base_url}/login")
        
        # Fill login form
        page.fill('input[type="email"]', "test@example.com")
        page.fill('input[type="password"]', "password123")
        
        # Click login button
        page.click('button[type="submit"]')
        
        # Wait for redirect to dashboard
        page.wait_for_url(f"{base_url}/dashboard")
        
        # Verify user is logged in
        expect(page.locator("text=Dashboard")).to_be_visible()
        expect(page.locator("text=test@example.com")).to_be_visible()
    
    def test_user_login_invalid_credentials(self, page: Page, base_url: str):
        """Test login with invalid credentials."""
        page.goto(f"{base_url}/login")
        
        # Fill login form with invalid credentials
        page.fill('input[type="email"]', "wrong@example.com")
        page.fill('input[type="password"]', "wrongpassword")
        
        # Click login button
        page.click('button[type="submit"]')
        
        # Verify error message
        expect(page.locator("text=Invalid email or password")).to_be_visible()
        # Should not redirect
        expect(page).to_have_url(f"{base_url}/login")
    
    def test_user_logout(self, page: Page, base_url: str):
        """Test user logout."""
        # First login
        page.goto(f"{base_url}/login")
        page.fill('input[type="email"]', "test@example.com")
        page.fill('input[type="password"]', "password123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{base_url}/dashboard")
        
        # Click logout
        page.click('button:has-text("Logout")')
        
        # Wait for redirect to login
        page.wait_for_url(f"{base_url}/login")
        
        # Verify logged out
        expect(page.locator("text=Login")).to_be_visible()
    
    def test_forgot_password_flow(self, page: Page, base_url: str):
        """Test forgot password flow."""
        page.goto(f"{base_url}/login")
        
        # Click forgot password
        page.click('a:has-text("Forgot password?")')
        
        # Verify forgot password page
        page.wait_for_url(f"{base_url}/forgot-password")
        expect(page.locator("text=Reset Your Password")).to_be_visible()
        
        # Fill email
        page.fill('input[type="email"]', "test@example.com")
        
        # Submit
        page.click('button:has-text("Send Reset Link")')
        
        # Verify success message
        expect(page.locator("text=reset link has been sent")).to_be_visible()
    
    def test_reset_password_with_token(self, page: Page, base_url: str):
        """Test reset password with token."""
        # Navigate to reset password page with token
        token = "test-token-1234567890abcdef"
        page.goto(f"{base_url}/reset-password?token={token}")
        
        # Verify reset password page
        expect(page.locator("text=Enter New Password")).to_be_visible()
        
        # Fill new password
        page.fill('input[name="new_password"]', "newpassword123")
        page.fill('input[name="confirm_password"]', "newpassword123")
        
        # Submit
        page.click('button:has-text("Reset Password")')
        
        # Verify success message
        expect(page.locator("text=Password reset successfully")).to_be_visible()
        
        # Redirect to login
        page.wait_for_url(f"{base_url}/login")


class TestServerManagement:
    """Test server management: add, edit, delete servers."""
    
    def test_add_server(self, page: Page, base_url: str):
        """Test adding a new server."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to servers page
        page.click('a:has-text("Servers")')
        page.wait_for_url(f"{base_url}/servers")
        
        # Click add server button
        page.click('button:has-text("Add Server")')
        
        # Wait for modal
        expect(page.locator(".modal")).to_be_visible()
        
        # Fill server details
        page.fill('input[name="hostname"]', "test-server-1")
        page.fill('input[name="ip_address"]', "192.168.1.100")
        page.select_option('select[name="server_type"]', "web")
        page.fill('textarea[name="description"]', "Test web server")
        
        # Submit
        page.click('button:has-text("Save")')
        
        # Verify server added
        expect(page.locator("text=test-server-1")).to_be_visible()
        expect(page.locator("text=192.168.1.100")).to_be_visible()
    
    def test_edit_server(self, page: Page, base_url: str):
        """Test editing an existing server."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to servers page
        page.goto(f"{base_url}/servers")
        
        # Click edit button on first server
        page.click('button:has-text("Edit")').first
        
        # Wait for modal
        expect(page.locator(".modal")).to_be_visible()
        
        # Edit server details
        page.fill('input[name="description"]', "Updated description")
        
        # Submit
        page.click('button:has-text("Save")')
        
        # Verify server updated
        expect(page.locator("text=Updated description")).to_be_visible()
    
    def test_delete_server(self, page: Page, base_url: str):
        """Test deleting a server."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to servers page
        page.goto(f"{base_url}/servers")
        
        # Click delete button
        page.click('button:has-text("Delete")').first
        
        # Wait for confirmation dialog
        expect(page.locator(".confirm-dialog")).to_be_visible()
        
        # Confirm deletion
        page.click('button:has-text("Yes, Delete")')
        
        # Verify success message
        expect(page.locator("text=Server deleted successfully")).to_be_visible()
    
    def test_server_list_pagination(self, page: Page, base_url: str):
        """Test server list pagination."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to servers page
        page.goto(f"{base_url}/servers")
        
        # Verify pagination controls
        expect(page.locator(".pagination")).to_be_visible()
        
        # Click next page
        page.click('.pagination button:has-text("Next")')
        
        # Wait for page load
        page.wait_for_load_state("networkidle")
        
        # Verify page changed
        expect(page.locator(".pagination .active")).not_to_have_text("1")


class TestMonitoringDashboard:
    """Test monitoring dashboard: metrics, alerts, charts."""
    
    def test_dashboard_metrics_display(self, page: Page, base_url: str):
        """Test dashboard displays metrics correctly."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to dashboard
        page.goto(f"{base_url}/dashboard")
        
        # Wait for dashboard to load
        page.wait_for_load_state("networkidle")
        
        # Verify metrics cards
        expect(page.locator(".metric-card")).to_have_count(4)  # CPU, RAM, Disk, Network
        
        # Verify metrics data
        expect(page.locator("text=CPU Usage")).to_be_visible()
        expect(page.locator("text=Memory Usage")).to_be_visible()
        expect(page.locator("text=Disk Usage")).to_be_visible()
    
    def test_dashboard_charts_render(self, page: Page, base_url: str):
        """Test dashboard charts render correctly."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to dashboard
        page.goto(f"{base_url}/dashboard")
        
        # Wait for charts to render
        page.wait_for_selector('.chart canvas')
        
        # Verify charts
        expect(page.locator('.chart')).to_have_count(3)  # CPU, RAM, Disk charts
    
    def test_dashboard_alerts_display(self, page: Page, base_url: str):
        """Test dashboard displays alerts."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to dashboard
        page.goto(f"{base_url}/dashboard")
        
        # Wait for alerts section
        page.wait_for_selector('.alerts-section')
        
        # Verify alerts
        expect(page.locator('.alert-item')).to_be_visible()
    
    def test_dashboard_server_filter(self, page: Page, base_url: str):
        """Test dashboard server filter."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to dashboard
        page.goto(f"{base_url}/dashboard")
        
        # Select server from dropdown
        page.select_option('select[name="server"]', "server-1")
        
        # Wait for filter to apply
        page.wait_for_load_state("networkidle")
        
        # Verify filter applied
        expect(page.locator('.dashboard-content')).to_be_visible()


class TestBackupAutomation:
    """Test backup automation: create, schedule, execute backups."""
    
    def test_create_backup_schedule(self, page: Page, base_url: str):
        """Test creating a backup schedule."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to backups page
        page.click('a:has-text("Backups")')
        page.wait_for_url(f"{base_url}/backups")
        
        # Click add schedule
        page.click('button:has-text("Add Schedule")')
        
        # Wait for modal
        expect(page.locator(".modal")).to_be_visible()
        
        # Fill backup schedule details
        page.select_option('select[name="server_id"]', "server-1")
        page.select_option('select[name="backup_type"]', "full")
        page.fill('input[name="schedule"]', "0 2 * * *")  # Daily at 2 AM
        page.fill('input[name="retention_days"]', "30")
        
        # Submit
        page.click('button:has-text("Save")')
        
        # Verify schedule created
        expect(page.locator("text=Daily at 2 AM")).to_be_visible()
    
    def test_execute_backup_now(self, page: Page, base_url: str):
        """Test executing backup immediately."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to backups page
        page.goto(f"{base_url}/backups")
        
        # Click backup now button
        page.click('button:has-text("Backup Now")').first
        
        # Wait for backup to start
        page.wait_for_selector('.backup-status:has-text("In Progress")')
        
        # Verify backup status
        expect(page.locator('.backup-status')).to_contain_text("In Progress")
    
    def test_view_backup_reports(self, page: Page, base_url: str):
        """Test viewing backup reports."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to backups page
        page.goto(f"{base_url}/backups")
        
        # Click view reports
        page.click('a:has-text("Reports")')
        
        # Wait for reports page
        page.wait_for_url(f"{base_url}/backups/reports")
        
        # Verify reports
        expect(page.locator('.backup-report')).to_be_visible()
    
    def test_edit_backup_schedule(self, page: Page, base_url: str):
        """Test editing a backup schedule."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to backups page
        page.goto(f"{base_url}/backups")
        
        # Click edit schedule
        page.click('button:has-text("Edit Schedule")').first
        
        # Wait for modal
        expect(page.locator(".modal")).to_be_visible()
        
        # Edit schedule
        page.fill('input[name="retention_days"]', "60")
        
        # Submit
        page.click('button:has-text("Save")')
        
        # Verify schedule updated
        expect(page.locator("text=60 days")).to_be_visible()


class TestSSHAccess:
    """Test SSH access: web-based terminal."""
    
    def test_ssh_connect_to_server(self, page: Page, base_url: str):
        """Test connecting to server via SSH."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to servers page
        page.goto(f"{base_url}/servers")
        
        # Click SSH button
        page.click('button:has-text("SSH")').first
        
        # Wait for terminal to open
        page.wait_for_selector('.terminal-container')
        
        # Verify terminal is active
        expect(page.locator('.terminal')).to_be_visible()
    
    def test_ssh_send_command(self, page: Page, base_url: str):
        """Test sending command via SSH terminal."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to SSH terminal
        page.goto(f"{base_url}/servers/server-1/ssh")
        
        # Wait for terminal
        page.wait_for_selector('.terminal-container')
        
        # Type command
        page.locator('.terminal-input').fill("ls -la")
        
        # Send command
        page.keyboard.press("Enter")
        
        # Wait for output
        page.wait_for_timeout(1000)
        
        # Verify command executed
        expect(page.locator('.terminal-output')).to_contain_text("total")
    
    def test_ssh_disconnect(self, page: Page, base_url: str):
        """Test disconnecting SSH session."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to SSH terminal
        page.goto(f"{base_url}/servers/server-1/ssh")
        
        # Wait for terminal
        page.wait_for_selector('.terminal-container')
        
        # Click disconnect
        page.click('button:has-text("Disconnect")')
        
        # Verify disconnected
        expect(page.locator("text=Session disconnected")).to_be_visible()


class TestAlertingSystem:
    """Test alerting system: create, view, dismiss alerts."""
    
    def test_create_alert(self, page: Page, base_url: str):
        """Test creating an alert rule."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to alerts page
        page.click('a:has-text("Alerts")')
        page.wait_for_url(f"{base_url}/alerts")
        
        # Click add alert
        page.click('button:has-text("Add Alert")')
        
        # Wait for modal
        expect(page.locator(".modal")).to_be_visible()
        
        # Fill alert details
        page.select_option('select[name="server_id"]', "server-1")
        page.select_option('select[name="metric_type"]', "cpu")
        page.fill('input[name="threshold"]', "90")
        page.select_option('select[name="severity"]', "critical")
        
        # Submit
        page.click('button:has-text("Save")')
        
        # Verify alert created
        expect(page.locator("text=CPU > 90%")).to_be_visible()
    
    def test_view_alert_history(self, page: Page, base_url: str):
        """Test viewing alert history."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to alerts page
        page.goto(f"{base_url}/alerts")
        
        # Click history tab
        page.click('button:has-text("History")')
        
        # Verify alert history
        expect(page.locator('.alert-history-item')).to_be_visible()
    
    def test_dismiss_alert(self, page: Page, base_url: str):
        """Test dismissing an alert."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to alerts page
        page.goto(f"{base_url}/alerts")
        
        # Click dismiss button
        page.click('button:has-text("Dismiss")').first
        
        # Verify alert dismissed
        expect(page.locator('.alert-item.dismissed')).to_be_visible()
    
    def test_edit_alert_threshold(self, page: Page, base_url: str):
        """Test editing alert threshold."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to alerts page
        page.goto(f"{base_url}/alerts")
        
        # Click edit alert
        page.click('button:has-text("Edit")').first
        
        # Wait for modal
        expect(page.locator(".modal")).to_be_visible()
        
        # Edit threshold
        page.fill('input[name="threshold"]', "85")
        
        # Submit
        page.click('button:has-text("Save")')
        
        # Verify threshold updated
        expect(page.locator("text=CPU > 85%")).to_be_visible()


class TestCredentialManagement:
    """Test credential management: create, encrypt, view credentials."""
    
    def test_create_credential_with_encryption(self, page: Page, base_url: str):
        """Test creating encrypted credential."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Setup master password (first time)
        page.goto(f"{base_url}/credentials")
        expect(page.locator("text=Set Master Password")).to_be_visible()
        
        page.fill('input[name="master_password"]', "test-master-password")
        page.click('button:has-text("Set Password")')
        
        # Wait for modal to close
        page.wait_for_selector('.modal', state='hidden')
        
        # Navigate to credentials page
        page.goto(f"{base_url}/credentials")
        
        # Click add credential
        page.click('button:has-text("Add Credential")')
        
        # Wait for modal
        expect(page.locator(".modal")).to_be_visible()
        
        # Fill credential details
        page.fill('input[name="name"]', "Database Credentials")
        page.fill('input[name="username"]', "db-admin")
        page.fill('input[name="password"]', "supersecret123")
        page.fill('input[name="description"]', "Production database")
        
        # Submit
        page.click('button:has-text("Save")')
        
        # Verify credential created
        expect(page.locator("text=Database Credentials")).to_be_visible()
    
    def test_view_decrypted_credential(self, page: Page, base_url: str):
        """Test viewing decrypted credential."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to credentials page
        page.goto(f"{base_url}/credentials")
        
        # Click view credential
        page.click('button:has-text("View")').first
        
        # Wait for modal
        expect(page.locator(".modal")).to_be_visible()
        
        # Verify credential decrypted
        expect(page.locator("text=db-admin")).to_be_visible()
    
    def test_edit_credential(self, page: Page, base_url: str):
        """Test editing a credential."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to credentials page
        page.goto(f"{base_url}/credentials")
        
        # Click edit credential
        page.click('button:has-text("Edit")').first
        
        # Wait for modal
        expect(page.locator(".modal")).to_be_visible()
        
        # Edit description
        page.fill('input[name="description"]', "Updated description")
        
        # Submit
        page.click('button:has-text("Save")')
        
        # Verify credential updated
        expect(page.locator("text=Updated description")).to_be_visible()
    
    def test_delete_credential(self, page: Page, base_url: str):
        """Test deleting a credential."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to credentials page
        page.goto(f"{base_url}/credentials")
        
        # Click delete credential
        page.click('button:has-text("Delete")').first
        
        # Wait for confirmation
        expect(page.locator(".confirm-dialog")).to_be_visible()
        
        # Confirm deletion
        page.click('button:has-text("Yes, Delete")')
        
        # Verify credential deleted
        expect(page.locator("text=Credential deleted successfully")).to_be_visible()


class TestDeploymentAutomation:
    """Test deployment automation: create, execute, monitor deployments."""
    
    def test_create_deployment(self, page: Page, base_url: str):
        """Test creating a deployment."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to deployments page
        page.click('a:has-text("Deployments")')
        page.wait_for_url(f"{base_url}/deployments")
        
        # Click add deployment
        page.click('button:has-text("New Deployment")')
        
        # Wait for modal
        expect(page.locator(".modal")).to_be_visible()
        
        # Fill deployment details
        page.fill('input[name="name"]', "Production Release")
        page.select_option('select[name="server_id"]', "server-1")
        page.fill('input[name="branch"]', "main")
        page.select_option('select[name="strategy"]', "rolling")
        
        # Submit
        page.click('button:has-text("Create")')
        
        # Verify deployment created
        expect(page.locator("text=Production Release")).to_be_visible()
    
    def test_execute_deployment(self, page: Page, base_url: str):
        """Test executing a deployment."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to deployments page
        page.goto(f"{base_url}/deployments")
        
        # Click deploy button
        page.click('button:has-text("Deploy")').first
        
        # Wait for deployment to start
        page.wait_for_selector('.deployment-status:has-text("In Progress")')
        
        # Verify deployment status
        expect(page.locator('.deployment-status')).to_contain_text("In Progress")
    
    def test_view_deployment_logs(self, page: Page, base_url: str):
        """Test viewing deployment logs."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to deployments page
        page.goto(f"{base_url}/deployments")
        
        # Click view logs
        page.click('button:has-text("Logs")').first
        
        # Wait for logs modal
        expect(page.locator(".logs-modal")).to_be_visible()
        
        # Verify logs
        expect(page.locator('.log-line')).to_be_visible()
    
    def test_deployment_status_monitoring(self, page: Page, base_url: str):
        """Test deployment status monitoring."""
        # Login first
        self.test_user_login_success(page, base_url)
        
        # Navigate to deployments page
        page.goto(f"{base_url}/deployments")
        
        # Verify status indicators
        expect(page.locator('.status-badge')).to_be_visible()
        
        # Check different statuses
        expect(page.locator('.status-badge.success')).to_be_visible()
        expect(page.locator('.status-badge.error')).to_be_visible()


# Pytest fixtures
@pytest.fixture
def base_url():
    """Base URL for E2E tests."""
    return "http://localhost:5173"  # Frontend dev server


@pytest.fixture
def page(browser_type_launch_args, browser_type):
    """Create a new page for each test."""
    context = browser_type.launch(**browser_type_launch_args)
    page = context.new_page()
    yield page
    context.close()

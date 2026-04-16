# OpsPilot Development Pillar
# Development environment specific configurations

opspilot:
  # API Configuration
  api_url: http://localhost:9000/api/v1
  api_key: "dev-api-key-for-testing"
  organization_id: "dev-org-id"
  
  # Server settings
  servers:
    default_os: ubuntu
    allowed_os_types:
      - ubuntu
      - debian
      - macos
    
  # Monitoring configuration
  monitoring:
    enabled: true
    metrics_interval: 30  # More frequent in dev
    cpu_threshold: 90
    memory_threshold: 90
    disk_threshold: 85
    network_threshold: 80
  
  # Backup configuration
  backup:
    enabled: true
    backup_schedule: "0 */2 * * *"  # Every 2 hours in dev
    retention_days: 7  # Shorter retention in dev
    compression_enabled: false  # Disable compression in dev for speed
    encryption_enabled: false  # Disable encryption in dev
  
  # Security settings
  security:
    password_policy:
      min_length: 6  # Weaker in dev for testing
      require_special_char: false
      require_number: false
      require_uppercase: false
      require_lowercase: false
      rotation_days: 7
    ssh_policy:
      require_key_auth: false  # Allow password auth in dev
      max_concurrent_sessions: 10  # Higher limit in dev
      session_timeout_minutes: 120  # Longer sessions in dev
    fail2ban_enabled: false  # Disable fail2ban in dev
    max_login_attempts: 100
    ban_duration_minutes: 1
  
  # Logging configuration
  logging:
    enabled: true
    level: DEBUG  # Debug logging in dev
    max_size: 500M  # Larger logs in dev
    retention_days: 3  # Shorter retention in dev
    ship_to_backend: true
    endpoint: http://localhost:9000/api/v1/logs
  
  # Alerting configuration
  alerts:
    enabled: true
    email_notifications: false  # No email in dev
    slack_webhook: ""  # No Slack in dev
    cpu_threshold: 95  # Higher thresholds in dev
    memory_threshold: 95
    disk_threshold: 90
    smtp_host: localhost
    smtp_from: dev@opspilot.local
    smtp_user: dev
    smtp_password: dev

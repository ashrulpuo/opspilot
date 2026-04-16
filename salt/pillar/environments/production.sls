# OpsPilot Production Pillar
# Production environment specific configurations

opspilot:
  # API Configuration
  api_url: https://api.opspilot.example.com/api/v1
  api_key: "CHANGE_ME_IN_PRODUCTION"
  organization_id: "CHANGE_ME_IN_PRODUCTION"
  
  # Server settings
  servers:
    default_os: ubuntu
    allowed_os_types:
      - ubuntu
      - debian
      - centos
      - rhel
    
  # Monitoring configuration
  monitoring:
    enabled: true
    metrics_interval: 60
    cpu_threshold: 90
    memory_threshold: 90
    disk_threshold: 85
    network_threshold: 80
  
  # Backup configuration
  backup:
    enabled: true
    backup_schedule: "0 */6 * * *"  # Every 6 hours
    retention_days: 90
    compression_enabled: true
    encryption_enabled: true
  
  # Security settings
  security:
    password_policy:
      min_length: 8
      require_special_char: true
      require_number: true
      require_uppercase: true
      require_lowercase: true
      rotation_days: 90
    ssh_policy:
      require_key_auth: true
      max_concurrent_sessions: 3
      session_timeout_minutes: 30
    fail2ban_enabled: true
    max_login_attempts: 5
    ban_duration_minutes: 30
  
  # Logging configuration
  logging:
    enabled: true
    level: INFO
    max_size: 100M
    retention_days: 30
    ship_to_backend: true
    endpoint: https://api.opspilot.example.com/api/v1/logs
  
  # Alerting configuration
  alerts:
    enabled: true
    email_notifications: true
    slack_webhook: "https://hooks.slack.com/services/CHANGE_ME"
    cpu_threshold: 90
    memory_threshold: 90
    disk_threshold: 85
    smtp_host: smtp.example.com
    smtp_from: alerts@opspilot.example.com
    smtp_user: alerts@opspilot.example.com
    smtp_password: "CHANGE_ME"

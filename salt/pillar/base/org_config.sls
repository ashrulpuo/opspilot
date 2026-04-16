# OpsPilot Organization Configuration Pillar
# Organization-specific settings and policies

default:
  organization:
    id: default-org-id
    name: Default Organization
    slug: default
    
  # Default server settings
  servers:
    default_os: ubuntu
    allowed_os_types:
      - ubuntu
      - debian
      - centos
      - rhel
      - fedora
    default_web_server: nginx
    allowed_web_servers:
      - nginx
      - apache
      - caddy
      - iis
    
  # Monitoring defaults
  monitoring:
    default_thresholds:
      cpu: 90
      memory: 90
      disk: 85
      network: 80
    alert_levels:
      warning: 70
      critical: 90
      
  # Backup policies
  backup:
    default_retention_days: 90
    backup_intervals:
      - 0 */6 * * *    # Every 6 hours
      - 0 0 * * *      # Daily at midnight
      - 0 0 0 * *      # Weekly
    compression_enabled: true
    encryption_enabled: true
    
  # Security policies
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
      
  # Resource limits
  resources:
    max_servers_per_org: 1000
    max_backups_per_day: 10
    max_alerts_per_day: 1000
    metrics_retention_days: 90

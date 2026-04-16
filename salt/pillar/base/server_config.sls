# OpsPilot Server Configuration Pillar
# Server-specific configuration data

opspilot:
  api_url: http://localhost:9000/api/v1
  api_key: "{{ salt['pillar'].get('opspilot:auth:api_key', 'change-me') }}"
  organization_id: "{{ salt['pillar'].get('opspilot:organization:id', 'default-org-id') }}"
  
  # Server metadata
  hostname: {{ grains['fqdn'] }}
  ip_address: {{ grains['ip4_interfaces']['eth0'] }}
  os_type: {{ grains['os'] }}
  os_family: {{ grains['os_family'] }}
  os_release: {{ grains['osrelease'] }}
  
  # Monitoring configuration
  monitoring:
    enabled: true
    metrics_interval: 60
    cpu_threshold: 90
    memory_threshold: 90
    disk_threshold: 85
  
  # Backup configuration
  backup:
    enabled: true
    backup_schedule: "0 */6 * * *"  # Every 6 hours
    retention_days: 90
    backup_locations:
      - /var/backups/opspilot/servers
      - /var/backups/opspilot/databases
  
  # Security settings
  security:
    allow_root_ssh: false
    firewall_enabled: true
    fail2ban_enabled: true
    
  # SSH configuration
  ssh:
    port: 22
    max_auth_tries: 3
    client_alive_interval: 300
    client_alive_count_max: 2

monitoring:
  # Prometheus configuration
  prometheus:
    enabled: true
    node_exporter_port: 9100
    scrape_interval: 15s
  
  # Alerting
  alerts:
    enabled: true
    email_notifications: true
    slack_webhook: "{{ salt['pillar'].get('opspilot:notifications:slack_webhook', '') }}"
    
  # Logging configuration
  logging:
    enabled: true
    level: INFO
    max_size: 100M
    retention_days: 30
    ship_to_backend: true

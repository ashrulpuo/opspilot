# OpsPilot Development Configuration
# Development environment specific configurations

{% set dev_config = salt['pillar'].get('opspilot:dev', {}) %}

# Enable debug logging
debug-logging:
  file.managed:
    - name: /etc/opspilot/debug.conf
    - contents: |
      [logging]
      level = DEBUG
      handlers = file
      [formatter_simple]
      format = %(asctime)s - %(name)s - %(levelname)s - %(message)s
      [handler_file]
      class = logging.FileHandler
      level = DEBUG
      formatter = simple
      args = ('/var/log/opspilot/debug.log', 'a')
    - user: opspilot
    - mode: '0644'
    - makedirs: True

# Disable authentication for local development
dev-auth-disabled:
  file.managed:
    - name: /etc/opspilot/dev-auth.conf
    - contents: |
      [auth]
      enabled = false
      allow_local = true
      allow_anonymous = true
    - user: opspilot
    - mode: '0644'

# Configure local test endpoints
test-endpoints:
  file.managed:
    - name: /etc/opspilot/endpoints.conf
    - contents: |
      [endpoints]
      api_url = http://localhost:9000/api/v1
      health_check_url = http://localhost:9000/api/v1/health
      metrics_endpoint = http://localhost:9000/api/v1/metrics
    - user: opspilot
    - mode: '0644'

# Enable mock metrics for testing
mock-metrics:
  file.managed:
    - name: /var/lib/opspilot/mock_metrics.json
    - contents: |
      {
        "cpu": 45.5,
        "memory": 62.3,
        "disk": 71.2,
        "network": {
          "in": 1024000,
          "out": 512000
        }
      }
    - user: opspilot
    - mode: '0644'

# Configure development monitoring intervals
dev-monitoring-intervals:
  file.managed:
    - name: /etc/opspilot/dev-monitoring.conf
    - contents: |
      [monitoring]
      metrics_interval = 30  # More frequent in dev
      health_check_interval = 60
      log_ship_interval = 60
      mock_data = true
    - user: opspilot
    - mode: '0644'

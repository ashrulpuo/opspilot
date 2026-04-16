# OpsPilot Alerting State
# Configures Prometheus alerting and notification rules

{% set alerting_config = salt['pillar'].get('opspilot:alerts', {}) %}

# Install alerting dependencies
alerting-deps:
  pkg.installed:
    - names:
      - prometheus-alertmanager
      - python3-prometheus-client
      - python3-requests
    - refresh: True

# Configure Alertmanager
alertmanager-config:
  file.managed:
    - name: /etc/alertmanager/alertmanager.yml
    - contents: |
      global:
        resolve_timeout: 5m
        smtp_smarthost: {{ alerting_config.get('smtp_host', 'localhost') }}
        smtp_from: {{ alerting_config.get('smtp_from', 'alerts@opspilot.local') }}
        smtp_auth_username: {{ alerting_config.get('smtp_user', '') }}
        smtp_auth_password: {{ alerting_config.get('smtp_password', '') }}
      
      route:
        group_by: ['alertname', 'cluster', 'service']
        group_wait: 10s
        group_interval: 10s
        repeat_interval: 12h
        receiver: 'opspilot-backend'
      
      receivers:
        - name: 'opspilot-backend'
          webhook_configs:
            - send_resolved: true
              url: {{ alerting_config.get('backend_webhook', 'http://localhost:9000/api/v1/alerts/webhook') }}
              http_config:
                bearer_token: {{ alerting_config.get('api_key', '') }}
        
      inhibit_rules:
        - source_match: 'alertname'
          target_match_re: 'Info'
          equal: ['alertname']
          regex: 'Warning'
          severity: 'warning'
      
      templates:
        - '/etc/alertmanager/templates/opspilot.tmpl'
    - user: root
    - mode: '0644'
    - require:
      - pkg: alerting-deps

# Create alert template
alert-template:
  file.managed:
    - name: /etc/alertmanager/templates/opspilot.tmpl
    - contents: |
      {{ define "slack.title" }}[{{ .Status | toUpper }}{{ if eq .Status "firing" }}]}}:{{ end }}{{ range .Alerts }}{{ .Labels.alertname }}{{ if .Labels.server }} for {{ .Labels.server }}{{ end }}{{ end }}
      {{- end }}
      {{ define "slack.message" }}{{ range .Alerts }}
      *Alert:* {{ .Labels.alertname }}
      *Server:* {{ .Labels.server | default "Unknown" }}
      *Severity:* {{ .Labels.severity | default "warning" }}
      *Status:* {{ .Status | toUpper }}
      *Description:* {{ .Annotations.description | default "No description" }}
      *Timestamp:* {{ .StartsAt.Format "2006-01-02 15:04:05.000" -0700 }}
      {{- end }}
      {{ end }}
      
      {
        "text": {{ template "slack.message" . }},
        "blocks": [
          {
            "type": "header",
            "text": {
              "type": "plain_text",
              "text": {{ template "slack.title" . }},
            },
          },
          {
            "type": "section",
            "fields": [
              {
                "title": "Server",
                "value": {{ .Labels.server | default "Unknown" }},
                "short": false,
              },
              {
                "title": "Severity",
                "value": {{ .Labels.severity | default "warning" }},
                "short": true,
              },
              {
                "title": "Status",
                "value": {{ .Status | toUpper }},
                "short": true,
              },
            ],
          },
        ],
      }
    - user: root
    - mode: '0644'
    - require:
      - file: alertmanager-config

# Start Alertmanager
alertmanager-service:
  service.running:
    - name: prometheus-alertmanager
    - enable: True
    - require:
      - file: alertmanager-config
      - file: alert-template

# Configure Prometheus to send alerts to Alertmanager
prometheus-alerts-config:
  file.managed:
    - name: /etc/prometheus/alerts.yml
    - contents: |
      groups:
        - name: opspilot.alerts
          interval: 30s
          rules:
            - alert: HighCPUUsage
              expr: 100 * (1 - avg(rate(node_cpu_seconds_total[5m])) > {{ alerting_config.get('cpu_threshold', 90) }}
              for: 5m
              labels:
                severity: warning
                alerttype: resource
              annotations:
                summary: "High CPU usage detected"
                description: "CPU usage is above {{ alerting_config.get('cpu_threshold', 90) }}% for more than 5 minutes"
            
            - alert: HighMemoryUsage
              expr: (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 < {{ alerting_config.get('memory_threshold', 10) }}
              for: 5m
              labels:
                severity: warning
                alerttype: resource
              annotations:
                summary: "High memory usage detected"
                description: "Memory available is below {{ alerting_config.get('memory_threshold', 10) }}%"
            
            - alert: HighDiskUsage
              expr: (node_filesystem_avail_bytes{mountpoint="/"} / {{ alerting_config.get('disk_mount', '/')} /"} / node_filesystem_size_bytes{mountpoint="/"} / {{ alerting_config.get('disk_mount', '/')} /"}) * 100 < {{ alerting_config.get('disk_threshold', 15) }}
              for: 5m
              labels:
                severity: warning
                alerttype: resource
              annotations:
                summary: "High disk usage detected"
                description: "Disk available is below {{ alerting_config.get('disk_threshold', 15) }}%"
            
            - alert: ServerDown
              expr: up{job="node_exporter"} == 0
              for: 1m
              labels:
                severity: critical
                alerttype: availability
              annotations:
                summary: "Server is down"
                description: "Node exporter is not responding"
            
            - alert: SSHBruteForce
              expr: rate(sshd_auth_successes_total[5m])[5m] > 10
              for: 5m
              labels:
                severity: critical
                alerttype: security
              annotations:
                summary: "SSH brute force attack detected"
                description: "More than 10 successful SSH logins per minute"
    - user: root
    - mode: '0644'
    - require:
      - pkg: alerting-deps

# Reload Prometheus configuration
prometheus-reload:
  cmd.run:
    - name: reload prometheus
    - onchanges:
      - file: prometheus-alerts-config
    - run: killall -HUP prometheus

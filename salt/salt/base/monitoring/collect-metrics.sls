# OpsPilot Monitoring State
# Configures Prometheus node_exporter and metrics collection

{% set monitoring_config = salt['pillar'].get('monitoring', {}) %}

# Install node_exporter
install-node-exporter:
  pkg.installed:
    - name: prometheus-node-exporter
    - version: latest
    - refresh: True

# Create node_exporter user
node-exporter-user:
  user.present:
    - name: node_exporter
    - shell: /sbin/nologin
    - system: True
    - createhome: False

# Configure node_exporter
node-exporter-config:
  file.managed:
    - name: /etc/default/prometheus-node-exporter
    - contents: |
      # Start Prometheus Node Exporter
      ARGS="--web.listen-address=0.0.0.0 --collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)root($$|/)"
    - user: root
    - mode: '0644'
    - require:
      - pkg: install-node-exporter

# Start node_exporter service
node-exporter-service:
  service.running:
    - name: prometheus-node-exporter
    - enable: True
    - require:
      - pkg: install-node-exporter
      - file: node-exporter-config

# Install Python monitoring dependencies
monitoring-deps:
  pkg.installed:
    - names:
      - python3-prometheus-client
      - python3-psutil
      - python3-requests
    - refresh: True

# Create monitoring directories
monitoring-dirs:
  file.directory:
    - names:
      - /var/lib/opspilot/monitoring
      - /var/log/opspilot/monitoring
    - mode: '0755'
    - makedirs: True
    - user: opspilot

# Configure metrics collection interval
metrics-config:
  file.managed:
    - name: /etc/opspilot/metrics.conf
    - contents: |
      [metrics]
      collection_interval = {{ monitoring_config.get('interval', 60) }}
      cpu_threshold = {{ monitoring_config.get('cpu_threshold', 90) }}
      memory_threshold = {{ monitoring_config.get('memory_threshold', 90) }}
      disk_threshold = {{ monitoring_config.get('disk_threshold', 85) }}
    - user: root
    - mode: '0644'
    - require:
      - file: monitoring-dirs

# Enable system performance metrics
enable-metrics:
  sysctl.present:
    - name: vm.swappiness
    - value: 10
    - config: /etc/sysctl.conf

enable-disk-metrics:
  sysctl.present:
    - name: vm.vfs_cache_pressure
    - value: 50
    - config: /etc/sysctl.conf

# Setup log rotation for metrics logs
metrics-logrotate:
  file.managed:
    - name: /etc/logrotate.d/opspilot-metrics
    - contents: |
      /var/log/opspilot/monitoring/*.log {
          daily
          rotate 7
          compress
          missingok
          notifempty
          size 100M
      }
    - user: root
    - mode: '0644'
    - require:
      - file: monitoring-dirs

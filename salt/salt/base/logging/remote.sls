# OpsPilot Remote Logging State
# Configures centralized log shipping to OpsPilot backend

{% set logging_config = salt['pillar'].get('opspilot:logging', {}) %}

# Install logging dependencies
logging-deps:
  pkg.installed:
    - names:
      - logrotate
      - rsyslog
      - python3-aiohttp
    - refresh: True

# Configure rsyslog for remote logging
rsyslog-config:
  file.managed:
    - name: /etc/rsyslog.d/50-opspilot.conf
    - contents: |
      # OpsPilot log forwarding
      $ModLoad omhttp
      $ActionOMHTTPSessionResumeRetryCount 10
      $ActionOMHTTPSessionHeader Content-Type: application/json
      $ActionOMHTTPSessionHeader X-API-Key {{ logging_config.get('api_key', '') }}
      
      # Forward all logs
      *.* action="omhttp:{{ logging_config.get('endpoint', 'http://localhost:9000/api/v1/logs') }}/json"
    - user: root
    - mode: '0644'
    - require:
      - pkg: logging-deps

# Restart rsyslog
rsyslog-service:
  service.running:
    - name: rsyslog
    - enable: True
    - require:
      - file: rsyslog-config
      - watch:
        - file: rsyslog-config

# Configure log rotation
logrotate-config:
  file.managed:
    - name: /etc/logrotate.d/opspilot
    - contents: |
      /var/log/opspilot/*.log {
          daily
          rotate {{ logging_config.get('rotate_days', 30) }}
          compress
          delaycompress
          notifempty
          missingok
          sharedscripts
              postrotate
                  if [ -d /var/log/opspilot ]; then
                      touch /var/log/opspilot/archive
                  fi
          postrotate
              /bin/kill -HUP $(cat /var/run/rsyslogd.pid)
      }
    - user: root
    - mode: '0644'
    - require:
      - pkg: logging-deps

# Create log archive directory
log-archive:
  file.directory:
    - name: /var/log/opspilot/archive
    - user: opspilot
    - mode: '0755'
    - makedirs: True
    - require:
      - file: logrotate-config

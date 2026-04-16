# OpsPilot Salt Setup State
# Installs and configures OpsPilot agent on servers

{% set opspilot_config = salt['pillar'].get('opspilot', {}) %}

# Install required packages
opspilot-packages:
  pkg.installed:
    - names:
      - python3-pip
      - curl
      - wget
      - jq
    - refresh: True

# Install Python packages for OpsPilot agent
opspilot-python-deps:
  pip.installed:
    - names:
      - requests
      - psutil
      - aiohttp
    - upgrade: True

# Create OpsPilot user
opspilot-user:
  user.present:
    - name: opspilot
    - shell: /bin/bash
    - home: /opt/opspilot
    - createhome: True

# Create OpsPilot directories
opspilot-directories:
  file.directory:
    - names:
      - /opt/opspilot/bin
      - /opt/opspilot/logs
      - /opt/opspilot/config
      - /opt/opspilot/scripts
      - /var/log/opspilot
    - user: opspilot
    - mode: '0755'
    - makedirs: True

# Deploy OpsPilot agent script
opspilot-agent:
  file.managed:
    - name: /opt/opspilot/bin/opspilot-agent.py
    - source: salt://opspilot/opspilot-agent.py
    - user: opspilot
    - group: opspilot
    - mode: '0755'

# Configure OpsPilot agent (JSON for push agent)
opspilot-config:
  file.managed:
    - name: /opt/opspilot/config/agent.json
    - source: salt://opspilot/agent.json.jinja
    - user: opspilot
    - group: opspilot
    - mode: '0644'
    - template: jinja
    - context:
      api_base_url: {{ opspilot_config.get('api_base_url', opspilot_config.get('api_url', 'http://127.0.0.1:8000/api/v1')) }}
      api_key: {{ opspilot_config.get('api_key') }}
      server_id: {{ opspilot_config.get('server_id', '') }}
      organization_id: {{ opspilot_config.get('organization_id') }}
      interval_seconds: {{ opspilot_config.get('metrics_interval', 60) }}

# Configure OpsPilot systemd service
opspilot-service:
  file.managed:
    - name: /etc/systemd/system/opspilot-agent.service
    - source: salt://opspilot/opspilot-agent.service
    - mode: '0644'

  cmd.run:
    - name: reload systemd
    - onchanges:
      - /etc/systemd/system/opspilot-agent.service
    - run: systemctl daemon-reload

opspilot-service-enabled:
  service.enabled:
    - name: opspilot-agent
    - enable: True
    - require:
      - file: /etc/systemd/system/opspilot-agent.service
      - cmd: reload systemd

opspilot-service-running:
  service.running:
    - name: opspilot-agent
    - enable: True
    - require:
      - service: opspilot-service-enabled
      - file: opspilot-agent
      - file: opspilot-config

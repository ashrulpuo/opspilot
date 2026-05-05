# OpsPilot Salt — minion baseline (PRD 002: minions push to backend API via Salt)
#
# Metrics: use execution module ``opspilot_metrics.push`` (``salt/salt/_modules/opspilot_metrics.py``)
# and ``base.opspilot.salt_metrics_schedule`` (cron). Pillar ``opspilot`` is set by OpsPilot API.
#
# Do not deploy the legacy standalone systemd push-agent here; SSH install also no longer deploys it.

# Shared packages (backup / scripts / troubleshooting)
opspilot-packages:
  pkg.installed:
    - names:
      - curl
      - wget
      - jq
    - refresh: True

# System user + dirs used by backup/monitoring states (see base.backup.backup, base.monitoring.*)
opspilot-user:
  user.present:
    - name: opspilot
    - shell: /bin/bash
    - home: /opt/opspilot
    - createhome: True

opspilot-directories:
  file.directory:
    - names:
      - /opt/opspilot/scripts
      - /opt/opspilot/logs
      - /var/log/opspilot
    - user: opspilot
    - mode: '0755'
    - makedirs: True

# If this minion was previously managed by an older state that installed ``opspilot-agent.service``, stop it.
legacy_opspilot_push_agent_stopped:
  service.dead:
    - name: opspilot-agent
    - enable: False

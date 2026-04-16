# Salt Top File
# Assigns states to minions based on environment and roles

base:
  '*':
    - base.opspilot.setup
    - base.monitoring.collect-metrics
    - base.backup.backup
    - base.security.hardening
    - base.logging.remote

dev:
  'dev-*':
    - base.dev.configuration

prod:
  'prod-*':
    - base.security.hardening
    - base.monitoring.alerts

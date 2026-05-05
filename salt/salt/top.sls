# Salt Top File
# Assigns states to minions based on environment and roles

base:
  '*':
    - base.opspilot.setup
    # Salt-scheduled HTTP metrics (pillar opspilot:* + ``opspilot_metrics.push``)
    - base.opspilot.salt_metrics_schedule
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

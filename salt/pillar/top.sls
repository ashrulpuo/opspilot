# Pillar Top File
# Assigns pillar data to minions

base:
  '*':
    - base
    - opspilot
    - server_config
    - org_config

dev:
  'dev-*':
    - dev
    - opspilot:dev

prod:
  'prod-*':
    - prod
    - opspilot:prod

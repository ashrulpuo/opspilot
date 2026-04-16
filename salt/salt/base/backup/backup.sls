# OpsPilot Backup State
# Configures rsync backup jobs and scheduling

{% set backup_config = salt['pillar'].get('backup', {}) %}

# Install rsync if not present
install-rsync:
  pkg.installed:
    - name: rsync
    - refresh: True

# Create backup directories
backup-directories:
  file.directory:
    - names:
      - /var/backups/opspilot
      - /var/backups/opspilot/servers
      - /var/backups/opspilot/databases
      - /var/log/opspilot/backups
    - user: opspilot
    - mode: '0755'
    - makedirs: True
    - require:
      - user: opspilot-user

# Create backup script
backup-script:
  file.managed:
    - name: /opt/opspilot/scripts/backup.sh
    - source: salt://opspilot/backup-script.sh
    - user: opspilot
    - group: opspilot
    - mode: '0755'
    - require:
      - file: backup-directories

# Configure cron jobs for backups
backup-cron:
  cron.present:
    - name: opspilot-backup
    - user: opspilot
    - minute: '0'
    - hour: '*/6'  # Every 6 hours
    - comment: 'OpsPilot automated backup'
    - require:
      - file: backup-script

# Configure log rotation for backup logs
backup-logrotate:
  file.managed:
    - name: /etc/logrotate.d/opspilot-backup
    - contents: |
      /var/log/opspilot/backups/*.log {
          daily
          rotate 30
          compress
          missingok
          notifempty
      }
    - user: root
    - mode: '0644'

# Backup retention policy (keep backups for 90 days)
retention-policy:
  file.managed:
    - name: /opt/opspilot/scripts/cleanup-old-backups.sh
    - contents: |
      #!/bin/bash
      # Cleanup backups older than 90 days
      find /var/backups/opspilot -type f -mtime +90 -delete
      
      # Cleanup log files older than 90 days
      find /var/log/opspilot/backups -type f -mtime +90 -delete
    - user: opspilot
    - mode: '0755'

# Add cleanup to daily cron
cleanup-cron:
  cron.present:
    - name: opspilot-backup-cleanup
    - user: opspilot
    - minute: '0'
    - hour: '3'  # 3 AM daily
    - comment: 'OpsPilot backup cleanup'
    - require:
      - file: retention-policy

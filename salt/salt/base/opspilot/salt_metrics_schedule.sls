{# Scheduled push to OpsPilot via execution module ``opspilot_snapshot.push``
   (metrics + host_profile + processes/services/packages/logs).

   Requires ``saltutil.sync_modules`` after updating ``_modules``.

   Deprecated single-metric cron: ``opspilot_metrics.push`` is still available for light-only pushes.

   Prereqs (on Salt master):
   - ``_modules/opspilot_metrics.py`` in file_roots (synced to minions).
   - Pillar ``opspilot`` with api_base_url, server_id, organization_id, api_key (OpsPilot sets these).

   First run on a minion (after sync):
     salt MINION saltutil.sync_modules
     salt MINION state.apply base.opspilot.salt_metrics_schedule

   Cron runs every 5 minutes. Adjust ``minute`` as needed.
#}

{% set op = salt['pillar.get']('opspilot', {}) or {} %}
{% set has_creds = (op.get('server_id') or salt['pillar.get']('opspilot:server_id', None))
   and (op.get('api_key') or salt['pillar.get']('opspilot:api_key', None)) %}

{% if has_creds %}

opspilot_snapshot_push_cron:
  cron.present:
    - identifier: OPSPILOT_SNAPSHOT_SALT_PUSH
    - name: /usr/bin/salt-call opspilot_snapshot.push
    - user: root
    - minute: '*/5'

{% endif %}

#!/usr/bin/env bash
# After updating repo salt/salt/_modules on the Salt master file_roots:
#
# Option A — OpsPilot UI (automates sync + cron + pillar key when key is rotated):
#   POST /api/v1/servers/{id}/reinstall-salt-minion  (stored SSH creds + SALT_MASTER_HOST)
#   The backend SSH flow runs: restart minion, saltutil.sync_modules,
#   state.apply base.opspilot.salt_metrics_schedule (best-effort if master has that state).
#
# Option B — Manual on each minion or from Salt master:
set -euo pipefail

echo "==> Manual fallback (if you did not use Reinstall in OpsPilot)"
echo "    1) salt-call saltutil.sync_modules"
echo "    2) salt-call state.apply base.opspilot.salt_metrics_schedule"
echo "    3) salt-call opspilot_snapshot.push   # optional smoke test"
echo ""
echo "==> Master must serve updated _modules/*.py before sync_modules copies them down."
echo "==> Pillar opspilot: api_base_url, server_id, organization_id, api_key (OpsPilot sets these)."
exit 0

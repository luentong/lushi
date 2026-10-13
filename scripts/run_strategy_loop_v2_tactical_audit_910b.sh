#!/usr/bin/env bash
source /usr/local/Ascend/cann-8.5.0/set_env.sh
set -euo pipefail
ROOT=/workspace/hearthstone-agent
REPORTS=/workspace/hs_decision_quality_verify_20260928/reports/strategy-loop-v2
export PYTHONPATH="${ROOT}/src:${ROOT}/scripts"
PYTHON=/usr/local/python3.11.14/bin/python3.11

for epoch in 2 4; do
  "${PYTHON}" "${ROOT}/scripts/audit_search_tactics.py" \
    --checkpoint "${REPORTS}/closed-loop-v2.epoch${epoch}.pt" \
    --device npu --budgets 128 --seeds 71 113 197 251 307 \
    --disable-tactical-precheck --audit-turn \
    --output "${REPORTS}/tactical-audit-epoch${epoch}-no-precheck.json"
done

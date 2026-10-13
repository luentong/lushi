#!/usr/bin/env bash
source /usr/local/Ascend/cann-8.5.0/set_env.sh
set -euo pipefail
ROOT=/workspace/hearthstone-agent
REPORTS=/workspace/hs_decision_quality_verify_20260928/reports/strategy-loop-v2
export PYTHONPATH="${ROOT}/src:${ROOT}/scripts"
/usr/local/python3.11.14/bin/python3.11 \
  "${ROOT}/scripts/evaluate_columnar_policy_value.py" \
  --checkpoint "${REPORTS}/closed-loop-v1.epoch2.widened-v2.pt" \
  --data "${REPORTS}/columnar127-v6-effect"/*.pt \
         "${REPORTS}/columnar-qtarget-v6-effect-127vocab"/*.pt \
  --device npu --validation-mod 5 --validation-rem 0 \
  > "${REPORTS}/eval-baseline-v1-epoch2-widened.json" \
  2> "${REPORTS}/eval-baseline-v1-epoch2-widened.err"

#!/usr/bin/env bash
source /usr/local/Ascend/cann-8.5.0/set_env.sh
set -euo pipefail
ROOT=/workspace/hearthstone-agent
REPORTS=/workspace/hs_decision_quality_verify_20260928/reports/strategy-loop-v2
export PYTHONPATH="${ROOT}/src:${ROOT}/scripts"
PYTHON=/usr/local/python3.11.14/bin/python3.11
HELD_OUT=dragon_hunter_user_02

# Train from random initialization so this deck variant cannot leak through
# an earlier checkpoint. All matchup shards containing the exact ID are held out.
"${PYTHON}" "${ROOT}/scripts/train_columnar_policy_value.py" \
  --data "${REPORTS}/columnar127-v6-effect"/*.pt \
  --priority-data "${REPORTS}/columnar-qtarget-v6-effect-127vocab"/*.pt \
  --priority-repeat 1 \
  --tactical-data "${REPORTS}/teacher-v6-effect-127vocab.pt" \
  --tactical-repeat 64 \
  --exclude-deck-id "${HELD_OUT}" \
  --output "${REPORTS}/heldout-${HELD_OUT}.pt" \
  --device npu --epochs 4 --batch-size 256 --hidden-size 1024 \
  --action-hidden-size 512 --residual-blocks 8 --card-embedding-size 256 \
  --learning-rate 0.0001 --value-weight 0.15 --action-value-weight 0.10 \
  --conditional-policy-weight 6 --checkpoint-every 2 \
  --exclude-mod 5 --exclude-rem 0 --seed 20260928

"${PYTHON}" "${ROOT}/scripts/evaluate_columnar_policy_value.py" \
  --checkpoint "${REPORTS}/heldout-${HELD_OUT}.epoch2.pt" \
  --data "${REPORTS}/columnar127-v6-effect"/*__"${HELD_OUT}"*.pt \
  --device npu --validation-mod 5 --validation-rem 0 \
  > "${REPORTS}/eval-heldout-${HELD_OUT}-epoch2.json"
"${PYTHON}" "${ROOT}/scripts/evaluate_columnar_policy_value.py" \
  --checkpoint "${REPORTS}/heldout-${HELD_OUT}.epoch4.pt" \
  --data "${REPORTS}/columnar127-v6-effect"/*__"${HELD_OUT}"*.pt \
  --device npu --validation-mod 5 --validation-rem 0 \
  > "${REPORTS}/eval-heldout-${HELD_OUT}-epoch4.json"

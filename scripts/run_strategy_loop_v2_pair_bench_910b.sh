#!/usr/bin/env bash
source /usr/local/Ascend/cann-8.5.0/set_env.sh
set -euo pipefail
ROOT=/workspace/hearthstone-agent
REPORTS=/workspace/hs_decision_quality_verify_20260928/reports/strategy-loop-v2
CONFIG=${ROOT}/config/decision_quality_pair_decks_20260928.json
export PYTHONPATH="${ROOT}/src:${ROOT}/scripts"
PYTHON=/usr/local/python3.11.14/bin/python3.11
BASELINE=${REPORTS}/closed-loop-v1.epoch2.widened-v2.pt

for epoch in 2 4; do
  CHECKPOINT=${REPORTS}/closed-loop-v2.epoch${epoch}.pt
  for matchup in dragon_warrior:dragon_warrior dragon_warrior:aggro_druid; do
    DECK_A=${matchup%%:*}
    DECK_B=${matchup##*:}
    "${PYTHON}" "${ROOT}/scripts/benchmark_mcts.py" \
      --pairs 3 --seed 2026092811 --search-seed 2026092811 \
      --mode puct --baseline puct --device npu --baseline-device npu \
      --npu-devices 0,1,2,3 --workers 4 \
      --checkpoint "${CHECKPOINT}" --baseline-checkpoint "${BASELINE}" \
      --iterations 16 --samples 1 --max-total-iterations 16 \
      --neural-prior-depth 1 --tree-depth 8 \
      --baseline-iterations 16 --baseline-samples 1 \
      --baseline-max-total-iterations 16 --baseline-neural-prior-depth 1 \
      --deck-config "${CONFIG}" --deck-a "${DECK_A}" --deck-b "${DECK_B}" \
      --max-game-seconds 180 \
      --output "${REPORTS}/paired-epoch${epoch}-${DECK_A}-vs-${DECK_B}.json"
  done
done

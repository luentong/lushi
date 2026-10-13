#!/usr/bin/env bash
source /usr/local/Ascend/cann-8.5.0/set_env.sh
set -euo pipefail
ROOT=/workspace/hearthstone-agent
REPORTS=/workspace/hs_decision_quality_verify_20260928/reports/strategy-loop-v2
CONFIG=${ROOT}/config/decision_quality_pair_decks_20260928.json
export PYTHONPATH="${ROOT}/src:${ROOT}/scripts"
PYTHON=/usr/local/python3.11.14/bin/python3.11
CHECKPOINT=${REPORTS}/closed-loop-v2.epoch2.pt
BASELINE=${REPORTS}/closed-loop-v1.epoch2.widened-v2.pt

# Ten paired seeds (20 games) per matchup, with seats swapped. Epoch 2 was
# selected provisionally from held-out policy/value and tactical robustness.
for matchup in dragon_warrior:dragon_warrior dragon_warrior:aggro_druid; do
  DECK_A=${matchup%%:*}
  DECK_B=${matchup##*:}
  "${PYTHON}" "${ROOT}/scripts/benchmark_mcts.py" \
    --pairs 10 --seed 2026092821 --search-seed 2026092821 \
    --mode puct --baseline puct --device npu --baseline-device npu \
    --npu-devices 0,1,2,3 --workers 4 \
    --checkpoint "${CHECKPOINT}" --baseline-checkpoint "${BASELINE}" \
    --iterations 16 --samples 1 --max-total-iterations 16 \
    --neural-prior-depth 1 --tree-depth 8 \
    --baseline-iterations 16 --baseline-samples 1 \
    --baseline-max-total-iterations 16 --baseline-neural-prior-depth 1 \
    --deck-config "${CONFIG}" --deck-a "${DECK_A}" --deck-b "${DECK_B}" \
    --max-game-seconds 180 \
    --output "${REPORTS}/confirm-epoch2-${DECK_A}-vs-${DECK_B}.json"
done

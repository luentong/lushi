#!/usr/bin/env bash
source /usr/local/Ascend/cann-8.5.0/set_env.sh
set -euo pipefail
ROOT=/workspace/hearthstone-agent
REPORTS=/workspace/hs_decision_quality_verify_20260928/reports/strategy-loop-v2
OUT=${REPORTS}/three-traces
CONFIG=${ROOT}/config/decision_quality_pair_decks_20260928.json
CHECKPOINT=${REPORTS}/closed-loop-v2.epoch2.pt
export PYTHONPATH="${ROOT}/src:${ROOT}/scripts"
PYTHON=/usr/local/python3.11.14/bin/python3.11
mkdir -p "${OUT}"

for item in 01:202609280301 02:202609280302 03:202609280303; do
  LABEL=${item%%:*}
  SEED=${item##*:}
  "${PYTHON}" "${ROOT}/scripts/trace_search_match.py" \
    --seed "${SEED}" --search-seed 2026092831 \
    --checkpoint "${CHECKPOINT}" --both-model \
    --use-model-value --use-action-value-estimates \
    --action-value-prior-weight 2.0 \
    --deck-config "${CONFIG}" --deck-a dragon_warrior --deck-b dragon_warrior \
    --device npu:0 --samples 1 --iterations 16 --max-total-iterations 16 \
    --tree-depth 6 --rollout-depth 0 \
    --output-prefix "${OUT}/game-${LABEL}"
done

"${PYTHON}" "${ROOT}/scripts/build_hearthstone_board_replay.py" \
  "${OUT}/dragon-mirror-replay.html" \
  "新模型第1局=${OUT}/game-01.json" \
  "新模型第2局=${OUT}/game-02.json" \
  "新模型第3局=${OUT}/game-03.json"

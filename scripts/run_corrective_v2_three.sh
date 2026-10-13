#!/usr/bin/env bash
set -eo pipefail
cd /workspace/hearthstone-agent
source /usr/local/Ascend/cann-9.0.0/set_env.sh
mkdir -p reports/corrective-v2-three-mirrors
for s in 202610070801 202610070802 202610070803; do
  /usr/local/python3.11.14/bin/python3 scripts/trace_search_match.py \
    --seed "$s" --candidate-seat 0 \
    --checkpoint reports/teacher-rebuild-v4-corrective-v2-training/standard91-rollout-v3-corrective-v2.epoch2.pt \
    --both-model --use-model-value --use-action-value-estimates \
    --action-value-prior-weight 0.25 \
    --deck-config config/decks_20260924_flat.json \
    --deck-a 龙战_01 --deck-b 龙战_02 --device npu:0 \
    --samples 1 --iterations 32 --tree-depth 8 --rollout-depth 6 \
    --min-simulations-per-root-action 2 --max-total-iterations 32 \
    --max-actions 120 \
    --output-prefix "reports/corrective-v2-three-mirrors/game-$s"
done

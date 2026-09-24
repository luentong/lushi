#!/usr/bin/env bash
set -eo pipefail
cd /workspace/hearthstone-agent
source /usr/local/Ascend/cann-9.0.0/set_env.sh
BASE=(/usr/local/python3.11.14/bin/python3 scripts/benchmark_mcts.py --mode puct --checkpoint reports/standard91_generalized_20260924/standard91-generalized-expanded18-v1.epoch1.pt --device npu --npu-devices 0 --baseline puct --baseline-checkpoint reports/standard91_generalized_20260924/standard91-generalized-columnar-v1.best.pt --baseline-device npu:1 --samples 1 --iterations 4 --tree-depth 4 --max-total-iterations 4 --baseline-samples 1 --baseline-iterations 4 --baseline-tree-depth 4 --baseline-max-total-iterations 4 --pairs 3 --mcts-seats 0,1 --deck-config config/decks_20260924_flat.json --deck-a 拉法姆术_01 --deck-b 控制牧_01 --cards cards.251332.enUS.json)
PYTHONPATH=src:.deps "${BASE[@]}" --output reports/standard91_generalized_20260924/direct_e18_lafam_control_normal.json > reports/standard91_generalized_20260924/direct_e18_lafam_control_normal.log 2>&1 &
PYTHONPATH=src:.deps "${BASE[@]}" --swap-decks --output reports/standard91_generalized_20260924/direct_e18_lafam_control_swapped.json > reports/standard91_generalized_20260924/direct_e18_lafam_control_swapped.log 2>&1 &
wait

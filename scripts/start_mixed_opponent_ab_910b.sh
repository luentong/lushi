#!/usr/bin/env bash
set -eu
cd /workspace/hs_observer_entity_20260929
out=reports/mixed-opponent-ab-20261002
test ! -e "$out"
mkdir "$out"
. /usr/local/Ascend/cann-8.5.0/set_env.sh >/dev/null 2>&1
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONHASHSEED=0
python_bin=/usr/local/python3.11.14/bin/python3.11
initial=reports/entity-scale-stage2-20261001/round-008-attempt1.pt
run_arm() {
  arm=$1
  device=$2
  fraction=$3
  "$python_bin" -u scripts/train_entity_selfplay.py \
    --mode ppo --init-checkpoint "$initial" --output "$out/$arm/model.pt" \
    --device "$device" --deck-config config/decks_20260925_smoke8.json \
    --rounds 1 --games-per-round 128 --rollout-workers 8 --inference-batch-size 16 \
    --batch-size 32 --epochs 2 --learning-rate 5e-6 --max-actions 400 \
    --heuristic-opponent-fraction "$fraction" --search-opponent-fraction "$fraction" \
    --search-opponent-iterations 16 --seed 203701010000
  "$python_bin" -u scripts/evaluate_entity_policy.py \
    --candidate "$out/$arm/model.pt" --opponent-kind heuristic --device "$device" \
    --deck-config config/decks_20260925_smoke8.json --pairs-per-matchup 1 \
    --seed 203801010000 --max-game-seconds 300 --output "$out/$arm/vs-heuristic"
}
run_arm historical npu:2 0 > "$out/historical.log" 2>&1 &
first=$!
run_arm mixed npu:4 .25 > "$out/mixed.log" 2>&1 &
second=$!
wait "$first"
wait "$second"
"$python_bin" -u scripts/evaluate_entity_policy.py \
  --candidate "$out/mixed/model.pt" --opponent-kind entity --opponent "$out/historical/model.pt" \
  --device npu:4 --deck-config config/decks_20260925_smoke8.json --pairs-per-matchup 1 \
  --seed 203801020000 --max-game-seconds 300 --output "$out/mixed-vs-historical"
# Development experiment only: no checkpoint promotion or automatic larger run.

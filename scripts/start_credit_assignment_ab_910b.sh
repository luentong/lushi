#!/usr/bin/env bash
set -eu
cd /workspace/hs_observer_entity_20260929
out=reports/credit-assignment-ab-20261002
test ! -e "$out"
mkdir "$out"
. /usr/local/Ascend/cann-8.5.0/set_env.sh >/dev/null 2>&1
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONHASHSEED=0
python_bin=/usr/local/python3.11.14/bin/python3.11
initial=reports/entity-scale-stage2-20261001/round-008-attempt1.pt
train_arm() {
  arm=$1
  device=$2
  "$python_bin" -u scripts/train_entity_selfplay.py \
    --mode ppo --init-checkpoint "$initial" --output "$out/$arm/model.pt" \
    --device "$device" --deck-config config/decks_20260925_smoke8.json \
    --rounds 1 --games-per-round 256 --rollout-workers 12 --inference-batch-size 32 \
    --batch-size 32 --epochs 2 --learning-rate 5e-6 --max-actions 400 \
    --advantage-mode "$arm" --gae-lambda .95 --seed 204601010000
}
train_arm terminal npu:2 > "$out/terminal.log" 2>&1 &
first=$!
train_arm gae npu:4 > "$out/gae.log" 2>&1 &
second=$!
wait "$first"
wait "$second"
"$python_bin" -u scripts/evaluate_entity_policy.py \
  --candidate "$out/gae/model.pt" --opponent-kind entity \
  --opponent "$out/terminal/model.pt" --device npu:4 \
  --deck-config config/decks_20260925_smoke8.json --pairs-per-matchup 1 \
  --seed 204701010000 --max-game-seconds 300 --output "$out/gae-vs-terminal" \
  > "$out/direct.log" 2>&1
# No promotion: this is one controlled experiment and needs held-out confirmation.

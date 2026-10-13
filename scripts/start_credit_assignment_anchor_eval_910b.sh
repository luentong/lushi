#!/usr/bin/env bash
set -eu
cd /workspace/hs_observer_entity_20260929
. /usr/local/Ascend/cann-8.5.0/set_env.sh >/dev/null 2>&1
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONHASHSEED=0
out=reports/credit-assignment-ab-20261002
python_bin=/usr/local/python3.11.14/bin/python3.11
anchor=reports/entity-scale-stage2-20261001/round-008-attempt1.pt
evaluate() {
  arm=$1
  device=$2
  "$python_bin" -u scripts/evaluate_entity_policy.py \
    --candidate "$out/$arm/model.pt" --opponent-kind entity \
    --opponent "$anchor" --device "$device" \
    --deck-config config/decks_20260925_smoke8.json --pairs-per-matchup 1 \
    --seed 204701020000 --max-game-seconds 300 --output "$out/$arm-vs-anchor"
}
evaluate terminal npu:2 > "$out/terminal-vs-anchor.log" 2>&1 &
first=$!
evaluate gae npu:4 > "$out/gae-vs-anchor.log" 2>&1 &
second=$!
wait "$first"
wait "$second"

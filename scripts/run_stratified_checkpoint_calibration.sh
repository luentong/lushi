#!/usr/bin/env bash
# Compare two policy-prior checkpoints over a compact, deck-stratified suite.
# Run this from the repository root after sourcing the Ascend CANN environment.
set -euo pipefail

base="${1:?usage: $0 REPORT_DIR [pairs_per_seating]}"
pairs="${2:-4}"
python_bin="${PYTHON_BIN:-/usr/local/python3.11.14/bin/python3}"

# The caller must source Ascend CANN before invoking this script.  Do not
# source the vendor set_env.sh here: it can mutate shell positional parameters
# and silently terminate a multi-matchup loop after its first iteration.

candidate="$base/policy_value_standard_runtime_v2_strict.epoch8.pt"
baseline="$base/policy_value_standard_runtime_v2_strict.pt"

matchups=(
  "dragon_warrior dirty_priest"
  "dragon_pirate_warrior mogasa_shaman"
  "aggro_druid raza_demon_hunter"
  "egg_death_knight herald_warlock"
  "drake_warlock rafaam_warlock"
  "stealth_rogue omen_rogue"
  "aya_rogue control_priest"
  "quest_priest celestial_demon_hunter"
)

for matchup in "${matchups[@]}"; do
  read -r deck_a deck_b <<<"$matchup"
  output="$base/calibration_epoch8_vs_epoch12_${deck_a}_vs_${deck_b}.json"
  if [[ -s "$output" ]]; then
    echo "skip completed: $deck_a vs $deck_b"
    continue
  fi
  echo "start: $deck_a vs $deck_b"
  # A partial/invalid matchup writes its diagnostic JSON and returns 1.  It
  # must not prevent the remaining independent strata from completing.
  # A legal 40-card Azalina game reproduced at 262 actions.  400 leaves
  # headroom for valid long games; reaching it remains an explicit failed
  # diagnostic, never a scored result.
  # Keep the calibration on the currently idle die group.  Do not compete
  # with interactive/team jobs on 0,1,4,5.
  set +e
  PYTHONPATH=src "$python_bin" scripts/benchmark_mcts.py \
    --pairs "$pairs" --seed 202609231300 --mode puct --policy-only \
    --checkpoint "$candidate" --device npu --npu-devices 2,3,6,7 \
    --workers 4 --batch-root-priors --neural-prior-depth 1 \
    --samples 1 --iterations 16 --tree-depth 5 --max-total-iterations 16 \
    --baseline puct --baseline-checkpoint "$baseline" --baseline-device npu \
    --baseline-policy-only --baseline-samples 1 --baseline-iterations 16 \
    --baseline-tree-depth 5 --baseline-max-total-iterations 16 \
    --baseline-neural-prior-depth 1 \
    --deck-config config/decks_20260920_multi.json \
    --deck-a "$deck_a" --deck-b "$deck_b" --max-actions 400 --max-game-seconds 120 \
    --output "$output"
  status=$?
  set -e
  if [[ "$status" -ne 0 ]]; then
    echo "incomplete: $deck_a vs $deck_b (exit=$status); retained diagnostic $output" >&2
    # Do not move on and manufacture more data after an unexplained partial
    # game.  The JSON is a deterministic repro artifact for the next fix.
    exit "$status"
  fi
done

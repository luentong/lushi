#!/usr/bin/env bash
# Evaluate the selected E12 policy-prior PUCT checkpoint across the compact,
# deck-stratified suite.  The caller must source Ascend CANN before running.
set -euo pipefail

base="${1:?usage: $0 REPORT_DIR [pairs_per_seating]}"
pairs="${2:-4}"
python_bin="${PYTHON_BIN:-/usr/local/python3.11.14/bin/python3}"
checkpoint="$base/policy_value_standard_runtime_v2_strict.pt"

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
  output="$base/e12_vs_heuristic_${deck_a}_vs_${deck_b}.json"
  if [[ -s "$output" ]]; then
    echo "skip completed: $deck_a vs $deck_b"
    continue
  fi
  echo "start: $deck_a vs $deck_b"
  set +e
  PYTHONPATH=src "$python_bin" scripts/benchmark_mcts.py \
    --pairs "$pairs" --seed 202609231500 --mode puct --policy-only \
    --checkpoint "$checkpoint" --device npu --npu-devices 2,3,6,7 \
    --workers 4 --batch-root-priors --neural-prior-depth 1 \
    --samples 1 --iterations 16 --tree-depth 5 --max-total-iterations 16 \
    --baseline heuristic --deck-config config/decks_20260920_multi.json \
    --deck-a "$deck_a" --deck-b "$deck_b" --max-actions 400 --max-game-seconds 120 \
    --output "$output"
  status=$?
  set -e
  if [[ "$status" -ne 0 ]]; then
    echo "incomplete: $deck_a vs $deck_b (exit=$status); retained diagnostic $output" >&2
    exit "$status"
  fi
done

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
set +e +u
source /usr/local/Ascend/cann-9.0.0/set_env.sh
set -e -u
export TORCH_DEVICE_BACKEND_AUTOLOAD=0 PYTHONUNBUFFERED=1

PYTHON_BIN="${PYTHON_BIN:-/usr/local/python3.11.14/bin/python3.11}"
CANDIDATE="${CANDIDATE:-reports/jev-v7-r2-distilled-20261012-training/model.epoch2.pt}"
BASELINE="${BASELINE:-reports/jev-v7-20261010-training/model.direct-best.eval.pt}"
OUTPUT_DIR="${OUTPUT_DIR:-reports/jev-v7-r2-distilled-20261012-probe-epoch2}"
USE_ACTION_VALUES="${USE_ACTION_VALUES:-0}"
USE_CANDIDATE_ACTION_VALUES="${USE_CANDIDATE_ACTION_VALUES:-$USE_ACTION_VALUES}"
USE_BASELINE_ACTION_VALUES="${USE_BASELINE_ACTION_VALUES:-$USE_ACTION_VALUES}"
mkdir -p "$OUTPUT_DIR"

run_matchup() {
  local index="$1" deck_a="$2" deck_b="$3" device="$4"
  local action_value_args=()
  if [[ "$USE_CANDIDATE_ACTION_VALUES" == 1 ]]; then
    action_value_args+=(--use-action-values)
  fi
  if [[ "$USE_BASELINE_ACTION_VALUES" == 1 ]]; then
    action_value_args+=(--baseline-use-action-values)
  fi
  "$PYTHON_BIN" scripts/benchmark_mcts.py \
    --mode puct --baseline puct \
    "${action_value_args[@]}" \
    --checkpoint "$CANDIDATE" --baseline-checkpoint "$BASELINE" \
    --device "npu:$device" --baseline-device "npu:$device" \
    --deck-config config/decks_20260920_multi.json \
    --deck-a "$deck_a" --deck-b "$deck_b" \
    --pairs 4 --mcts-seats 0,1 \
    --samples 1 --baseline-samples 1 \
    --iterations 8 --baseline-iterations 8 \
    --tree-depth 4 --baseline-tree-depth 4 \
    --rollout-depth 0 --baseline-rollout-depth 0 \
    --max-total-iterations 8 --baseline-max-total-iterations 8 \
    --neural-prior-depth 1 --baseline-neural-prior-depth 1 \
    --max-actions 400 --max-game-seconds 300 \
    --seed "$((202610160000 + index * 1000))" \
    --search-seed "$((20261016 + index))" \
    --output "$OUTPUT_DIR/$index.json" \
    >"$OUTPUT_DIR/$index.log" 2>&1
}

run_matchup 0 dragon_warrior dragon_warrior 1 &
pid0="$!"
run_matchup 1 egg_death_knight mogasa_shaman 2 &
pid1="$!"
wait "$pid0"
wait "$pid1"

"$PYTHON_BIN" - "$OUTPUT_DIR" "$CANDIDATE" "$BASELINE" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
rows = []
for index, matchup in enumerate(("dragon_warrior mirror", "egg_death_knight vs mogasa_shaman")):
    result = json.loads((root / f"{index}.json").read_text(encoding="utf-8"))
    summary = result["summary"]
    rows.append({"matchup": matchup, "games": summary["valid_games"],
                 "wins": summary["mcts_wins"],
                 "invalid_actions": summary["invalid_actions"],
                 "timed_out_games": summary["timed_out_games"]})
payload = {"candidate": sys.argv[2], "baseline": sys.argv[3], "matchups": rows,
           "games": sum(row["games"] for row in rows),
           "wins": sum(row["wins"] for row in rows)}
(root / "summary.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, ensure_ascii=False))
PY

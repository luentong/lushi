#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

set +e +u
source /usr/local/Ascend/cann-9.0.0/set_env.sh
set -e -u
export TORCH_DEVICE_BACKEND_AUTOLOAD=0 PYTHONUNBUFFERED=1
# Each matchup has its own process. Avoid multiplying OpenMP workers across
# those processes; search logic is mostly serial and tiny CPU tensor ops.
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}"

PYTHON_BIN="${PYTHON_BIN:-/usr/local/python3.11.14/bin/python3.11}"
WAIT_PID="${WAIT_PID:-}"
CANDIDATE="${CANDIDATE:-reports/jev-v7-selfplay-r1-20261011-training/model.pt}"
BASELINE="${BASELINE:-reports/jev-v7-20261010-training/model.direct-best.pt}"
OUTPUT_DIR="${OUTPUT_DIR:-reports/jev-v7-selfplay-r1-20261011-eval}"
DECK_CONFIG="${DECK_CONFIG:-config/decks_20260920_multi.json}"
EVAL_PAIR_SET="${EVAL_PAIR_SET:-fixed8}"
PAIRS_PER_SEATING="${PAIRS_PER_SEATING:-4}"
EVAL_SEED_BASE="${EVAL_SEED_BASE:-202610120000}"
USE_ACTION_VALUES="${USE_ACTION_VALUES:-0}"
USE_CANDIDATE_ACTION_VALUES="${USE_CANDIDATE_ACTION_VALUES:-$USE_ACTION_VALUES}"
USE_BASELINE_ACTION_VALUES="${USE_BASELINE_ACTION_VALUES:-$USE_ACTION_VALUES}"
EVAL_NPU_DEVICES="${EVAL_NPU_DEVICES:-0,1,2,3,4,5,6,7}"
IFS=, read -r -a npu_device_list <<<"$EVAL_NPU_DEVICES"
[[ "${#npu_device_list[@]}" -gt 0 ]] || { echo "empty EVAL_NPU_DEVICES" >&2; exit 2; }
MAX_EVAL_JOBS="${MAX_EVAL_JOBS:-${#npu_device_list[@]}}"
[[ "$MAX_EVAL_JOBS" =~ ^[1-9][0-9]*$ ]] || { echo "invalid MAX_EVAL_JOBS" >&2; exit 2; }

process_is_running() {
  local pid="$1" state
  kill -0 "$pid" 2>/dev/null || return 1
  state="$(ps -o stat= -p "$pid" 2>/dev/null | tr -d '[:space:]')"
  [[ -n "$state" && "$state" != Z* ]]
}

if [[ -n "$WAIT_PID" ]]; then
  echo "waiting for training process $WAIT_PID" >&2
  while process_is_running "$WAIT_PID"; do sleep 30; done
fi
[[ -s "$CANDIDATE" ]] || { echo "candidate checkpoint missing: $CANDIDATE" >&2; exit 2; }
[[ -s "$BASELINE" ]] || { echo "baseline checkpoint missing: $BASELINE" >&2; exit 2; }
mkdir -p "$OUTPUT_DIR"

PAIRS=(
  "dragon_warrior dragon_warrior"
  "dragon_warrior aggro_druid"
  "dirty_priest herald_warlock"
  "quest_priest drake_warlock"
  "celestial_demon_hunter control_priest"
  "stealth_rogue aya_rogue"
  "egg_death_knight mogasa_shaman"
  "rafaam_warlock omen_rogue"
)
if [[ "$EVAL_PAIR_SET" == balanced32 ]]; then
  mapfile -t PAIRS < <("$PYTHON_BIN" - "$DECK_CONFIG" <<'PY'
import json
import sys
from pathlib import Path

decks = [row["id"] for row in json.loads(Path(sys.argv[1]).read_text())["decks"]]
if len(decks) != 16 or len(set(decks)) != 16:
    raise SystemExit("balanced32 expects 16 unique deck IDs")
for offset in (1, 5):
    for index, deck in enumerate(decks):
        print(deck, decks[(index + offset) % len(decks)])
PY
  )
elif [[ "$EVAL_PAIR_SET" != fixed8 ]]; then
  echo "unsupported EVAL_PAIR_SET: $EVAL_PAIR_SET" >&2
  exit 2
fi
[[ "${#PAIRS[@]}" -gt 0 ]] || { echo "empty evaluation pair set" >&2; exit 2; }

pids=()
status=0
for index in "${!PAIRS[@]}"; do
  read -r deck_a deck_b <<<"${PAIRS[$index]}"
  output="$OUTPUT_DIR/$index-$deck_a-vs-$deck_b.json"
  log="$OUTPUT_DIR/$index.log"
  device="${npu_device_list[$((index % ${#npu_device_list[@]}))]}"
  action_value_args=()
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
    --deck-config "$DECK_CONFIG" --deck-a "$deck_a" --deck-b "$deck_b" \
    --pairs "$PAIRS_PER_SEATING" --mcts-seats 0,1 \
    --samples 1 --baseline-samples 1 \
    --iterations 8 --baseline-iterations 8 \
    --tree-depth 4 --baseline-tree-depth 4 \
    --rollout-depth 0 --baseline-rollout-depth 0 \
    --max-total-iterations 8 --baseline-max-total-iterations 8 \
    --neural-prior-depth 1 --baseline-neural-prior-depth 1 \
    --max-actions 400 --max-game-seconds 300 \
    --seed "$((EVAL_SEED_BASE + index * 1000))" \
    --search-seed "$((20261012 + index))" \
    --output "$output" >"$log" 2>&1 &
  pids+=("$!")
  if [[ "${#pids[@]}" -ge "$MAX_EVAL_JOBS" ]]; then
    for pid in "${pids[@]}"; do wait "$pid" || status=1; done
    pids=()
  fi
done

for pid in "${pids[@]}"; do wait "$pid" || status=1; done
[[ "$status" -eq 0 ]] || { echo "one or more evaluation jobs failed" >&2; exit 3; }

"$PYTHON_BIN" - "$OUTPUT_DIR" "$CANDIDATE" "$BASELINE" "$USE_CANDIDATE_ACTION_VALUES" "$USE_BASELINE_ACTION_VALUES" "$EVAL_PAIR_SET" <<'PY'
import json
import math
import sys
from pathlib import Path

root = Path(sys.argv[1])
candidate = sys.argv[2]
baseline = sys.argv[3]
candidate_action_q = sys.argv[4] == "1"
baseline_action_q = sys.argv[5] == "1"
pair_set = sys.argv[6]
rows = []
for path in sorted(root.glob("*.json")):
    if path.name == "summary.json":
        continue
    payload = json.loads(path.read_text(encoding="utf-8"))
    summary = payload["summary"]
    rows.append({
        "file": path.name,
        "valid_games": summary["valid_games"],
        "candidate_wins": summary["mcts_wins"],
        "candidate_win_rate": summary["mcts_win_rate"],
        "invalid_actions": summary["invalid_actions"],
        "timed_out_games": summary["timed_out_games"],
    })
valid = sum(row["valid_games"] for row in rows)
wins = sum(row["candidate_wins"] for row in rows)
if valid:
    p = wins / valid
    z2 = 1.96 ** 2
    center = (p + z2 / (2 * valid)) / (1 + z2 / valid)
    half = 1.96 * math.sqrt(p * (1 - p) / valid + z2 / (4 * valid ** 2)) / (1 + z2 / valid)
    interval = [max(0.0, center - half), min(1.0, center + half)]
else:
    interval = None
result = {
    "candidate": candidate,
    "baseline": baseline,
    "pair_set": pair_set,
    "candidate_action_q": candidate_action_q,
    "baseline_action_q": baseline_action_q,
    "valid_games": valid,
    "candidate_wins": wins,
    "candidate_win_rate": wins / valid if valid else None,
    "wilson_95_interval": interval,
    "matchups": rows,
}
(root / "summary.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(result, ensure_ascii=False))
PY

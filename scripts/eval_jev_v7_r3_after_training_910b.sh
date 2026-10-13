#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

set +e +u
source /usr/local/Ascend/cann-9.0.0/set_env.sh
set -e -u
export TORCH_DEVICE_BACKEND_AUTOLOAD=0 PYTHONUNBUFFERED=1
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}"

PYTHON_BIN="${PYTHON_BIN:-/usr/local/python3.11.14/bin/python3.11}"
TRAIN_DIR="${TRAIN_DIR:-reports/jev-v7-selfplay-r3-mixed-20261012-training}"
EVAL_DIR="${EVAL_DIR:-reports/jev-v7-selfplay-r3-mixed-20261012-eval}"
R2_BASELINE="${R2_BASELINE:-reports/jev-v7-selfplay-r2-20261011-training/model.epoch6.eval.pt}"
CHAMPION="${CHAMPION:-reports/jev-v7-20261010-training/model.direct-best.eval.pt}"
TRAIN_WAITER_PID="${TRAIN_WAITER_PID:-}"
MAX_WAIT_SECONDS="${MAX_WAIT_SECONDS:-86400}"

process_is_running() {
  local pid="$1" state
  kill -0 "$pid" 2>/dev/null || return 1
  state="$(ps -o stat= -p "$pid" 2>/dev/null | tr -d '[:space:]')"
  [[ -n "$state" && "$state" != Z* ]]
}

mkdir -p "$EVAL_DIR"
elapsed=0
until [[ -s "$TRAIN_DIR/model.json" ]]; do
  if [[ -n "$TRAIN_WAITER_PID" ]] && ! process_is_running "$TRAIN_WAITER_PID"; then
    echo "R3 training waiter exited without a final model report" >&2
    exit 2
  fi
  if ((elapsed >= MAX_WAIT_SECONDS)); then
    echo "R3 training did not finish within ${MAX_WAIT_SECONDS}s" >&2
    exit 2
  fi
  sleep 30
  elapsed=$((elapsed + 30))
done
[[ -s "$TRAIN_DIR/model.pt" ]] || { echo "R3 model.pt missing" >&2; exit 2; }

TRAIN_DIR="$TRAIN_DIR" EVAL_DIR="$EVAL_DIR/screen" BASELINE="$R2_BASELINE" \
  EVAL_SEED_BASE=202610210000 PAIRS_PER_SEATING=4 \
  EVAL_NPU_DEVICES=0,1,2,3,4,5,6,7 \
  bash scripts/eval_jev_v7_r2_distilled_910b.sh \
  >"$EVAL_DIR/screen.log" 2>&1

best="$($PYTHON_BIN - "$EVAL_DIR/screen/summary.json" <<'PY'
import json
import sys
from pathlib import Path

rows = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["results"]
eligible = [
    row for row in rows
    if row["valid_games"] == 64
    and row["invalid_actions"] == 0 and row["timed_out_games"] == 0
]
if eligible:
    print(max(eligible, key=lambda row: row["wins"])["candidate"])
PY
)"
if [[ -z "$best" ]]; then
  "$PYTHON_BIN" - "$EVAL_DIR" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
(root / "verdict.json").write_text(
    json.dumps({
        "candidate": None,
        "promotion_eligible": False,
        "reason": "No checkpoint completed the 64-game screen without invalid actions or timeouts.",
    }, indent=2) + "\n",
    encoding="utf-8",
)
PY
  echo "no R3 checkpoint passed the 64-game validity screen" >&2
  exit 0
fi

for comparison in r2 champion; do
  if [[ "$comparison" == r2 ]]; then
    baseline="$R2_BASELINE"
    seed=202610220000
  else
    baseline="$CHAMPION"
    seed=202610230000
  fi
  CANDIDATE="$best" BASELINE="$baseline" USE_ACTION_VALUES=1 \
    EVAL_NPU_DEVICES=0,1,2,3,4,5,6,7 \
    EVAL_PAIR_SET=balanced32 \
    OUTPUT_DIR="$EVAL_DIR/confirm-vs-$comparison" \
    PAIRS_PER_SEATING=4 EVAL_SEED_BASE="$seed" \
    bash scripts/run_jev_v7_selfplay_r1_eval_910b.sh \
    >"$EVAL_DIR/confirm-vs-$comparison.log" 2>&1
done

"$PYTHON_BIN" - "$EVAL_DIR" "$best" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
best = sys.argv[2]
comparisons = {}
for name in ("r2", "champion"):
    path = root / f"confirm-vs-{name}" / "summary.json"
    summary = json.loads(path.read_text(encoding="utf-8"))
    comparisons[name] = {
        "wins": summary["candidate_wins"],
        "valid_games": summary["valid_games"],
        "wilson_95_interval": summary["wilson_95_interval"],
        "invalid_actions": sum(row["invalid_actions"] for row in summary["matchups"]),
        "timed_out_games": sum(row["timed_out_games"] for row in summary["matchups"]),
    }
promotion_eligible = all(
    row["valid_games"] == 256
    and row["wilson_95_interval"][0] > 0.5
    and row["invalid_actions"] == 0
    and row["timed_out_games"] == 0
    for row in comparisons.values()
)
result = {
    "candidate": best,
    "screen": next(
        {key: value for key, value in row.items() if key != "matchups"}
        for row in json.loads((root / "screen" / "summary.json").read_text(encoding="utf-8"))["results"]
        if row["candidate"] == best
    ),
    "comparisons": comparisons,
    "promotion_eligible": promotion_eligible,
    "note": "Promotion requires a separate rules/trace audit; no checkpoint is changed automatically.",
}
(root / "verdict.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result))
PY

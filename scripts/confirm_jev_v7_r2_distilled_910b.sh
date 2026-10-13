#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

WAIT_PID="${WAIT_PID:-}"
EVAL_DIR="${EVAL_DIR:-reports/jev-v7-r2-distilled-20261012-eval}"
CONFIRM_DIR="${CONFIRM_DIR:-reports/jev-v7-r2-distilled-20261012-confirm}"
CHAMPION="${CHAMPION:-reports/jev-v7-20261010-training/model.direct-best.eval.pt}"
R2_CANDIDATE="${R2_CANDIDATE:-reports/jev-v7-selfplay-r2-20261011-training/model.epoch6.eval.pt}"
PYTHON_BIN="${PYTHON_BIN:-/usr/local/python3.11.14/bin/python3.11}"

process_is_running() {
  local pid="$1" state
  kill -0 "$pid" 2>/dev/null || return 1
  state="$(ps -o stat= -p "$pid" 2>/dev/null | tr -d '[:space:]')"
  [[ -n "$state" && "$state" != Z* ]]
}

if [[ -n "$WAIT_PID" ]]; then
  echo "waiting for 64-game checkpoint screen $WAIT_PID" >&2
  while process_is_running "$WAIT_PID"; do sleep 30; done
fi
[[ -s "$EVAL_DIR/summary.json" ]] || {
  echo "screening summary missing: $EVAL_DIR/summary.json" >&2
  exit 2
}

best="$($PYTHON_BIN - "$EVAL_DIR/summary.json" <<'PY'
import json
import sys
from pathlib import Path

results = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["results"]
eligible = [
    row for row in results
    if row["valid_games"] == 64 and row["wins"] > 32
    and row["invalid_actions"] == 0 and row["timed_out_games"] == 0
]
if eligible:
    print(max(eligible, key=lambda row: row["wins"])["candidate"])
PY
)"
if [[ -z "$best" ]]; then
  echo "no checkpoint passed the 64-game screen; no expansion" >&2
  exit 0
fi

mkdir -p "$CONFIRM_DIR"
echo "confirming $best against champion over 256 games" >&2
CANDIDATE="$best" BASELINE="$CHAMPION" \
  USE_ACTION_VALUES=1 \
  EVAL_NPU_DEVICES=1,2,3,4,5,6,7 \
  OUTPUT_DIR="$CONFIRM_DIR/vs-champion" \
  PAIRS_PER_SEATING=16 EVAL_SEED_BASE=202610140000 \
  bash scripts/run_jev_v7_selfplay_r1_eval_910b.sh \
  >"$CONFIRM_DIR/vs-champion.log" 2>&1

champion_wins="$($PYTHON_BIN - "$CONFIRM_DIR/vs-champion/summary.json" <<'PY'
import json
import sys
from pathlib import Path

row = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(row["candidate_wins"] if row["valid_games"] == 256 else 0)
PY
)"
if (( champion_wins <= 128 )); then
  echo "candidate did not beat champion in 256 games: $champion_wins/256" >&2
  exit 0
fi

echo "confirming $best against R2 Epoch 6 over 256 games" >&2
CANDIDATE="$best" BASELINE="$R2_CANDIDATE" \
  USE_ACTION_VALUES=1 \
  EVAL_NPU_DEVICES=1,2,3,4,5,6,7 \
  OUTPUT_DIR="$CONFIRM_DIR/vs-r2-epoch6" \
  PAIRS_PER_SEATING=16 EVAL_SEED_BASE=202610150000 \
  bash scripts/run_jev_v7_selfplay_r1_eval_910b.sh \
  >"$CONFIRM_DIR/vs-r2-epoch6.log" 2>&1
echo "confirmation complete; inspect both summaries before promotion" >&2

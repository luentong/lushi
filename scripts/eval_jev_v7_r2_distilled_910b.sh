#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
set +e +u
source /usr/local/Ascend/cann-9.0.0/set_env.sh
set -e -u
export TORCH_DEVICE_BACKEND_AUTOLOAD=0

TRAIN_PID="${TRAIN_PID:-}"
TRAIN_DIR="${TRAIN_DIR:-reports/jev-v7-r2-distilled-20261012-training}"
EVAL_DIR="${EVAL_DIR:-reports/jev-v7-r2-distilled-20261012-eval}"
BASELINE="${BASELINE:-reports/jev-v7-20261010-training/model.direct-best.eval.pt}"
PYTHON_BIN="${PYTHON_BIN:-/usr/local/python3.11.14/bin/python3.11}"

process_is_running() {
  local pid="$1" state
  kill -0 "$pid" 2>/dev/null || return 1
  state="$(ps -o stat= -p "$pid" 2>/dev/null | tr -d '[:space:]')"
  [[ -n "$state" && "$state" != Z* ]]
}

if [[ -n "$TRAIN_PID" ]]; then
  echo "waiting for distilled training process $TRAIN_PID" >&2
  while process_is_running "$TRAIN_PID"; do sleep 30; done
fi

if [[ ! -s "$TRAIN_DIR/model.pt" ]]; then
  echo "training did not produce final model.pt; see $TRAIN_DIR/training.log" >&2
  exit 2
fi

mkdir -p "$EVAL_DIR"
for candidate_name in epoch2 epoch4 epoch6 epoch8 final; do
  if [[ -s "$EVAL_DIR/$candidate_name/summary.json" ]]; then
    echo "reusing completed $candidate_name screen" >&2
    continue
  fi
  if [[ "$candidate_name" == final ]]; then
    source_checkpoint="$TRAIN_DIR/model.pt"
    candidate="$TRAIN_DIR/model.eval.pt"
  else
    source_checkpoint="$TRAIN_DIR/model.$candidate_name.pt"
    candidate="$TRAIN_DIR/model.$candidate_name.eval.pt"
  fi
  if [[ -s "$source_checkpoint" ]]; then
    "$PYTHON_BIN" scripts/prepare_eval_checkpoint.py \
      --input "$source_checkpoint" --output "$candidate"
  fi
  [[ -s "$candidate" ]] || continue
  echo "evaluating $candidate_name against champion" >&2
  CANDIDATE="$candidate" BASELINE="$BASELINE" \
    USE_ACTION_VALUES=1 \
    EVAL_NPU_DEVICES=1,2,3,4,5,6,7 \
    OUTPUT_DIR="$EVAL_DIR/$candidate_name" \
    bash scripts/run_jev_v7_selfplay_r1_eval_910b.sh \
    >"$EVAL_DIR/$candidate_name.log" 2>&1
done

"$PYTHON_BIN" - "$EVAL_DIR" "$TRAIN_DIR" "$BASELINE" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
train = Path(sys.argv[2])
baseline = sys.argv[3]
results = []
for name in ("epoch2", "epoch4", "epoch6", "epoch8", "final"):
    summary_path = root / name / "summary.json"
    if not summary_path.exists():
        continue
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    rows = summary["matchups"]
    results.append({
        "candidate": str(train / ("model.eval.pt" if name == "final" else f"model.{name}.eval.pt")),
        "valid_games": summary["valid_games"],
        "wins": summary["candidate_wins"],
        "win_rate": summary["candidate_win_rate"],
        "invalid_actions": sum(row["invalid_actions"] for row in rows),
        "timed_out_games": sum(row["timed_out_games"] for row in rows),
        "matchups": rows,
    })
payload = {"baseline": baseline, "search_mode": "action_q_puct_both_sides", "results": results}
(root / "summary.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps({"baseline": baseline, "results": [
    {key: value for key, value in row.items() if key != "matchups"}
    for row in results
]}, ensure_ascii=False))
PY

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

set +e +u
source /usr/local/Ascend/cann-9.0.0/set_env.sh
set -e -u
export TORCH_DEVICE_BACKEND_AUTOLOAD=0 PYTHONUNBUFFERED=1

PYTHON_BIN="${PYTHON_BIN:-/usr/local/python3.11.14/bin/python3.11}"
WAIT_PID="${WAIT_PID:-}"
SELFPLAY_DIR="${SELFPLAY_DIR:-reports/jev-v7-selfplay-r1-20261011}"
SELFPLAY_MANIFEST="${SELFPLAY_MANIFEST:-reports/jev-v7-selfplay-r1-20261011-manifest.json}"
NEW_COLUMNAR_DIR="${NEW_COLUMNAR_DIR:-reports/jev-v7-selfplay-r1-20261011-columnar}"
BASE_COLUMNAR_DIR="${BASE_COLUMNAR_DIR:-reports/multiarchetype-jev-v7-20261010-columnar}"
EXTRA_COLUMNAR_DIRS="${EXTRA_COLUMNAR_DIRS:-}"
INIT_CHECKPOINT="${INIT_CHECKPOINT:-reports/jev-v7-20261010-training/model.direct-best.pt}"
OUTPUT_DIR="${OUTPUT_DIR:-reports/jev-v7-selfplay-r1-20261011-training}"
MAX_FAILED_JOBS="${MAX_FAILED_JOBS:-16}"
TRAIN_EPOCHS="${TRAIN_EPOCHS:-8}"
LEARNING_RATE="${LEARNING_RATE:-1e-5}"
ANCHOR_CHECKPOINT="${ANCHOR_CHECKPOINT:-}"
ANCHOR_POLICY_KL_WEIGHT="${ANCHOR_POLICY_KL_WEIGHT:-0}"
ANCHOR_VALUE_WEIGHT="${ANCHOR_VALUE_WEIGHT:-0}"

process_is_running() {
  local pid="$1" state
  kill -0 "$pid" 2>/dev/null || return 1
  state="$(ps -o stat= -p "$pid" 2>/dev/null | tr -d '[:space:]')"
  [[ -n "$state" && "$state" != Z* ]]
}

if [[ -n "$WAIT_PID" ]]; then
  echo "waiting for self-play process $WAIT_PID" >&2
  while process_is_running "$WAIT_PID"; do
    sleep 30
  done
fi

"$PYTHON_BIN" - "$SELFPLAY_MANIFEST" "$MAX_FAILED_JOBS" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
max_failed = int(sys.argv[2])
if not path.exists():
    raise SystemExit(f"self-play manifest is missing: {path}")
payload = json.loads(path.read_text(encoding="utf-8"))
failed = int(payload.get("failed_jobs", 0))
jobs = payload.get("jobs") or []
completed = int(payload.get("completed_jobs", 0)) or sum(
    row.get("status") in {"complete", "skipped"} for row in jobs
)
if failed > max_failed:
    raise SystemExit(
        f"self-play contains {failed} failed matchup jobs, above limit {max_failed}"
    )
if completed < 1:
    raise SystemExit("self-play completed no matchup jobs")
print(f"validated self-play manifest: {completed} completed, {failed} failed")
PY

mkdir -p "$NEW_COLUMNAR_DIR" "$OUTPUT_DIR"
"$PYTHON_BIN" scripts/columnize_jsonl_shards.py \
  "$SELFPLAY_DIR" "$NEW_COLUMNAR_DIR" --workers 8 --chunk-size 256 \
  >"$OUTPUT_DIR/columnize.log" 2>&1

DATA_DIRS=("$BASE_COLUMNAR_DIR" "$NEW_COLUMNAR_DIR")
if [[ -n "$EXTRA_COLUMNAR_DIRS" ]]; then
  read -r -a EXTRA_DIRS <<<"$EXTRA_COLUMNAR_DIRS"
  DATA_DIRS+=("${EXTRA_DIRS[@]}")
fi
mapfile -t DATA_FILES < <(
  find "${DATA_DIRS[@]}" \
    -maxdepth 1 -name '*.pt' -size +0c | sort
)
if [[ ${#DATA_FILES[@]} -lt 2 ]]; then
  echo "not enough combined schema-v7 shards" >&2
  exit 2
fi

echo "starting incremental JEV-v7 training with ${#DATA_FILES[@]} shards" >&2
ANCHOR_ARGS=()
if [[ -n "$ANCHOR_CHECKPOINT" ]]; then
  ANCHOR_ARGS+=(
    --anchor-checkpoint "$ANCHOR_CHECKPOINT"
    --anchor-policy-kl-weight "$ANCHOR_POLICY_KL_WEIGHT"
    --anchor-value-weight "$ANCHOR_VALUE_WEIGHT"
  )
fi
exec "$PYTHON_BIN" scripts/train_policy_value.py \
  --data "${DATA_FILES[@]}" \
  --allow-mixed-rulesets \
  --index-cache "$OUTPUT_DIR/decision-index-columnar.pt" \
  --output "$OUTPUT_DIR/model.pt" \
  --device npu \
  --architecture jev-v7-action-q \
  --hidden-size 512 \
  --action-hidden-size 256 \
  --entity-layers 3 \
  --entity-heads 8 \
  --card-embedding-size 128 \
  --init-checkpoint "$INIT_CHECKPOINT" \
  "${ANCHOR_ARGS[@]}" \
  --epochs "$TRAIN_EPOCHS" \
  --checkpoint-every 2 \
  --batch-size 256 \
  --learning-rate "$LEARNING_RATE" \
  --weight-decay 1e-4 \
  --gradient-clip 1.0 \
  --policy-weight 1.0 \
  --value-weight 1.0 \
  --action-q-weight 0.5 \
  --validation-ratio 0.1 \
  --early-stopping-patience 4 \
  --early-stopping-metric joint \
  --policy-target visits \
  --policy-target-temperature 0.7

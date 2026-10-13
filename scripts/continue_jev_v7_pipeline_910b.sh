#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

GEN_PID="${GEN_PID:?GEN_PID is required}"
PRIOR_TRAIN_WAITER_PID="${PRIOR_TRAIN_WAITER_PID:?PRIOR_TRAIN_WAITER_PID is required}"
PYTHON_BIN="${PYTHON_BIN:-/usr/local/python3.11.14/bin/python3}"
DATA_DIR="reports/multiarchetype-jev-v7-20261010"
MANIFEST="reports/multiarchetype-jev-v7-20261010-manifest.json"

process_is_running() {
  local pid="$1" state
  kill -0 "$pid" 2>/dev/null || return 1
  state="$(ps -o stat= -p "$pid" 2>/dev/null | tr -d '[:space:]')"
  [[ -n "$state" && "$state" != Z* ]]
}

while process_is_running "$GEN_PID"; do sleep 60; done

# Retry only missing/failed matchup shards. Outputs are written atomically by
# the child generator, so --resume never treats an interrupted shard as valid.
for attempt in 1 2 3; do
  count="$(find "$DATA_DIR" -maxdepth 1 -name '*.jsonl.gz' -size +0c | wc -l)"
  [[ "$count" -eq 256 ]] && break
  echo "schema-v7 repair attempt $attempt: $count/256 shards" >&2
  "$PYTHON_BIN" scripts/generate_multideck_policy_value_data.py \
    --config config/decks_20260920_multi.json \
    --cards cards.251332.enUS.json \
    --output-dir "$DATA_DIR" --manifest "$MANIFEST" \
    --total-games 2048 --min-games-per-pair 2 \
    --seed 202610100000 --seed-stride 10007 \
    --teacher-samples 2 --teacher-iterations 32 --rollout-depth 4 \
    --workers 8 --parallel-jobs 8 --max-actions 1000 \
    --ruleset-label standard-multideck-runtime-v3-jev7 \
    --card-vocab expanded-executable --continue-on-error --resume || true
done

count="$(find "$DATA_DIR" -maxdepth 1 -name '*.jsonl.gz' -size +0c | wc -l)"
if [[ "$count" -ne 256 ]]; then
  echo "schema-v7 generation incomplete after retries: $count/256" >&2
  exit 3
fi

# The existing structured baseline and JEV-v6 comparison retain NPU priority.
# Start v7 only after that queued comparison has left the machine.
while process_is_running "$PRIOR_TRAIN_WAITER_PID"; do sleep 60; done
# CANN's generated environment script reads a few optional variables before
# assigning them.  Temporarily disable nounset so an otherwise clean SSH
# environment does not abort the training handoff.
set +e +u
source /usr/local/Ascend/cann-9.0.0/set_env.sh
set -e -u
export TORCH_DEVICE_BACKEND_AUTOLOAD=0 PYTHONUNBUFFERED=1
exec scripts/run_jev_v7_experiment_910b.sh

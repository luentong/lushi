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
R2_CHECKPOINT="${R2_CHECKPOINT:-reports/jev-v7-selfplay-r2-20261011-training/model.epoch6.eval.pt}"
DISTILLED_CHECKPOINT="${DISTILLED_CHECKPOINT:-reports/jev-v7-r2-distilled-20261012-training/model.epoch8.eval.pt}"
OUTPUT_ROOT="${OUTPUT_ROOT:-reports/jev-v7-selfplay-r3-mixed-20261012}"
GAMES_PER_TEACHER="${GAMES_PER_TEACHER:-512}"
TEACHER_ITERATIONS="${TEACHER_ITERATIONS:-24}"

for checkpoint in "$R2_CHECKPOINT" "$DISTILLED_CHECKPOINT"; do
  [[ -s "$checkpoint" ]] || { echo "missing teacher checkpoint: $checkpoint" >&2; exit 2; }
done

mkdir -p "$OUTPUT_ROOT"
pids=()
for teacher in r2 distilled; do
  if [[ "$teacher" == r2 ]]; then
    checkpoint="$R2_CHECKPOINT"
    devices="npu:0,npu:1,npu:2,npu:3"
    seed=202610160000
  else
    checkpoint="$DISTILLED_CHECKPOINT"
    devices="npu:4,npu:5,npu:6,npu:7"
    seed=202610170000
  fi
  "$PYTHON_BIN" scripts/generate_multideck_policy_value_data.py \
    --config config/decks_20260920_multi.json \
    --cards cards.251332.enUS.json \
    --output-dir "$OUTPUT_ROOT/$teacher" \
    --manifest "$OUTPUT_ROOT/$teacher-manifest.json" \
    --total-games "$GAMES_PER_TEACHER" --min-games-per-pair 2 \
    --seed "$seed" --seed-stride 10007 \
    --teacher-samples 2 --teacher-iterations "$TEACHER_ITERATIONS" \
    --teacher-checkpoint "$checkpoint" --teacher-devices "$devices" \
    --teacher-value-mode trained --rollout-depth 0 \
    --workers 1 --parallel-jobs 4 --max-actions 1000 \
    --job-timeout-seconds 1800 \
    --ruleset-label standard-multideck-runtime-v3-jev7-selfplay-r3 \
    --card-vocab expanded-executable --continue-on-error --resume \
    >"$OUTPUT_ROOT/$teacher.log" 2>&1 &
  pids+=("$!")
done

status=0
for pid in "${pids[@]}"; do wait "$pid" || status=1; done
"$PYTHON_BIN" - "$OUTPUT_ROOT" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
result = {}
for teacher in ("r2", "distilled"):
    path = root / f"{teacher}-manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    jobs = manifest["jobs"]
    result[teacher] = {
        "requested_games": manifest["total_games"],
        "completed_jobs": sum(job["status"] in {"complete", "skipped"} for job in jobs),
        "failed_jobs": sum(job["status"] == "failed" for job in jobs),
        "completed_games": sum(job["games"] for job in jobs if job["status"] in {"complete", "skipped"}),
    }
(root / "summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result))
PY
exit "$status"

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
DATA_ROOT="${DATA_ROOT:-reports/jev-v7-selfplay-r4-highbudget-20261012}"
OUTPUT_DIR="${OUTPUT_DIR:-reports/jev-v7-selfplay-r4-highbudget-20261012-training}"
INIT_CHECKPOINT="${INIT_CHECKPOINT:-reports/jev-v7-selfplay-r3-mixed-20261012-training/model.epoch2.pt}"
ANCHOR_CHECKPOINT="${ANCHOR_CHECKPOINT:-reports/jev-v7-selfplay-r2-20261011-training/model.epoch6.pt}"
MAX_WAIT_SECONDS="${MAX_WAIT_SECONDS:-86400}"

mkdir -p "$OUTPUT_DIR"
elapsed=0
until [[ -s "$DATA_ROOT/summary.json" ]]; do
  if ((elapsed >= MAX_WAIT_SECONDS)); then
    echo "R4 generation did not finish within ${MAX_WAIT_SECONDS}s" >&2
    exit 2
  fi
  sleep 30
  elapsed=$((elapsed + 30))
done

"$PYTHON_BIN" - "$DATA_ROOT" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
for teacher in ("baseline", "candidate"):
    manifest = json.loads((root / f"{teacher}-manifest.json").read_text())
    jobs = manifest["jobs"]
    failures = [job for job in jobs if job["status"] == "failed"]
    files = sorted((root / teacher).glob("*.jsonl.gz"))
    if failures or len(files) != 256:
        raise SystemExit(
            f"{teacher}: {len(files)}/256 shards, {len(failures)} failed jobs; "
            "stop before training and inspect the manifest"
        )
    print(f"validated {teacher}: {len(files)}/256 shards, zero failed jobs")
PY

for teacher in baseline candidate; do
  "$PYTHON_BIN" scripts/columnize_jsonl_shards.py \
    "$DATA_ROOT/$teacher" "$DATA_ROOT/$teacher-columnar" \
    --workers 4 --chunk-size 256 \
    >"$OUTPUT_DIR/columnize-$teacher.log" 2>&1
done

mapfile -t DATA_FILES < <(
  find reports/multiarchetype-jev-v7-20261010-columnar-qmask \
       reports/jev-v7-selfplay-r2-20261011-columnar-qmask \
       reports/jev-v7-selfplay-r3-mixed-20261012/r2-columnar \
       reports/jev-v7-selfplay-r3-mixed-20261012/distilled-columnar \
       "$DATA_ROOT/baseline-columnar" "$DATA_ROOT/candidate-columnar" \
       -maxdepth 1 -name '*.pt' -size +0c | sort
)
if [[ "${#DATA_FILES[@]}" -lt 1800 ]]; then
  echo "unexpectedly few tensor shards: ${#DATA_FILES[@]}" >&2
  exit 3
fi
[[ -s "$INIT_CHECKPOINT" ]] || { echo "missing init checkpoint: $INIT_CHECKPOINT" >&2; exit 3; }
[[ -s "$ANCHOR_CHECKPOINT" ]] || { echo "missing anchor checkpoint: $ANCHOR_CHECKPOINT" >&2; exit 3; }

# Keep physical NPU 0 available for other work; this process sees physical NPU 1 as npu:0.
ASCEND_RT_VISIBLE_DEVICES=1 "$PYTHON_BIN" scripts/train_policy_value.py \
  --data "${DATA_FILES[@]}" --allow-mixed-rulesets \
  --index-cache "$OUTPUT_DIR/decision-index-columnar.pt" \
  --output "$OUTPUT_DIR/model.pt" --device npu \
  --architecture jev-v7-action-q --hidden-size 512 \
  --action-hidden-size 256 --entity-layers 3 --entity-heads 8 \
  --card-embedding-size 128 \
  --init-checkpoint "$INIT_CHECKPOINT" \
  --anchor-checkpoint "$ANCHOR_CHECKPOINT" \
  --anchor-policy-kl-weight 0.10 --anchor-value-weight 0.05 \
  --epochs 8 --checkpoint-every 2 --batch-size 256 \
  --learning-rate 5e-6 --weight-decay 1e-4 --gradient-clip 1.0 \
  --policy-weight 1.0 --value-weight 1.0 --action-q-weight 0.5 \
  --validation-ratio 0.1 --early-stopping-patience 4 \
  --early-stopping-metric joint --policy-target visits \
  --policy-target-temperature 0.7 --skip-post-training-metrics

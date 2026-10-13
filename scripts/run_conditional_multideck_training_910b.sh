#!/usr/bin/env bash
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BASE_ROOT="${BASE_ROOT:-/workspace/hearthstone-agent-live-advisory-20260925}"
BASE_RUN="$BASE_ROOT/reports/standard_live_20260926_full127"
RUN_DIR="${RUN_DIR:-$ROOT/reports/standard127-conditional-20260926-v1}"
PYTHON="${PYTHON:-/usr/local/python3.11.14/bin/python3}"

source /usr/local/Ascend/ascend-toolkit/set_env.sh >/dev/null 2>&1 || true
set -e
npu-smi info >/dev/null
export PYTHONPATH="$ROOT/src:$ROOT:$BASE_ROOT/.deps${PYTHONPATH:+:$PYTHONPATH}"
mkdir -p "$RUN_DIR"

if [[ ! -s "$BASE_RUN/standard127-balanced-replay-v2.pt" ]]; then
  echo "Missing compatible base checkpoint: $BASE_RUN/standard127-balanced-replay-v2.pt" >&2
  exit 2
fi
if [[ ! -d "$BASE_RUN/columnar" ]]; then
  echo "Missing replay columnar shards: $BASE_RUN/columnar" >&2
  exit 2
fi

echo "[$(date --iso-8601=seconds)] conditional multi-deck data generation begins" | tee -a "$RUN_DIR/pipeline.log"
"$PYTHON" "$ROOT/scripts/generate_multideck_policy_value_data.py" \
  --config "$ROOT/config/decks_20260925_standard127.json" \
  --cards "$ROOT/cards.251332.enUS.json" \
  --output-dir "$RUN_DIR/data" \
  --manifest "$RUN_DIR/manifest.json" \
  --total-games 512 \
  --min-games-per-pair 0 \
  --seed 202609260000 \
  --teacher-samples 2 \
  --teacher-iterations 32 \
  --rollout-depth 3 \
  --collect-conditional-training \
  --conditional-training-min-visits 8 \
  --conditional-training-min-action-visits 1 \
  --conditional-training-repeats 3 \
  --conditional-training-iterations 24 \
  --conditional-training-max-branches 2 \
  --workers 1 \
  --parallel-jobs 8 \
  --job-timeout-seconds 1200 \
  --continue-on-error \
  --resume \
  --max-actions 1000 \
  --ruleset-label standard-live-20260926-conditional-v1 \
  --card-vocab expanded-executable \
  >> "$RUN_DIR/generation.log" 2>&1

"$PYTHON" - "$RUN_DIR/manifest.json" <<'PY'
import json, sys
manifest = json.load(open(sys.argv[1], encoding="utf-8"))
failed = [job for job in manifest["jobs"] if job.get("status") == "failed"]
completed = [job for job in manifest["jobs"] if job.get("status") == "complete"]
print(f"generation summary: complete={len(completed)} failed={len(failed)}")
if failed:
    for job in failed[:20]:
        print(f"FAILED {job['deck_a']} vs {job['deck_b']}: {job.get('error', 'unknown')}")
    raise SystemExit("Refusing to train on an incomplete generated corpus")
if not completed:
    raise SystemExit("No complete matchup data was generated")
PY

echo "[$(date --iso-8601=seconds)] packing generated decisions" | tee -a "$RUN_DIR/pipeline.log"
"$PYTHON" "$ROOT/scripts/pack_training_shards.py" \
  "$RUN_DIR/data" "$RUN_DIR/packed" --batch-size 512 --workers 8 \
  >> "$RUN_DIR/pack.log" 2>&1
"$PYTHON" "$ROOT/scripts/columnize_pt_shards.py" \
  "$RUN_DIR/packed" "$RUN_DIR/columnar" --workers 8 \
  >> "$RUN_DIR/columnize.log" 2>&1

conditional_count=$("$PYTHON" - "$RUN_DIR/columnar" <<'PY'
import glob, sys, torch
count = 0
for path in glob.glob(sys.argv[1] + "/*.pt"):
    shard = torch.load(path, map_location="cpu", weights_only=False)
    count += int(shard.get("conditional", torch.zeros(shard["count"], dtype=torch.bool)).sum())
print(count)
PY
)
if [[ "$conditional_count" -lt 100 ]]; then
  echo "Only $conditional_count conditional decision labels; refusing under-covered training run" >&2
  exit 3
fi

echo "[$(date --iso-8601=seconds)] starting NPU fine-tuning; conditional_labels=$conditional_count" | tee -a "$RUN_DIR/pipeline.log"
npu-smi info >> "$RUN_DIR/npu-before-train.log" 2>&1

"$PYTHON" "$ROOT/scripts/train_columnar_policy_value.py" \
  --data "$BASE_RUN"/columnar/*.pt "$RUN_DIR"/columnar/*.pt \
  --output "$RUN_DIR/standard127-conditional-v1.pt" \
  --init-checkpoint "$BASE_RUN/standard127-balanced-replay-v2.pt" \
  --device npu \
  --epochs 8 \
  --batch-size 512 \
  --learning-rate 0.00002 \
  --value-weight 0.15 \
  --conditional-policy-weight 6.0 \
  --checkpoint-every 2 \
  --seed 20260926 \
  > "$RUN_DIR/training.log" 2>&1

echo "[$(date --iso-8601=seconds)] NPU fine-tuning finished" | tee -a "$RUN_DIR/pipeline.log"
npu-smi info >> "$RUN_DIR/npu-after-train.log" 2>&1

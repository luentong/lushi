#!/usr/bin/env bash
set -eo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BASE="/workspace/hearthstone-agent-conditional-20260926/reports/standard127-conditional-20260926-v1"
RUN="$ROOT/reports/dragon-warrior-qtarget-20260927"
PYTHON="/usr/local/python3.11.14/bin/python3"

source /usr/local/Ascend/cann-9.0.0/set_env.sh >/dev/null 2>&1 || true
export LD_LIBRARY_PATH="/usr/local/Ascend/cann-9.0.0/aarch64-linux/lib64:${LD_LIBRARY_PATH:-}"
export PYTHONPATH="$ROOT/src:$ROOT:$ROOT/.deps${PYTHONPATH:+:$PYTHONPATH}"
mkdir -p "$RUN"

if [[ ! -s "$BASE/standard127-conditional-v1.pt" ]]; then
  echo "Missing initialization checkpoint: $BASE/standard127-conditional-v1.pt" >&2
  exit 2
fi

echo "[$(date --iso-8601=seconds)] action-value teacher generation begins" | tee -a "$RUN/pipeline.log"
"$PYTHON" "$ROOT/scripts/generate_multideck_policy_value_data.py" \
  --config "$ROOT/config/decks_20260927_dragon_warrior_focus.json" \
  --cards "$ROOT/cards.251332.enUS.json" \
  --output-dir "$RUN/data" \
  --manifest "$RUN/manifest.json" \
  --total-games 48 \
  --min-games-per-pair 48 \
  --seed 202609270271 \
  --teacher-samples 2 \
  --teacher-iterations 48 \
  --rollout-depth 3 \
  --policy-target-source action-values \
  --policy-action-value-temperature 0.15 \
  --collect-conditional-training \
  --conditional-training-min-visits 6 \
  --conditional-training-min-action-visits 1 \
  --conditional-training-repeats 4 \
  --conditional-training-iterations 32 \
  --conditional-training-max-branches 2 \
  --workers 4 \
  --parallel-jobs 1 \
  --job-timeout-seconds 5400 \
  --max-actions 1000 \
  --ruleset-label dragon-warrior-qtarget-conditional-20260927 \
  --card-vocab expanded-executable \
  > "$RUN/generation.log" 2>&1

"$PYTHON" - "$RUN/manifest.json" <<'PY'
import json, sys
manifest = json.load(open(sys.argv[1], encoding="utf-8"))
failed = [job for job in manifest["jobs"] if job.get("status") == "failed"]
complete = [job for job in manifest["jobs"] if job.get("status") == "complete"]
if failed or not complete:
    raise SystemExit(f"teacher generation incomplete: complete={len(complete)} failed={len(failed)}")
print(f"teacher generation complete: {len(complete)} ordered pairs")
PY

echo "[$(date --iso-8601=seconds)] packing and tensor conversion begin" | tee -a "$RUN/pipeline.log"
"$PYTHON" "$ROOT/scripts/pack_training_shards.py" \
  "$RUN/data" "$RUN/packed" --batch-size 512 --workers 4 \
  > "$RUN/pack.log" 2>&1
"$PYTHON" "$ROOT/scripts/columnize_pt_shards.py" \
  "$RUN/packed" "$RUN/columnar" --workers 4 \
  > "$RUN/columnize.log" 2>&1

conditional_count=$("$PYTHON" - "$RUN/columnar" <<'PY'
import glob, sys, torch
count = 0
for path in glob.glob(sys.argv[1] + "/*.pt"):
    shard = torch.load(path, map_location="cpu", weights_only=False)
    count += int(shard.get("conditional", torch.zeros(shard["count"], dtype=torch.bool)).sum())
print(count)
PY
)
if [[ "$conditional_count" -lt 20 ]]; then
  echo "Only $conditional_count conditional branch labels; refusing fine-tuning" >&2
  exit 3
fi

echo "[$(date --iso-8601=seconds)] NPU fine-tuning begins; conditional_labels=$conditional_count" | tee -a "$RUN/pipeline.log"
npu-smi info > "$RUN/npu-before-train.log" 2>&1
"$PYTHON" "$ROOT/scripts/train_columnar_policy_value.py" \
  --data "$RUN"/columnar/*.pt \
  --output "$RUN/dragon-warrior-qtarget-conditional.pt" \
  --init-checkpoint "$BASE/standard127-conditional-v1.pt" \
  --device npu \
  --epochs 6 \
  --batch-size 256 \
  --learning-rate 0.00001 \
  --value-weight 0.15 \
  --conditional-policy-weight 10.0 \
  --checkpoint-every 2 \
  --seed 20260927 \
  > "$RUN/training.log" 2>&1

echo "[$(date --iso-8601=seconds)] Q-target fine-tuning complete" | tee -a "$RUN/pipeline.log"
npu-smi info > "$RUN/npu-after-train.log" 2>&1

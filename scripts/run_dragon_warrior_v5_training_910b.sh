#!/usr/bin/env bash
set -eo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BASE="/workspace/hearthstone-agent-conditional-20260926"
BASE_RUN="$BASE/reports/standard127-conditional-20260926-v1"
RUN="$ROOT/reports/dragon-warrior-v5-conditional-20260927"
PYTHON="/usr/local/python3.11.14/bin/python3"

source /usr/local/Ascend/cann-9.0.0/set_env.sh >/dev/null 2>&1 || true
export LD_LIBRARY_PATH="/usr/local/Ascend/cann-9.0.0/aarch64-linux/lib64:${LD_LIBRARY_PATH:-}"
export PYTHONPATH="$ROOT/src:$ROOT:$ROOT/.deps${PYTHONPATH:+:$PYTHONPATH}"
mkdir -p "$RUN"
npu-smi info >/dev/null

if [[ ! -s "$BASE_RUN/standard127-conditional-v1.pt" ]]; then
  echo "Missing base checkpoint: $BASE_RUN/standard127-conditional-v1.pt" >&2
  exit 2
fi

echo "[$(date --iso-8601=seconds)] v5 focused conditional data generation begins" | tee -a "$RUN/pipeline.log"
"$PYTHON" "$ROOT/scripts/generate_multideck_policy_value_data.py" \
  --config "$ROOT/config/decks_20260927_dragon_warrior_focus.json" \
  --cards "$ROOT/cards.251332.enUS.json" \
  --output-dir "$RUN/data" \
  --manifest "$RUN/manifest.json" \
  --total-games 48 \
  --min-games-per-pair 48 \
  --seed 202609270001 \
  --teacher-samples 2 \
  --teacher-iterations 48 \
  --rollout-depth 3 \
  --collect-conditional-training \
  --conditional-training-min-visits 6 \
  --conditional-training-min-action-visits 1 \
  --conditional-training-repeats 4 \
  --conditional-training-iterations 32 \
  --conditional-training-max-branches 2 \
  --workers 4 \
  --parallel-jobs 1 \
  --job-timeout-seconds 3600 \
  --continue-on-error \
  --resume \
  --max-actions 1000 \
  --ruleset-label standard-live-20260927-dragon-warrior-v5-conditional \
  --card-vocab expanded-executable \
  >> "$RUN/generation.log" 2>&1

"$PYTHON" - "$RUN/manifest.json" <<'PY'
import json, sys
manifest = json.load(open(sys.argv[1], encoding="utf-8"))
failed = [job for job in manifest["jobs"] if job.get("status") == "failed"]
complete = [job for job in manifest["jobs"] if job.get("status") == "complete"]
print(f"generation summary: complete={len(complete)} failed={len(failed)}")
if failed or not complete:
    raise SystemExit("Refusing training: focused teacher data generation incomplete")
PY

echo "[$(date --iso-8601=seconds)] packing v5 decisions" | tee -a "$RUN/pipeline.log"
"$PYTHON" "$ROOT/scripts/pack_training_shards.py" \
  "$RUN/data" "$RUN/packed" --batch-size 512 --workers 4 \
  >> "$RUN/pack.log" 2>&1
"$PYTHON" "$ROOT/scripts/columnize_pt_shards.py" \
  "$RUN/packed" "$RUN/columnar" --workers 4 \
  >> "$RUN/columnize.log" 2>&1

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
  echo "Only $conditional_count conditional labels; refusing under-covered fine-tuning" >&2
  exit 3
fi

echo "[$(date --iso-8601=seconds)] NPU v5 fine-tuning begins; conditional_labels=$conditional_count" | tee -a "$RUN/pipeline.log"
npu-smi info > "$RUN/npu-before-train.log" 2>&1
"$PYTHON" "$ROOT/scripts/train_columnar_policy_value.py" \
  --data "$RUN"/columnar/*.pt \
  --output "$RUN/dragon-warrior-v5-conditional.pt" \
  --init-checkpoint "$BASE_RUN/standard127-conditional-v1.pt" \
  --device npu \
  --epochs 6 \
  --batch-size 256 \
  --learning-rate 0.00001 \
  --value-weight 0.15 \
  --conditional-policy-weight 10.0 \
  --checkpoint-every 2 \
  --seed 20260927 \
  > "$RUN/training.log" 2>&1

echo "[$(date --iso-8601=seconds)] v5 fine-tuning finished" | tee -a "$RUN/pipeline.log"
npu-smi info > "$RUN/npu-after-train.log" 2>&1

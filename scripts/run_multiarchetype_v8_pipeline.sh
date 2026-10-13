#!/usr/bin/env bash
set -eo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source /usr/local/Ascend/cann-9.0.0/set_env.sh
set -u
export TORCH_DEVICE_BACKEND_AUTOLOAD=0
PY=/usr/local/python3.11.14/bin/python3
PLAN=reports/multiarchetype-v8-plan.json
TRAIN_MANIFEST=reports/multiarchetype-v8-train-manifest.json

# Wait for the balanced training split to finish.  The manifest is resumable,
# so an interrupted run can be restarted without duplicating completed games.
while ! grep -q '"finished_at"' "$TRAIN_MANIFEST"; do
  sleep 60
done

"$PY" scripts/run_archetype_selfplay_plan.py \
  --plan "$PLAN" --split validation \
  --deck-config config/decks_20260924_flat.json \
  --output-dir reports/multiarchetype-v8-validation \
  --manifest reports/multiarchetype-v8-validation-manifest.json \
  --iterations 32 --samples 4 --rollout-depth 4 \
  --parallel-jobs 8 --timeout-seconds 1800 --resume \
  > reports/multiarchetype-v8-validation.log 2>&1

"$PY" scripts/run_archetype_selfplay_plan.py \
  --plan "$PLAN" --split unseen \
  --deck-config config/decks_20260924_flat.json \
  --output-dir reports/multiarchetype-v8-unseen \
  --manifest reports/multiarchetype-v8-unseen-manifest.json \
  --iterations 16 --samples 2 --rollout-depth 3 \
  --parallel-jobs 16 --timeout-seconds 1200 --resume \
  > reports/multiarchetype-v8-unseen.log 2>&1

mapfile -t TRAIN_DATA < <(find reports/multiarchetype-v8-train -name '*.jsonl.gz' -type f | sort)
mapfile -t VALIDATION_DATA < <(find reports/multiarchetype-v8-validation -name '*.jsonl.gz' -type f | sort)
if ((${#TRAIN_DATA[@]} == 0 || ${#VALIDATION_DATA[@]} == 0)); then
  echo 'no training or validation shards were generated' >&2
  exit 2
fi

"$PY" scripts/train_policy_value.py \
  --data "${TRAIN_DATA[@]}" \
  --validation-data "${VALIDATION_DATA[@]}" \
  --output reports/standard91-multiarchetype-v8.structured-v5.pt \
  --init-checkpoint reports/standard91-corrective-v5-highbudget-3/standard91-corrective-v6.pt \
  --device npu --architecture structured-v5 \
  --hidden-size 1024 --action-hidden-size 512 --residual-blocks 8 \
  --card-embedding-size 256 --epochs 12 --batch-size 128 \
  --learning-rate 1e-5 --weight-decay 1e-3 --gradient-clip 1.0 \
  --policy-target value-weighted-visits --policy-value-temperature 0.5 \
  --early-stopping-patience 3 --early-stopping-metric joint \
  --seed 202610090901 \
  > reports/standard91-multiarchetype-v8-training.log 2>&1

echo 'multiarchetype v8 pipeline complete'

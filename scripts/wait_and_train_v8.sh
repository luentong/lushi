#!/usr/bin/env bash
set -e
cd /workspace/hearthstone-agent
source /usr/local/Ascend/cann-9.0.0/set_env.sh
export TORCH_DEVICE_BACKEND_AUTOLOAD=0
while ! grep -q 'finished_at' reports/multiarchetype-v8-validation-manifest.json; do
  sleep 10
done
mapfile -t TRAIN_DATA < <(find reports/multiarchetype-v8-train -name '*.jsonl.gz' -type f | sort)
mapfile -t VALIDATION_DATA < <(find reports/multiarchetype-v8-validation -name '*.jsonl.gz' -type f | sort)
/usr/local/python3.11.14/bin/python3 scripts/train_policy_value.py \
  --data "${TRAIN_DATA[@]}" \
  --validation-data "${VALIDATION_DATA[@]}" \
  --output reports/standard91-multiarchetype-v8.structured-v5.pt \
  --device npu --architecture structured-v5 \
  --hidden-size 1024 --action-hidden-size 512 --residual-blocks 8 \
  --card-embedding-size 256 --epochs 12 --batch-size 128 \
  --learning-rate 1e-5 --weight-decay 1e-3 --gradient-clip 1.0 \
  --policy-target value-weighted-visits --policy-value-temperature 0.5 \
  --early-stopping-patience 3 --early-stopping-metric joint \
  --seed 202610090901

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

set +e +u
source /usr/local/Ascend/cann-9.0.0/set_env.sh
set -e -u
export TORCH_DEVICE_BACKEND_AUTOLOAD=0 PYTHONUNBUFFERED=1
export ASCEND_RT_VISIBLE_DEVICES="${ASCEND_RT_VISIBLE_DEVICES:-0}"

PYTHON_BIN="${PYTHON_BIN:-/usr/local/python3.11.14/bin/python3.11}"
BASE_COLUMNAR_DIR="${BASE_COLUMNAR_DIR:-reports/multiarchetype-jev-v7-20261010-columnar}"
R2_COLUMNAR_DIR="${R2_COLUMNAR_DIR:-reports/jev-v7-selfplay-r2-20261011-columnar}"
CHAMPION="${CHAMPION:-reports/jev-v7-20261010-training/model.direct-best.pt}"
OUTPUT_DIR="${OUTPUT_DIR:-reports/jev-v7-r2-distilled-20261012-training}"
TRAIN_EPOCHS="${TRAIN_EPOCHS:-8}"
LEARNING_RATE="${LEARNING_RATE:-5e-6}"
ANCHOR_POLICY_KL_WEIGHT="${ANCHOR_POLICY_KL_WEIGHT:-0.25}"
ANCHOR_VALUE_WEIGHT="${ANCHOR_VALUE_WEIGHT:-0.10}"

mapfile -t DATA_FILES < <(
  find "$BASE_COLUMNAR_DIR" "$R2_COLUMNAR_DIR" \
    -maxdepth 1 -name '*.pt' -size +0c | sort
)
if [[ ${#DATA_FILES[@]} -lt 2 ]]; then
  echo "not enough base + R2 schema-v7 shards" >&2
  exit 2
fi
if [[ ! -s "$CHAMPION" ]]; then
  echo "champion checkpoint is missing: $CHAMPION" >&2
  exit 2
fi

mkdir -p "$OUTPUT_DIR"
echo "starting champion-distilled JEV-v7 training with ${#DATA_FILES[@]} shards" >&2
echo "anchor policy KL=$ANCHOR_POLICY_KL_WEIGHT value=$ANCHOR_VALUE_WEIGHT" >&2

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
  --init-checkpoint "$CHAMPION" \
  --anchor-checkpoint "$CHAMPION" \
  --anchor-policy-kl-weight "$ANCHOR_POLICY_KL_WEIGHT" \
  --anchor-value-weight "$ANCHOR_VALUE_WEIGHT" \
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

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DATA_DIR="${DATA_DIR:-reports/multiarchetype-v8-hb-20261010}"
OUTPUT_DIR="${OUTPUT_DIR:-reports/jev-v6-hb-20261010-training}"
PYTHON_BIN="${PYTHON_BIN:-/usr/local/python3.11.14/bin/python3}"

mkdir -p "$OUTPUT_DIR"
mapfile -t DATA_FILES < <(
  find "$DATA_DIR" -maxdepth 1 -name '*.jsonl.gz' -size +0c | sort
)
if [[ ${#DATA_FILES[@]} -ne 256 ]]; then
  echo "expected 256 data shards, found ${#DATA_FILES[@]}" >&2
  exit 2
fi

exec "$PYTHON_BIN" scripts/train_policy_value.py \
  --data "${DATA_FILES[@]}" \
  --allow-mixed-rulesets \
  --output "$OUTPUT_DIR/model.pt" \
  --device npu \
  --architecture jev-v6-action-q \
  --hidden-size 512 \
  --action-hidden-size 256 \
  --entity-layers 2 \
  --entity-heads 8 \
  --card-embedding-size 128 \
  --epochs 16 \
  --batch-size 256 \
  --learning-rate 2e-5 \
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

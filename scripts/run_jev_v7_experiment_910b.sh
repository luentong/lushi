#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Make the training entry point self-contained.  Callers may be clean SSH
# shells without CANN library paths; set_env.sh also references optional
# variables, so source it with nounset temporarily disabled.
set +e +u
source /usr/local/Ascend/cann-9.0.0/set_env.sh
set -e -u
export TORCH_DEVICE_BACKEND_AUTOLOAD=0 PYTHONUNBUFFERED=1

# The input shards must have been regenerated after STATE_SCHEMA_VERSION=7;
# schema-v6 histograms cannot reconstruct per-slot card identities.
DATA_DIR="${DATA_DIR:-reports/multiarchetype-jev-v7-20261010-columnar}"
OUTPUT_DIR="${OUTPUT_DIR:-reports/jev-v7-20261010-training}"
PYTHON_BIN="${PYTHON_BIN:-/usr/local/python3.11.14/bin/python3}"
DATA_GLOB="${DATA_GLOB:-*.pt}"
INDEX_CACHE="${INDEX_CACHE:-$OUTPUT_DIR/decision-index-columnar.pt}"

mkdir -p "$OUTPUT_DIR"
mapfile -t DATA_FILES < <(
  find "$DATA_DIR" -maxdepth 1 -name "$DATA_GLOB" -size +0c | sort
)
if [[ ${#DATA_FILES[@]} -lt 1 ]]; then
  echo "no schema-v7 tensor shards found in $DATA_DIR" >&2
  exit 2
fi

echo "starting JEV-v7 training with ${#DATA_FILES[@]} shards on NPU" >&2

exec "$PYTHON_BIN" scripts/train_policy_value.py \
  --data "${DATA_FILES[@]}" \
  --allow-mixed-rulesets \
  --index-cache "$INDEX_CACHE" \
  --output "$OUTPUT_DIR/model.pt" \
  --device npu \
  --architecture jev-v7-action-q \
  --hidden-size 512 \
  --action-hidden-size 256 \
  --entity-layers 3 \
  --entity-heads 8 \
  --card-embedding-size 128 \
  --epochs 16 \
  --checkpoint-every 2 \
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

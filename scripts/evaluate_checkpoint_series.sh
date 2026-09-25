#!/usr/bin/env bash
# Evaluate a series of columnar policy/value checkpoints on one held-out split.
set -euo pipefail

if [[ $# -lt 4 ]]; then
  echo "usage: $0 RUN_DIR VALIDATION_MOD VALIDATION_REM EPOCH [EPOCH ...]" >&2
  exit 2
fi

run_dir=$1
validation_mod=$2
validation_rem=$3
shift 3

repo_root=$(cd "$(dirname "$0")/.." && pwd)
cd "$repo_root"

for epoch in "$@"; do
  echo "=== epoch${epoch} ==="
  PYTHONPATH="$repo_root/src" /usr/local/python3.11.14/bin/python3 \
    scripts/evaluate_columnar_policy_value.py \
    --checkpoint "$run_dir/standard127-smoke8-finetune-v1.epoch${epoch}.pt" \
    --data "$run_dir"/columnar/*.pt \
    --device npu \
    --batch-size 256 \
    --validation-mod "$validation_mod" \
    --validation-rem "$validation_rem"
done

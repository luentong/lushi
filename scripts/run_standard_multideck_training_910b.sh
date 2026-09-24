#!/usr/bin/env bash
set -o pipefail

ROOT="/workspace/hearthstone-agent"
PYTHON="/usr/local/python3.11.14/bin/python3.11"
RUN_TAG="${RUN_TAG:-20260920}"
LOG_DIR="$ROOT/reports/standard_multideck_${RUN_TAG}"
mkdir -p "$LOG_DIR"
source /usr/local/Ascend/cann-9.0.0/set_env.sh || true
set -euo pipefail
export PYTHONPATH="$ROOT/src:$ROOT/.deps"

cd "$ROOT"

# Gate the expensive pooled run on the three fast integration checks:
# target/effect legality, action-schema coverage, and one complete smoke game
# for every configured deck.  A failure leaves a JSON report and aborts before
# any training data is overwritten.
"$PYTHON" scripts/preflight_multideck.py \
  --cards cards.251332.enUS.json \
  --deck-config config/decks_20260920_multi.json \
  --iterations 4 \
  --output "$LOG_DIR/preflight.json" \
  > "$LOG_DIR/preflight.log" 2>&1

"$PYTHON" scripts/generate_multideck_policy_value_data.py \
  --config config/decks_20260920_multi.json \
  --cards cards.251332.enUS.json \
  --output-dir "$LOG_DIR/data" \
  --manifest "$LOG_DIR/manifest.json" \
  --total-games 1024 \
  --min-games-per-pair 2 \
  --seed 202609200000 \
  --teacher-samples 2 \
  --teacher-iterations 32 \
  --rollout-depth 3 \
  --workers 8 \
  --parallel-jobs 6 \
  > "$LOG_DIR/data_generation.json" 2>&1

"$PYTHON" scripts/train_policy_value.py \
  --device npu \
  --data "$LOG_DIR"/data/*.jsonl.gz \
  --output "$LOG_DIR/policy-value-standard-multideck-20260920-v1.pt" \
  --architecture structured-v5 \
  --hidden-size 1024 \
  --action-hidden-size 512 \
  --residual-blocks 8 \
  --card-embedding-size 256 \
  --epochs 20 \
  --batch-size 512 \
  --learning-rate 2e-4 \
  --weight-decay 1e-2 \
  --value-weight 0.15 \
  --policy-weight 1.0 \
  --validation-ratio 0.2 \
  --early-stopping-patience 4 \
  --early-stopping-metric joint \
  --policy-target visits \
  --seed 2026092001 \
  > "$LOG_DIR/training.json" 2>&1

date -Is > "$LOG_DIR/COMPLETE"

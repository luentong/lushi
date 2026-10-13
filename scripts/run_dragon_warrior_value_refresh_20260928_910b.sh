#!/usr/bin/env bash
set -euo pipefail

ROOT="/workspace/hearthstone-agent-v5-retrain-20260927"
BASE="$ROOT/reports/dragon-warrior-qtarget-20260927"
RUN="$ROOT/reports/dragon-warrior-value-refresh-20260928"
PYTHON="/usr/local/python3.11.14/bin/python3"
CONFIG="$ROOT/config/decks_20260927_dragon_warrior_focus.json"
CARDS="$ROOT/cards.251332.enUS.json"
INITIAL="$BASE/dragon-warrior-qtarget-conditional.epoch6.pt"

source /usr/local/Ascend/cann-9.0.0/set_env.sh >/dev/null 2>&1 || true
export LD_LIBRARY_PATH="/usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64/common:/usr/local/Ascend/driver/lib64/driver:/usr/local/Ascend/cann-9.0.0/aarch64-linux/lib64:${LD_LIBRARY_PATH:-}"
export PYTHONPATH="$ROOT/src:$ROOT/scripts:$ROOT/.deps:/workspace/hearthstone-agent/.deps${PYTHONPATH:+:$PYTHONPATH}"
mkdir -p "$RUN"

assert_npu0_idle() {
  # Avoid grep -q closing the pipe early: with pipefail enabled, npu-smi may
  # receive SIGPIPE and make an actually-idle device look busy.
  if ! npu-smi info | grep 'No running processes found in NPU 0' >/dev/null; then
    echo "NPU 0 is occupied; refusing to run inference/training" >&2
    exit 4
  fi
}

for required in "$CONFIG" "$CARDS" "$INITIAL" "$BASE/columnar"; do
  [[ -e "$required" ]] || { echo "Missing required input: $required" >&2; exit 2; }
done

generate() {
  local name="$1" games="$2" seed="$3"
  local out="$RUN/$name"
  "$PYTHON" "$ROOT/scripts/generate_multideck_policy_value_data.py" \
    --config "$CONFIG" --cards "$CARDS" \
    --output-dir "$out/data" --manifest "$out/manifest.json" \
    --total-games "$games" --min-games-per-pair "$games" \
    --seed "$seed" --teacher-samples 2 --teacher-iterations 48 \
    --rollout-depth 3 --policy-target-source visits \
    --workers 4 --parallel-jobs 1 --job-timeout-seconds 5400 \
    --max-actions 1000 --ruleset-label "dragon-warrior-value-refresh-20260928" \
    --card-vocab expanded-executable --resume
  "$PYTHON" - "$out/manifest.json" <<'PY'
import json, sys
manifest = json.load(open(sys.argv[1], encoding="utf-8"))
failed = [job for job in manifest["jobs"] if job.get("status") != "complete"]
if failed:
    raise SystemExit(f"incomplete generation manifest: {failed}")
print(f"generation verified: {manifest['total_games']} games")
PY
  if ! compgen -G "$out/columnar/*.pt" >/dev/null; then
    "$PYTHON" "$ROOT/scripts/pack_training_shards.py" \
      "$out/data" "$out/packed" --batch-size 512 --workers 4 \
      > "$out/pack.log" 2>&1
    "$PYTHON" "$ROOT/scripts/columnize_pt_shards.py" \
      "$out/packed" "$out/columnar" --workers 4 \
      > "$out/columnize.log" 2>&1
  else
    echo "[$(date --iso-8601=seconds)] reuse existing columnar shards for $name" | tee -a "$RUN/pipeline.log"
  fi
}

echo "[$(date --iso-8601=seconds)] independent training games start" | tee -a "$RUN/pipeline.log"
generate train-new 192 202609280001
echo "[$(date --iso-8601=seconds)] independent calibration games start" | tee -a "$RUN/pipeline.log"
generate calibration 48 2026092890000

mapfile -t CAL_SHARDS < <(find "$RUN/calibration/columnar" -maxdepth 1 -name '*.pt' -type f | sort)
mapfile -t NEW_SHARDS < <(find "$RUN/train-new/columnar" -maxdepth 1 -name '*.pt' -type f | sort)
mapfile -t OLD_SHARDS < <(find "$BASE/columnar" -maxdepth 1 -name '*.pt' -type f | sort)
[[ ${#CAL_SHARDS[@]} -gt 0 && ${#NEW_SHARDS[@]} -gt 0 && ${#OLD_SHARDS[@]} -gt 0 ]] || {
  echo "Missing columnar shards; refusing training" >&2; exit 3;
}

echo "[$(date --iso-8601=seconds)] evaluate baseline on untouched calibration games" | tee -a "$RUN/pipeline.log"
assert_npu0_idle
export ASCEND_RT_VISIBLE_DEVICES=0
"$PYTHON" "$ROOT/scripts/evaluate_columnar_policy_value.py" \
  --checkpoint "$INITIAL" --data "${CAL_SHARDS[@]}" \
  --device npu --validation-mod 1 --validation-rem 0 \
  > "$RUN/calibration-baseline-epoch6.json"

assert_npu0_idle
echo "[$(date --iso-8601=seconds)] value-emphasis fine-tune starts on NPU 0" | tee -a "$RUN/pipeline.log"
"$PYTHON" "$ROOT/scripts/train_columnar_policy_value.py" \
  --data "${OLD_SHARDS[@]}" "${NEW_SHARDS[@]}" \
  --output "$RUN/dragon-warrior-value-refresh.pt" \
  --init-checkpoint "$INITIAL" --device npu --epochs 8 --batch-size 256 \
  --learning-rate 0.000005 --value-weight 0.5 \
  --checkpoint-every 2 --seed 20260928 \
  > "$RUN/training.log" 2>&1

for epoch in 2 4 6 8; do
  ckpt="$RUN/dragon-warrior-value-refresh.epoch${epoch}.pt"
  if [[ -s "$ckpt" ]]; then
    assert_npu0_idle
    "$PYTHON" "$ROOT/scripts/evaluate_columnar_policy_value.py" \
      --checkpoint "$ckpt" --data "${CAL_SHARDS[@]}" \
      --device npu --validation-mod 1 --validation-rem 0 \
      > "$RUN/calibration-epoch${epoch}.json"
  fi
done
echo "[$(date --iso-8601=seconds)] all checkpoints evaluated; none auto-promoted" | tee -a "$RUN/pipeline.log"

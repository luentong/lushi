#!/usr/bin/env bash
source /usr/local/Ascend/cann-8.5.0/set_env.sh
set -euo pipefail
ROOT=/workspace/hearthstone-agent
PARENT=/workspace/hs_decision_quality_verify_20260928/reports
OLD=${PARENT}/strategy-loop-v2
RUN=${PARENT}/strategy-v3-20260929
RAW=${RUN}/raw
PACKED=${RUN}/packed
COLUMNAR=${RUN}/columnar
PYTHON=/usr/local/python3.11.14/bin/python3.11
GEN_PID=${GEN_PID:-3495458}

export PYTHONPATH="${ROOT}/src:${ROOT}/scripts"
mkdir -p "${RUN}"
cd "${ROOT}"

# The 127-deck high-budget teacher generation is already running in a
# separate session. Wait for it to finalize its manifest before packing.
while kill -0 "${GEN_PID}" 2>/dev/null; do sleep 30; done
MANIFEST=${RUN}/generation-manifest.json
if grep -q '"status": "running"' "${MANIFEST}"; then
  echo "generation exited with jobs still marked running; refusing to train" >&2
  exit 2
fi
FAILED=$(grep -c '"status": "failed"' "${MANIFEST}" || true)
echo "generation completed; failed jobs=${FAILED}" | tee "${RUN}/pipeline.status"

mkdir -p "${PACKED}" "${COLUMNAR}"
"${PYTHON}" scripts/pack_training_shards.py "${RAW}" "${PACKED}" \
  --batch-size 512 --workers 8 > "${RUN}/pack.log" 2>&1
"${PYTHON}" scripts/columnize_pt_shards.py "${PACKED}" "${COLUMNAR}" \
  --workers 8 > "${RUN}/columnize.log" 2>&1

BASE=("${OLD}"/columnar127-v6-effect/*.pt "${COLUMNAR}"/*.pt)
PRIORITY=("${OLD}"/columnar-qtarget-v6-effect-127vocab/*.pt)
TACTICAL=("${OLD}"/teacher-v6-effect-127vocab.pt)
HELDOUT_IDS=(dragon_hunter_user_02 mogasa_shaman_user_01)
HELDOUT=()
for SHARD in "${BASE[@]}"; do
  SHARD_NAME=${SHARD##*/}
  for DECK_ID in "${HELDOUT_IDS[@]}"; do
    if [[ "${SHARD_NAME}" == *"${DECK_ID}"* ]]; then
      HELDOUT+=("${SHARD}")
      break
    fi
  done
done

# Evaluate the existing candidate on the exact new held-out seed split before
# training. Then fit a same-capacity control and a wider/deeper model from
# scratch on identical data and seeds.
"${PYTHON}" scripts/evaluate_columnar_policy_value.py \
  --checkpoint "${OLD}/closed-loop-v2.epoch2.pt" \
  --data "${BASE[@]}" "${PRIORITY[@]}" "${TACTICAL[@]}" \
  --device npu --validation-mod 5 --validation-rem 0 \
  > "${RUN}/eval-old-v2-on-newdata.json" \
  2> "${RUN}/eval-old-v2-on-newdata.err"

"${PYTHON}" scripts/train_columnar_policy_value.py \
  --data "${BASE[@]}" \
  --priority-data "${PRIORITY[@]}" --priority-repeat 1 \
  --tactical-data "${TACTICAL[@]}" --tactical-repeat 16 \
  --output "${RUN}/strategy-v3-control-1024x8.pt" \
  --device npu --epochs 12 --batch-size 256 \
  --hidden-size 1024 --action-hidden-size 512 \
  --residual-blocks 8 --card-embedding-size 256 \
  --learning-rate 0.0001 --value-weight 0.15 \
  --opponent-value-weight 1.0 --action-value-weight 0.10 \
  --conditional-policy-weight 4 --checkpoint-every 2 \
  --exclude-deck-id "${HELDOUT_IDS[0]}" \
  --exclude-deck-id "${HELDOUT_IDS[1]}" \
  --exclude-mod 5 --exclude-rem 0 --seed 20260929 \
  > "${RUN}/train-control.log" 2>&1

"${PYTHON}" scripts/train_columnar_policy_value.py \
  --data "${BASE[@]}" \
  --priority-data "${PRIORITY[@]}" --priority-repeat 1 \
  --tactical-data "${TACTICAL[@]}" --tactical-repeat 16 \
  --output "${RUN}/strategy-v3-wide-deep-1536x12.pt" \
  --device npu --epochs 12 --batch-size 256 \
  --hidden-size 1536 --action-hidden-size 768 \
  --residual-blocks 12 --card-embedding-size 384 \
  --learning-rate 0.0001 --value-weight 0.15 \
  --opponent-value-weight 1.0 --action-value-weight 0.10 \
  --conditional-policy-weight 4 --checkpoint-every 2 \
  --exclude-deck-id "${HELDOUT_IDS[0]}" \
  --exclude-deck-id "${HELDOUT_IDS[1]}" \
  --exclude-mod 5 --exclude-rem 0 --seed 20260929 \
  > "${RUN}/train-wide-deep.log" 2>&1

for EPOCH in 2 4 6 8 10 12; do
  for MODEL in control-1024x8 wide-deep-1536x12; do
    "${PYTHON}" scripts/evaluate_columnar_policy_value.py \
      --checkpoint "${RUN}/strategy-v3-${MODEL}.epoch${EPOCH}.pt" \
      --data "${BASE[@]}" "${PRIORITY[@]}" "${TACTICAL[@]}" \
      --device npu --validation-mod 5 --validation-rem 0 \
      > "${RUN}/eval-${MODEL}-epoch${EPOCH}.json" \
      2> "${RUN}/eval-${MODEL}-epoch${EPOCH}.err"
    "${PYTHON}" scripts/evaluate_columnar_policy_value.py \
      --checkpoint "${RUN}/strategy-v3-${MODEL}.epoch${EPOCH}.pt" \
      --data "${HELDOUT[@]}" \
      --device npu --validation-mod 5 --validation-rem 0 \
      > "${RUN}/eval-${MODEL}-epoch${EPOCH}-unseen-decks.json" \
      2> "${RUN}/eval-${MODEL}-epoch${EPOCH}-unseen-decks.err"
  done
done

echo "training and fixed-seed evaluation complete; select promotion candidate only after paired-game/tactical gates" \
  | tee -a "${RUN}/pipeline.status"

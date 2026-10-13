#!/usr/bin/env bash
set -eu
cd /workspace/hs_observer_entity_20260929
test ! -e reports/kl-guard-ab-20261002
mkdir reports/kl-guard-ab-20261002
. /usr/local/Ascend/cann-8.5.0/set_env.sh >/dev/null 2>&1
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONHASHSEED=0
# Two bounded runs: same checkpoint, schedule, seeds and hyperparameters.
# Only the KL guard differs; neither output is automatically promoted.
for guard in minibatch probe; do
  device=npu:2
  if [ "$guard" = probe ]; then device=npu:4; fi
  nohup /usr/local/python3.11.14/bin/python3.11 -u scripts/train_entity_selfplay.py \
    --mode ppo --init-checkpoint reports/entity-scale-stage2-20261001/round-008-attempt1.pt \
    --output reports/kl-guard-ab-20261002/$guard/model.pt --device "$device" \
    --deck-config config/decks_20260925_smoke8.json --rounds 1 --games-per-round 128 \
    --rollout-workers 8 --inference-batch-size 16 --batch-size 32 --epochs 2 \
    --learning-rate 5e-6 --kl-guard "$guard" --kl-probe-size 128 --kl-check-interval 25 \
    --max-actions 400 --seed 203601010000 \
    > reports/kl-guard-ab-20261002/$guard.log 2>&1 < /dev/null &
  printf '%s PID: %s\n' "$guard" "$!"
done

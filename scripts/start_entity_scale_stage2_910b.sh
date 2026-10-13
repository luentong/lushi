#!/usr/bin/env bash
set -eu
cd /workspace/hs_observer_entity_20260929
test ! -e reports/entity-scale-stage2-20261001/pipeline.json
test ! -e reports/entity-scale-stage2-20261001.driver.log
test -f reports/entity-scale32768-20260930/round-032-attempt1.pt
. /usr/local/Ascend/cann-8.5.0/set_env.sh >/dev/null 2>&1
export PYTHONHASHSEED=0 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
# New stage: retain learned weights, reset Adam moments on the first round.
# Later rounds resume the stage's optimizer and grow its frozen opponent pool.
nohup /usr/local/python3.11.14/bin/python3.11 -u scripts/run_entity_scale.py \
  --init-checkpoint reports/entity-scale32768-20260930/round-032-attempt1.pt \
  --deck-config config/decks_20260925_smoke8.json \
  --output-dir reports/entity-scale-stage2-20261001 \
  --rounds 32 --games-per-round 1024 --learning-rate 5e-6 \
  --seed 203103010000 --dev-seed 203201010000 --confirm-seed 203301010000 \
  --device npu:2 --eval-device npu:3 \
  > reports/entity-scale-stage2-20261001.driver.log 2>&1 < /dev/null &
printf 'Coordinator PID: %s\n' "$!"

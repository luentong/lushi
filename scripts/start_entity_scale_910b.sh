#!/usr/bin/env bash
set -eu
cd /workspace/hs_observer_entity_20260929
test ! -e reports/entity-scale32768-20260930/pipeline.json
test ! -e reports/entity-scale32768-20260930.driver.log
. /usr/local/Ascend/cann-8.5.0/set_env.sh >/dev/null 2>&1
export PYTHONHASHSEED=0 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
nohup /usr/local/python3.11.14/bin/python3.11 -u scripts/run_entity_scale.py \
  --init-checkpoint reports/entity-pilot128-v2-repaired/entity-ppo.pt \
  --deck-config config/decks_20260925_smoke8.json \
  --output-dir reports/entity-scale32768-20260930 \
  --device npu:2 --eval-device npu:3 \
  > reports/entity-scale32768-20260930.driver.log 2>&1 < /dev/null &
printf 'Coordinator PID: %s\n' "$!"

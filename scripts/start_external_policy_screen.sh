#!/usr/bin/env bash
set -eu
cd /workspace/hs_observer_entity_20260929
test ! -e reports/policy-external-screen-20261002
test ! -e reports/policy-external-screen-20261002.log
. /usr/local/Ascend/cann-8.5.0/set_env.sh >/dev/null 2>&1
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONHASHSEED=0
nohup /usr/local/python3.11.14/bin/python3.11 -u scripts/screen_entity_external_opponents.py \
  --checkpoints reports/entity-scale32768-20260930/round-032-attempt1.pt \
  reports/entity-scale-stage2-20261001/round-008-attempt1.pt \
  --output reports/policy-external-screen-20261002 --device npu:3 \
  > reports/policy-external-screen-20261002.log 2>&1 < /dev/null &
printf 'Screen PID: %s\n' "$!"

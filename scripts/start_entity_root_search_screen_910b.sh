#!/usr/bin/env bash
set -eu
cd /workspace/hs_observer_entity_20260929
test ! -e reports/mixed-opponent-ab-20261002/search-vs-greedy
. /usr/local/Ascend/cann-8.5.0/set_env.sh >/dev/null 2>&1
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONHASHSEED=0
/usr/local/python3.11.14/bin/python3.11 -u scripts/screen_entity_root_search.py \
  --checkpoint reports/entity-scale-stage2-20261001/round-008-attempt1.pt \
  --deck-config config/decks_20260925_smoke8.json --device npu:2 --budget 32 \
  --seed 203901010000 --output reports/mixed-opponent-ab-20261002/search-vs-greedy

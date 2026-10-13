#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
REPORTS="${ROOT}/reports/strategy-loop-v1"
DATA=("${REPORTS}/columnar127-v6"/*.pt "${REPORTS}/columnar-qtarget-v6"/*.pt)

for epoch in 2 4 6 8; do
  "${PYTHON:-python3.11}" "${ROOT}/scripts/evaluate_columnar_policy_value.py" \
    --checkpoint "${REPORTS}/closed-loop-v1.epoch${epoch}.pt" \
    --data "${DATA[@]}" --device npu --validation-mod 5 --validation-rem 0 \
    > "${REPORTS}/eval-epoch${epoch}.json" \
    2> "${REPORTS}/eval-epoch${epoch}.err"
done

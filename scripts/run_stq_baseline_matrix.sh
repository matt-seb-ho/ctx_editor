#!/usr/bin/env bash
# STQ (single-turn) upper-bound matrix.
#
# Concurrency model: STQ requests are very fast (~1-3s each) so a high
# max_concurrent can easily burst above per-model RPM caps. After hitting
# 429s on the first attempt with mc=20-30, we now use:
#   - gpt-5.4 (OpenAI, huge quota): mc=20, runs in parallel
#   - Foundry models (single 250 RPM bucket per model): mc=3 each, and the
#     three foundry pipelines are SERIALIZED (one-at-a-time) so they don't
#     contend for the foundry endpoint.
#
# Tasks × runs × models = 4 × 3 × 4 = 48 cells, ~30-90s each.

set -uo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
[[ -f .env ]] && { set -a; source .env; set +a; }

OUT_ROOT="outputs/post_neurips_lic_vanilla_stq"
LOG_DIR="${OUT_ROOT}/logs"
mkdir -p "$LOG_DIR"

TASKS=(math_v2 code_v2 database_v2 actions_v2)

run_model() {
    local model="$1" lb="$2" mc="$3"
    python scripts/run_stq_baseline.py \
        --model "${model}" \
        --load-balancer "${lb}" \
        --tasks "${TASKS[@]}" \
        --n-runs 3 \
        --subset htn50_52 \
        --max-concurrent "${mc}" \
        --output-root "${OUT_ROOT}"
}

# Pipeline A: gpt-5.4 in parallel with everything else (separate endpoint pool).
run_model gpt5_4 multi_endpoint 20 > "${LOG_DIR}/stq_gpt5_4.log" 2>&1 &
pa=$!

# Pipeline B: Foundry models, one at a time, low concurrency.
(
    run_model deepseek_v4_flash_foundry multi_endpoint_foundry 3 > "${LOG_DIR}/stq_deepseek.log" 2>&1
    run_model kimi_k2_6_foundry         multi_endpoint_foundry 3 > "${LOG_DIR}/stq_kimi.log"     2>&1
    run_model gpt5_5_foundry            multi_endpoint_foundry 3 > "${LOG_DIR}/stq_gpt5_5.log"   2>&1
) &
pb=$!

echo "Launched STQ pipelines: gpt5_4(parallel)=${pa}  foundry-serialized=${pb}"
wait "${pa}" "${pb}"
echo "All STQ runs done."

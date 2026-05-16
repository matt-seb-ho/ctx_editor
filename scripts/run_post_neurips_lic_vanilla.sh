#!/usr/bin/env bash
# Post-NeurIPS LiC vanilla baseline runs.
#
# Matrix:
#   domains:   math_v2, code_v2, database_v2, actions_v2 (new — bakes the
#              'accumulate' instruction into the actions system prompt)
#   models:    gpt5_4, deepseek_v4_flash_foundry, kimi_k2_6_foundry,
#              gpt5_5_foundry  (Phi-4 dropped — 1 RPM is too slow)
#   strategy:  baseline (no context modification)
#   user_mode: sharded (LiC-identical)
#   user sim:  gpt-4o-mini (default in each model config)
#   data:      data/htn50_52_{task}_subset.json
#   N runs:    3 sequential ctx-editor invocations per (model, domain)
#
# Concurrency strategy:
#   Each assistant model has its own RPM bucket at its endpoint, so running
#   the four models in parallel pipelines does NOT compete on rate limit:
#     gpt-5.4              OpenAI (dl-openai-1=10000 RPM, dl-openai-3=2500)
#     DeepSeek-V4-Flash    Foundry (250 RPM)
#     Kimi-K2.6            Foundry (100 RPM)
#     gpt-5.5              Foundry (250 RPM)
#   Within a pipeline we use a generous process-level max_concurrent; the
#   load balancer caps at the per-model RPM if we'd exceed it.
#
# Robustness:
#   - Each ctx-editor run writes incremental traces into its own
#     outputs/{date}/{time}/ directory, so partial progress survives a crash.
#   - The launcher uses `set +e`-style continue-on-fail per invocation.
#   - All output dirs and per-run summaries are appended to the results MD.
#
# Usage:
#   bash scripts/run_post_neurips_lic_vanilla.sh           # full matrix
#   bash scripts/run_post_neurips_lic_vanilla.sh gpt5_4
#   bash scripts/run_post_neurips_lic_vanilla.sh deepseek
#   bash scripts/run_post_neurips_lic_vanilla.sh kimi
#   bash scripts/run_post_neurips_lic_vanilla.sh gpt5_5
#   bash scripts/run_post_neurips_lic_vanilla.sh smoke    # tiny smoke test

set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Load .env so AZURE keys/etc. are available.
if [[ -f "$PROJECT_ROOT/.env" ]]; then
    set -a
    # shellcheck source=/dev/null
    source "$PROJECT_ROOT/.env"
    set +a
fi

FILTER="${1:-all}"
RUN_TAG="post_neurips_lic_vanilla"
RESULTS_MD="$PROJECT_ROOT/docs/reports/${RUN_TAG}.md"
ROWS_DIR="$PROJECT_ROOT/outputs/${RUN_TAG}/rows"
LAUNCHER_LOG_DIR="$PROJECT_ROOT/outputs/${RUN_TAG}/logs"
mkdir -p "$LAUNCHER_LOG_DIR" "$ROWS_DIR"

DOMAINS=(math_v2 code_v2 database_v2 actions_v2)
declare -A DATA_FILE
DATA_FILE[math_v2]="data/htn50_52_math_subset.json"
DATA_FILE[code_v2]="data/htn50_52_code_subset.json"
DATA_FILE[database_v2]="data/htn50_52_database_subset.json"
DATA_FILE[actions_v2]="data/htn50_52_actions_subset.json"

N_RUNS=3

# ─── helpers ────────────────────────────────────────────────────────────────
init_results_md() {
    if [[ -f "${RESULTS_MD}" ]]; then return; fi
    cat > "${RESULTS_MD}" <<EOF
# Post-NeurIPS LiC Vanilla Baseline Runs

**Started**: $(date -Iseconds)
**Strategy**: baseline (no context modification)
**User simulator**: gpt-4o-mini
**Subset**: htn50_52 (50/44/50/50 problems for math/code/database/actions)
**Runs per (model, domain)**: ${N_RUNS} sequential ctx-editor invocations
**User mode**: sharded (LiC-identical)
**Task evaluators**: math_v2, code_v2, database_v2, actions_v2 (new, includes 'accumulate' instruction)

## Models

| Model | Config | Endpoint pool | Per-model RPM cap |
|---|---|---|---|
| gpt-5.4 | \`gpt5_4\` | OpenAI (dl-openai-1/3) | 10000 / 2500 |
| DeepSeek-V4-Flash | \`deepseek_v4_flash_foundry\` | Foundry (mgalley-foundry2) | 250 |
| Kimi-K2.6 | \`kimi_k2_6_foundry\` | Foundry (mgalley-foundry2) | 100 |
| gpt-5.5 | \`gpt5_5_foundry\` | Foundry (mgalley-foundry2) | 250 |

Phi-4 was excluded — its Foundry quota is 1 RPM, making the matrix infeasible.

## Per-run table

Each row = one ctx-editor invocation. Same (model, domain) appears ${N_RUNS}× with different run_idx.
Aggregate "(model, domain) means over the N runs" lives below.

| Started | Model | Task | Run | rc | Wall | Accuracy | Cost | Avg Turns | Output Dir | Log |
|---|---|---|---|---|---|---|---|---|---|---|
EOF
}

# Append accumulated row files to the table (idempotent — flushes ROWS_DIR/*.row).
flush_rows() {
    init_results_md
    shopt -s nullglob
    local row_files=("$ROWS_DIR"/*.row)
    if (( ${#row_files[@]} > 0 )); then
        # Sort by mtime so order matches completion order.
        ls -t "${row_files[@]}" 2>/dev/null | tac | xargs -r cat >> "${RESULTS_MD}"
        rm -f "${row_files[@]}"
    fi
}

run_one() {
    local model="$1"
    local task="$2"
    local lb="$3"
    local mc="$4"
    local run_idx="$5"
    local label="${model}__${task}__run${run_idx}"
    local logfile="${LAUNCHER_LOG_DIR}/${label}.log"

    local data_file="${DATA_FILE[$task]}"
    local start_ts start_human
    start_ts="$(date +%s)"
    start_human="$(date -Iseconds)"

    echo "[$(date +%H:%M:%S)] BEGIN ${label}  lb=${lb} mc=${mc} data=${data_file}"

    local exp_name="baseline_sharded_${model}_${task}_run${run_idx}"

    ctx-editor \
        experiment=baseline \
        model="${model}" \
        task="${task}" \
        task.data_file="${data_file}" \
        user_mode=sharded \
        load_balancer="${lb}" \
        execution.max_concurrent="${mc}" \
        experiment_name="${exp_name}" \
        logging.verbose=false \
        metadata.branch="${RUN_TAG}" \
        > "${logfile}" 2>&1
    local rc=$?

    local end_ts elapsed
    end_ts="$(date +%s)"
    elapsed=$((end_ts - start_ts))

    local out_dir acc_line cost_line turns_line
    out_dir="$(grep -oE 'outputs/[0-9-]+/[0-9-]+' "${logfile}" | head -1 || true)"
    acc_line="$(grep -E '^Accuracy:' "${logfile}" | head -1 | sed 's/^Accuracy: //' || true)"
    cost_line="$(grep -E '^Total Cost:' "${logfile}" | head -1 | sed 's/^Total Cost: //' || true)"
    turns_line="$(grep -E '^Average Turns:' "${logfile}" | head -1 | sed 's/^Average Turns: //' || true)"

    if [[ $rc -eq 0 ]]; then
        echo "[$(date +%H:%M:%S)] DONE  ${label}  (${elapsed}s)  ${acc_line}"
    else
        echo "[$(date +%H:%M:%S)] FAIL  ${label}  (rc=${rc}, ${elapsed}s)  see ${logfile}"
    fi

    # Write a one-line row file. Flushed into the table by flush_rows().
    {
        printf '| %s | %s | %s | %s | %s | %ss | %s | %s | %s | `%s` | `%s` |\n' \
            "${start_human}" "${model}" "${task}" "${run_idx}" "${rc}" "${elapsed}" \
            "${acc_line}" "${cost_line}" "${turns_line}" "${out_dir:-?}" "${label}.log"
    } > "${ROWS_DIR}/${start_ts}_${label}.row"
}

# ─── pipelines (each iterates 4 domains × N_RUNS sequentially) ──────────────
pipeline_for() {
    local model="$1"
    local lb="$2"
    local mc="$3"
    for domain in "${DOMAINS[@]}"; do
        for ((i=1; i<=N_RUNS; i++)); do
            run_one "${model}" "${domain}" "${lb}" "${mc}" "${i}"
            flush_rows
        done
    done
}

pipeline_smoke() {
    init_results_md
    for entry in \
        "gpt5_4 multi_endpoint 8" \
        "deepseek_v4_flash_foundry multi_endpoint_foundry 4" \
        "kimi_k2_6_foundry multi_endpoint_foundry 4" \
        "gpt5_5_foundry multi_endpoint_foundry 4"; do
        # shellcheck disable=SC2086
        set -- $entry
        local model="$1" lb="$2" mc="$3"
        local label="${model}__math_v2__smoke"
        local logfile="${LAUNCHER_LOG_DIR}/${label}.log"
        echo "[$(date +%H:%M:%S)] SMOKE ${model} math_v2 (limit=2, mc=${mc})"
        ctx-editor \
            experiment=baseline \
            model="${model}" \
            task=math_v2 \
            task.data_file=data/htn50_52_math_subset.json \
            task.limit=2 \
            user_mode=sharded \
            load_balancer="${lb}" \
            execution.max_concurrent="${mc}" \
            experiment_name="smoke_${model}_math_v2" \
            > "${logfile}" 2>&1
        local rc=$?
        echo "  rc=${rc}; tail of log:"
        tail -n 6 "${logfile}" | sed 's/^/    /'
    done
}

trap flush_rows EXIT

case "${FILTER}" in
    smoke)
        pipeline_smoke
        ;;
    gpt5_4)
        init_results_md
        pipeline_for gpt5_4 multi_endpoint 30
        ;;
    deepseek)
        init_results_md
        pipeline_for deepseek_v4_flash_foundry multi_endpoint_foundry 30
        ;;
    kimi)
        init_results_md
        pipeline_for kimi_k2_6_foundry multi_endpoint_foundry 20
        ;;
    gpt5_5)
        init_results_md
        pipeline_for gpt5_5_foundry multi_endpoint_foundry 30
        ;;
    all)
        init_results_md
        # Run each model pipeline as its own background process. Different models
        # have separate rate-limit buckets at their endpoints, so they don't
        # contend.
        pipeline_for gpt5_4                    multi_endpoint         30 \
            >  "${LAUNCHER_LOG_DIR}/_pipeline_gpt5_4.log"    2>&1 &
        pid_a=$!
        pipeline_for deepseek_v4_flash_foundry multi_endpoint_foundry 30 \
            >  "${LAUNCHER_LOG_DIR}/_pipeline_deepseek.log"  2>&1 &
        pid_b=$!
        pipeline_for kimi_k2_6_foundry         multi_endpoint_foundry 20 \
            >  "${LAUNCHER_LOG_DIR}/_pipeline_kimi.log"      2>&1 &
        pid_c=$!
        pipeline_for gpt5_5_foundry            multi_endpoint_foundry 30 \
            >  "${LAUNCHER_LOG_DIR}/_pipeline_gpt5_5.log"    2>&1 &
        pid_d=$!
        echo "Launched pipelines: gpt5_4=${pid_a} deepseek=${pid_b} kimi=${pid_c} gpt5_5=${pid_d}"
        wait "${pid_a}" "${pid_b}" "${pid_c}" "${pid_d}"
        ;;
    *)
        echo "Usage: $0 [all|gpt5_4|deepseek|kimi|gpt5_5|smoke]"
        exit 1
        ;;
esac

echo "All done. Results table: ${RESULTS_MD}"

#!/usr/bin/env bash
# Phase 3a — CollabLLM N=3 redo with the Phase 1/2 winning AC3 variant.
# Strategies: baseline, AO, Augment (v8), Reset (v8) — winning method.
# Tasks: math-hard, bigcodebench.
# Model: DeepSeek-V4-Flash (mirrors Phase 1).
# N=3 sampling reps per (strategy, task) cell.

set -uo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
[[ -f .env ]] && { set -a; source .env; set +a; }

RUN_TAG="post_neurips_ac3_phase3_collabllm"
OUT_ROOT="outputs/${RUN_TAG}"
LOG_DIR="${OUT_ROOT}/logs"
mkdir -p "$LOG_DIR"

MODEL=deepseek_v4_flash_foundry
LB=multi_endpoint_foundry
MC=8

STRATEGIES=(collabllm_baseline collabllm_assistant_omit collabllm_ac3_augment_v8 collabllm_ac3_reset_v8)
TASKS=(math-hard bigcodebench)
REPS=(1 2 3)

run_one() {
    local strategy="$1" dataset="$2" rep="$3"
    local label="${strategy}__${dataset}__rep${rep}"
    local logfile="${LOG_DIR}/${label}.log"
    local start_ts; start_ts="$(date +%s)"
    local out_run_name="${strategy}_${dataset}_rep${rep}_${start_ts}"
    local out_override="${OUT_ROOT}/${out_run_name}"

    local task_name
    if [[ "$dataset" == "math-hard" ]]; then task_name=collabllm_math
    else task_name=collabllm_code; fi

    echo "[$(date +%H:%M:%S)] BEGIN ${label}"
    ctx-editor-collabllm \
        experiment="${strategy}" \
        model="${MODEL}" \
        load_balancer="${LB}" \
        task.name="${task_name}" \
        task.dataset_name="${dataset}" \
        task.limit=20 \
        execution.max_concurrent="${MC}" \
        seed="$((42 + rep))" \
        experiment_name="${out_run_name}" \
        logging.output_dir="${out_override}" \
        metadata.branch="${RUN_TAG}" \
        > "${logfile}" 2>&1
    local rc=$?
    local elapsed=$(( $(date +%s) - start_ts ))
    local acc; acc="$(grep -E '^Accuracy:' "${logfile}" | head -1 | sed 's/^Accuracy: //')"
    if [[ $rc -eq 0 ]]; then
        echo "[$(date +%H:%M:%S)] DONE  ${label}  (${elapsed}s)  ${acc}"
    else
        echo "[$(date +%H:%M:%S)] FAIL  ${label}  (rc=${rc}, ${elapsed}s)  see ${logfile}"
    fi
}

for strategy in "${STRATEGIES[@]}"; do
    for dataset in "${TASKS[@]}"; do
        for rep in "${REPS[@]}"; do
            run_one "${strategy}" "${dataset}" "${rep}"
        done
    done
done

echo "Phase 3a (CollabLLM) all done."

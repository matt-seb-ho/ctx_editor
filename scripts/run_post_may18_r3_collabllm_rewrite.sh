#!/usr/bin/env bash
# CollabLLM × Rewrite (compaction) — fill in the Rewrite row.
# Run on DeepSeek-V4-Flash (assistant + user-sim) to match R2 setup.
# 2 cells × 20 problems each. ~25-30 min wall.

set -uo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
[[ -f .env ]] && { set -a; source .env; set +a; }

RUN_TAG="post_may18_r3_collabllm_fills"
OUT_ROOT="outputs/${RUN_TAG}"
LOG_DIR="${OUT_ROOT}/logs"
mkdir -p "$LOG_DIR"

MODEL=deepseek_v4_flash_user_deepseek
LB=multi_endpoint_foundry
MC=4

STRATEGY=collabllm_compaction
TASKS=(math-hard bigcodebench)
SEED=43

run_one() {
    local dataset="$1"
    local label="deepseek__${STRATEGY}__${dataset}"
    local logfile="${LOG_DIR}/${label}.log"
    local start_ts; start_ts="$(date +%s)"
    local out_run_name="${STRATEGY}_deepseek_${dataset}_${start_ts}"
    local out_override="${OUT_ROOT}/${out_run_name}"

    local task_name
    if [[ "$dataset" == "math-hard" ]]; then task_name=collabllm_math
    else task_name=collabllm_code; fi

    echo "[$(date +%H:%M:%S)] BEGIN ${label}"
    python -m ctx_editor.run_collabllm \
        experiment="${STRATEGY}" \
        model="${MODEL}" \
        load_balancer="${LB}" \
        task.name="${task_name}" \
        task.dataset_name="${dataset}" \
        task.limit=20 \
        execution.max_concurrent="${MC}" \
        seed="${SEED}" \
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
        echo "[$(date +%H:%M:%S)] FAIL  ${label}  (rc=${rc}, ${elapsed}s) — see ${logfile}"
    fi
}

PIDS=()
for dataset in "${TASKS[@]}"; do
    run_one "$dataset" &
    PIDS+=($!)
done
for pid in "${PIDS[@]}"; do
    wait "$pid"
done
echo "CollabLLM Rewrite (DeepSeek) fills done."

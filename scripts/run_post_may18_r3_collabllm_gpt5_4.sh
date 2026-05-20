#!/usr/bin/env bash
# CollabLLM mega-table fill: gpt-5.4 assistant only (Kimi will follow
# in its own launcher). Throttled to MC=4 to avoid foundry user-sim
# token-rate exhaustion while Kimi LiC retry is still in flight.

set -uo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
[[ -f .env ]] && { set -a; source .env; set +a; }

RUN_TAG="post_may18_r3_collabllm_fills"
OUT_ROOT="outputs/${RUN_TAG}"
LOG_DIR="${OUT_ROOT}/logs"
mkdir -p "$LOG_DIR"

MODEL=gpt5_4
LB=multi_endpoint_with_foundry   # combines Azure OAI (gpt-5.4) + Foundry (DeepSeek user-sim)
MC=4

STRATEGIES=(collabllm_baseline collabllm_assistant_omit collabllm_ac3_augment_v8 collabllm_ac3_reset_v8)
TASKS=(math-hard bigcodebench)
SEED=43

run_one() {
    local strategy="$1" dataset="$2"
    local label="gpt5_4__${strategy}__${dataset}"
    local logfile="${LOG_DIR}/${label}.log"
    local start_ts; start_ts="$(date +%s)"
    local out_run_name="${strategy}_gpt5_4_${dataset}_${start_ts}"
    local out_override="${OUT_ROOT}/${out_run_name}"

    local task_name
    if [[ "$dataset" == "math-hard" ]]; then task_name=collabllm_math
    else task_name=collabllm_code; fi

    echo "[$(date +%H:%M:%S)] BEGIN ${label}"
    python -m ctx_editor.run_collabllm \
        experiment="${strategy}" \
        model="${MODEL}" \
        load_balancer="${LB}" \
        model.user.model=DeepSeek-V4-Flash \
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

# Parallelize across (strategy, task) within gpt-5.4
PIDS=()
for strategy in "${STRATEGIES[@]}"; do
    for dataset in "${TASKS[@]}"; do
        run_one "$strategy" "$dataset" &
        PIDS+=($!)
    done
done
for pid in "${PIDS[@]}"; do
    wait "$pid"
done
echo "CollabLLM gpt-5.4 fills done."

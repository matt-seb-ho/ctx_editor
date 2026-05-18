#!/usr/bin/env bash
# Post-NeurIPS R2 — CollabLLM with stronger user simulator.
#
# Phase 3a tested CollabLLM with gpt-4o-mini as the user simulator. The
# resulting conversations on bigcodebench drift wildly off-spec (the user
# sim never communicates the actual `task_func` signature, so the
# assistant produces unrelated code). All-zero pass-rate on Phase 3a is a
# user-sim quality issue, not an eval bug.
#
# This run swaps in DeepSeek-V4-Flash as the user simulator and reruns
# baseline + AC3-Reset + AC3-Augment on both math-hard and bigcodebench.
# 2 reps × 20 = 40 problems per cell. ~2h estimated.

set -uo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
[[ -f .env ]] && { set -a; source .env; set +a; }

RUN_TAG="post_neurips_r2_collabllm_user_deepseek"
OUT_ROOT="outputs/${RUN_TAG}"
LOG_DIR="${OUT_ROOT}/logs"
mkdir -p "$LOG_DIR"

MODEL=deepseek_v4_flash_user_deepseek
LB=multi_endpoint_foundry
MC=15

# R2 leaner sweep: bigcodebench is the diagnostic priority (testing whether
# stronger user-sim recovers the all-zero scores). math-hard kept too as a
# sanity check that we don't regress where Phase 3a worked.
STRATEGIES=(collabllm_baseline collabllm_assistant_omit collabllm_ac3_reset_v8)
TASKS=(bigcodebench math-hard)
REPS=(1)

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
    python -m ctx_editor.run_collabllm \
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

# Run cells in parallel (3 strategies x 2 tasks = 6 cells) to fully exploit
# DeepSeek-V4-Flash's 250 RPM quota. Each cell is its own process; the
# foundry endpoint will rate-limit across processes automatically.
PIDS=()
for strategy in "${STRATEGIES[@]}"; do
    for dataset in "${TASKS[@]}"; do
        for rep in "${REPS[@]}"; do
            run_one "${strategy}" "${dataset}" "${rep}" &
            PIDS+=($!)
        done
    done
done
echo "Launched ${#PIDS[@]} cells in parallel; pids=${PIDS[*]}"
for pid in "${PIDS[@]}"; do
    wait "$pid"
done

echo "Post-NeurIPS R2 CollabLLM (user-sim=DeepSeek) all done."

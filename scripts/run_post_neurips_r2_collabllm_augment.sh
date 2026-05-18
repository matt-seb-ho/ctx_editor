#!/usr/bin/env bash
# Fill in the AC3-Augment cells for the R2 CollabLLM batch.
#
# We initially excluded Augment to keep scope manageable. Now that the
# user-sim swap result is so dramatic (math-hard 30%→95%), it's worth
# completing the 4-strategy comparison to see whether Augment also
# recovers (Phase 3a had it as the worst performer on math-hard).

set -uo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
[[ -f .env ]] && { set -a; source .env; set +a; }

RUN_TAG="post_neurips_r2_collabllm_user_deepseek"   # land in same dir as main batch
OUT_ROOT="outputs/${RUN_TAG}"
LOG_DIR="${OUT_ROOT}/logs"
mkdir -p "$LOG_DIR"

MODEL=deepseek_v4_flash_user_deepseek
LB=multi_endpoint_foundry
MC=15

STRATEGIES=(collabllm_ac3_augment_v8)
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
        metadata.branch="${RUN_TAG}_augment" \
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

PIDS=()
for strategy in "${STRATEGIES[@]}"; do
    for dataset in "${TASKS[@]}"; do
        for rep in "${REPS[@]}"; do
            run_one "${strategy}" "${dataset}" "${rep}" &
            PIDS+=($!)
        done
    done
done
echo "Launched ${#PIDS[@]} augment cells; pids=${PIDS[*]}"
for pid in "${PIDS[@]}"; do
    wait "$pid"
done

echo "Augment fill-in done."

#!/usr/bin/env bash
# Re-run Kimi LiC Rewrite cells with throttled concurrency. The first
# attempt saturated foundry token quota; most cells had 30-49/50 samples
# excluded as errors. Re-launching with max_concurrent=4 per cell, no
# parallel cells (one task at a time × 3 convs in parallel = 3 cells).

set -uo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
[[ -f .env ]] && { set -a; source .env; set +a; }

RUN_TAG="post_may18_r3_lic_rewrite_kimi_retry"
OUT_ROOT="outputs/${RUN_TAG}"
LOG_DIR="${OUT_ROOT}/logs"
mkdir -p "$LOG_DIR"

MODEL=kimi_k2_6_foundry
LB=multi_endpoint_foundry
MC=4

TASKS=(math_v2 code_v2 database_v2 actions_v2)
CONVS=(0 1 2)

declare -A DATA_FILE
DATA_FILE[math_v2]="data/htn50_52_math_subset.json"
DATA_FILE[code_v2]="data/htn50_52_code_subset.json"
DATA_FILE[database_v2]="data/htn50_52_database_subset.json"
DATA_FILE[actions_v2]="data/htn50_52_actions_subset.json"

run_one() {
    local task="$1" conv="$2"
    local exp_name="ac3_rewrite_lic"
    local label="${MODEL}__${exp_name}__${task}__conv${conv}__retry"
    local logfile="${LOG_DIR}/${label}.log"
    local start_ts; start_ts="$(date +%s)"
    local out_run_name="${exp_name}_${MODEL}_${task}_conv${conv}_${start_ts}"
    local out_override="${OUT_ROOT}/${out_run_name}"

    local replay_source="data/valid_prefixes_htn50_52/${MODEL}/${task}/conv${conv}"
    [[ -d "$replay_source" ]] || { echo "[$(date +%H:%M:%S)] SKIP ${label}"; return; }

    echo "[$(date +%H:%M:%S)] BEGIN ${label}"
    ctx-editor \
        experiment="${exp_name}" \
        model="${MODEL}" \
        load_balancer="${LB}" \
        task="${task}" \
        task.data_file="${DATA_FILE[$task]}" \
        user_mode=sharded \
        execution.max_concurrent="${MC}" \
        execution.replay_source="${replay_source}" \
        execution.replay_turns=1 \
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

# Serial across tasks, parallel across convs within task. Keeps to 3 cells
# × 4 max_concurrent = 12 simultaneous foundry calls.
for task in "${TASKS[@]}"; do
    echo "=== Task: ${task} ==="
    PIDS=()
    for conv in "${CONVS[@]}"; do
        run_one "${task}" "${conv}" &
        PIDS+=($!)
    done
    for pid in "${PIDS[@]}"; do
        wait "$pid"
    done
done

echo "Kimi LiC Rewrite retry done."

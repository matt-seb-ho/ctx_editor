#!/usr/bin/env bash
# Re-launch just the gpt-5.4 LiC Rewrite cells (the first attempt failed
# because we passed load_balancer=multi_endpoint_foundry, which doesn't
# host gpt-5.4). gpt-5.4 routes via multi_endpoint.

set -uo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
[[ -f .env ]] && { set -a; source .env; set +a; }

RUN_TAG="post_may18_r3_lic_rewrite_fills"
OUT_ROOT="outputs/${RUN_TAG}"
LOG_DIR="${OUT_ROOT}/logs"
mkdir -p "$LOG_DIR"

MODEL=gpt5_4
LB=multi_endpoint
MC=12

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
    if [[ ! -d "$replay_source" ]]; then
        echo "[$(date +%H:%M:%S)] SKIP ${label} — no replay source at ${replay_source}"
        return
    fi

    echo "[$(date +%H:%M:%S)] BEGIN ${label}"
    ctx-editor \
        experiment="${exp_name}" \
        model="${MODEL}" \
        task="${task}" \
        task.data_file="${DATA_FILE[$task]}" \
        user_mode=sharded \
        load_balancer="${LB}" \
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

PIDS=()
for task in "${TASKS[@]}"; do
    for conv in "${CONVS[@]}"; do
        run_one "${task}" "${conv}" &
        PIDS+=($!)
    done
done
echo "Launched ${#PIDS[@]} gpt-5.4 Rewrite cells; pids=${PIDS[*]}"
for pid in "${PIDS[@]}"; do
    wait "$pid"
done
echo "gpt-5.4 LiC Rewrite retries done."

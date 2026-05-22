#!/usr/bin/env bash
# R6 B1: full 12-cell sweep on DSV4F using the A4 GEPA winner (v10).
# Re-confirms whether the +1 problem GEPA improvement on math conv0
# (12-problem mini-eval) generalizes to the full sweep. ~20-25 min wall.

set -uo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
[[ -f .env ]] && { set -a; source .env; set +a; }

RUN_TAG="post_may18_r6_a4_gepa_sweep"
OUT_ROOT="outputs/${RUN_TAG}"
LOG_DIR="${OUT_ROOT}/logs"
mkdir -p "$LOG_DIR"

EXP_NAME=ac3_rewrite_v10_gepa_lic
MODEL=deepseek_v4_flash_foundry
LB=multi_endpoint_foundry
MC=4
MAX_PARALLEL=4

TASKS=(math_v2 code_v2 database_v2 actions_v2)
CONVS=(0 1 2)

declare -A DATA_FILE
DATA_FILE[math_v2]="data/htn50_52_math_subset.json"
DATA_FILE[code_v2]="data/htn50_52_code_subset.json"
DATA_FILE[database_v2]="data/htn50_52_database_subset.json"
DATA_FILE[actions_v2]="data/htn50_52_actions_subset.json"

run_one() {
    local task="$1" conv="$2"
    local label="${EXP_NAME}__${task}__conv${conv}"
    local logfile="${LOG_DIR}/${label}.log"
    local start_ts; start_ts="$(date +%s)"
    local out_run_name="${EXP_NAME}_${task}_conv${conv}_${start_ts}"
    local out_override="${OUT_ROOT}/${out_run_name}"

    local replay_source="data/valid_prefixes_htn50_52/${MODEL}/${task}/conv${conv}"
    [[ -d "$replay_source" ]] || { echo "[$(date +%H:%M:%S)] SKIP ${label}"; return; }

    echo "[$(date +%H:%M:%S)] BEGIN ${label}"
    ctx-editor \
        experiment="${EXP_NAME}" \
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

PIDS=()
for task in "${TASKS[@]}"; do
    for conv in "${CONVS[@]}"; do
        run_one "$task" "$conv" &
        PIDS+=($!)
        if (( ${#PIDS[@]} >= MAX_PARALLEL )); then
            wait "${PIDS[0]}"
            PIDS=("${PIDS[@]:1}")
        fi
    done
done
for pid in "${PIDS[@]}"; do
    wait "$pid"
done
echo "R6 B1 (A4 v10 GEPA on DSV4F) done."

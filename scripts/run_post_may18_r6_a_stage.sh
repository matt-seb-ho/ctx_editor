#!/usr/bin/env bash
# R6 A-stage: A1 (ac3_rewrite_lic, v1 prompt+v8 analyzer),
#             A2 (ac3_rewrite_v8_lic, v8 prompt+v8 analyzer),
#             A3 (ac3_rewrite_v9_no_conv_lic, v9 prompt+v8 analyzer).
# All three run in parallel; analyzer cache hits keep wall time ~25–30 min.
# Each experiment runs 12 cells (4 tasks * 3 convs) on DSV4F.

set -uo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
[[ -f .env ]] && { set -a; source .env; set +a; }

RUN_TAG="post_may18_r6_a_stage"
OUT_ROOT="outputs/${RUN_TAG}"
LOG_DIR="${OUT_ROOT}/logs"
mkdir -p "$LOG_DIR"

MODEL=deepseek_v4_flash_foundry
LB=multi_endpoint_foundry
MC=4
# Slightly higher overall parallelism — we have 3 experiments × 12 cells = 36 cells.
# Keep MAX_PARALLEL conservative to avoid foundry RPS pressure.
MAX_PARALLEL=6

EXPS=(ac3_rewrite_lic ac3_rewrite_v8_lic ac3_rewrite_v9_no_conv_lic)
TASKS=(math_v2 code_v2 database_v2 actions_v2)
CONVS=(0 1 2)

declare -A DATA_FILE
DATA_FILE[math_v2]="data/htn50_52_math_subset.json"
DATA_FILE[code_v2]="data/htn50_52_code_subset.json"
DATA_FILE[database_v2]="data/htn50_52_database_subset.json"
DATA_FILE[actions_v2]="data/htn50_52_actions_subset.json"

run_one() {
    local exp="$1" task="$2" conv="$3"
    local label="${exp}__${task}__conv${conv}"
    local logfile="${LOG_DIR}/${label}.log"
    local start_ts; start_ts="$(date +%s)"
    local out_run_name="${exp}_${task}_conv${conv}_${start_ts}"
    local out_override="${OUT_ROOT}/${out_run_name}"

    local replay_source="data/valid_prefixes_htn50_52/${MODEL}/${task}/conv${conv}"
    [[ -d "$replay_source" ]] || { echo "[$(date +%H:%M:%S)] SKIP ${label} (no replay)"; return; }

    echo "[$(date +%H:%M:%S)] BEGIN ${label}"
    ctx-editor \
        experiment="${exp}" \
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
for exp in "${EXPS[@]}"; do
    for task in "${TASKS[@]}"; do
        for conv in "${CONVS[@]}"; do
            run_one "$exp" "$task" "$conv" &
            PIDS+=($!)
            if (( ${#PIDS[@]} >= MAX_PARALLEL )); then
                wait "${PIDS[0]}"
                PIDS=("${PIDS[@]:1}")
            fi
        done
    done
done
for pid in "${PIDS[@]}"; do
    wait "$pid"
done
echo "R6 A-stage (A1+A2+A3) done."

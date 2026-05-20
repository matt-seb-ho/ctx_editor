#!/usr/bin/env bash
# Rewrite v3 LiC sweep on DeepSeek-V4-Flash.
#
# Two variants in parallel:
#   v3_no_conv     — strip the conversation from the rewrite prompt;
#                    rewriter operates on analyzer output only.
#   v3_conv_first  — keep conversation but put it BEFORE analysis so
#                    analyzer notes are most-recent in the prompt.
# Hypothesis (Task 1.2b): the conversation-as-input is contagiously
# polluting the rewriter. v3_no_conv is the strongest test; v3_conv_first
# is a softer / cheaper variant of the same hypothesis.

set -uo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
[[ -f .env ]] && { set -a; source .env; set +a; }

RUN_TAG="post_may18_r3_rewrite_v3"
OUT_ROOT="outputs/${RUN_TAG}"
LOG_DIR="${OUT_ROOT}/logs"
mkdir -p "$LOG_DIR"

MODEL=deepseek_v4_flash_foundry
LB=multi_endpoint_foundry
MC=12

VARIANTS=(ac3_rewrite_v3_no_conv_lic ac3_rewrite_v3_conv_first_lic)
TASKS=(math_v2 code_v2 database_v2 actions_v2)
CONVS=(0 1 2)

declare -A DATA_FILE
DATA_FILE[math_v2]="data/htn50_52_math_subset.json"
DATA_FILE[code_v2]="data/htn50_52_code_subset.json"
DATA_FILE[database_v2]="data/htn50_52_database_subset.json"
DATA_FILE[actions_v2]="data/htn50_52_actions_subset.json"

run_one() {
    local exp_name="$1" task="$2" conv="$3"
    local label="${exp_name}__${task}__conv${conv}"
    local logfile="${LOG_DIR}/${label}.log"
    local start_ts; start_ts="$(date +%s)"
    local out_run_name="${exp_name}_${task}_conv${conv}_${start_ts}"
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

PIDS=()
for variant in "${VARIANTS[@]}"; do
    for task in "${TASKS[@]}"; do
        for conv in "${CONVS[@]}"; do
            run_one "${variant}" "${task}" "${conv}" &
            PIDS+=($!)
        done
    done
done
echo "Launched ${#PIDS[@]} Rewrite v3 cells; pids=${PIDS[*]}"
for pid in "${PIDS[@]}"; do
    wait "$pid"
done
echo "Rewrite v3 LiC sweep done."

#!/usr/bin/env bash
# Re-run AC3-Rewrite v3 (no-conv) + v4 (strict relay) on LiC, properly
# throttled to avoid foundry rate-limits. The first attempt at v3 saturated
# the foundry token quota and had 30-49 / 50 samples excluded as errors.
#
# Throttle: max_concurrent=4 per cell; cells run in waves of 4 parallel
# (4 cells × 4 samples ≈ 16 concurrent foundry calls). Two-pass: v3_no_conv
# first, then v4_strict.

set -uo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
[[ -f .env ]] && { set -a; source .env; set +a; }

RUN_TAG="post_may18_r3_rewrite_v3_v4"
OUT_ROOT="outputs/${RUN_TAG}"
LOG_DIR="${OUT_ROOT}/logs"
mkdir -p "$LOG_DIR"

MODEL=deepseek_v4_flash_foundry
LB=multi_endpoint_foundry
MC=4   # per-cell — was 12, caused 429s

# Order: v3_no_conv first (the "remove conversation" hypothesis from
# Task 1.2b), then v4_strict (the "relay only, no hallucination" prompt
# motivated by the 1.1 attribution finding).
VARIANTS=(ac3_rewrite_v3_no_conv_lic ac3_rewrite_v4_strict_lic)
TASKS=(math_v2 code_v2 database_v2 actions_v2)
CONVS=(0 1 2)
MAX_PARALLEL=4   # at most 4 cells run simultaneously

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

# Launch in waves of MAX_PARALLEL across one variant at a time
for variant in "${VARIANTS[@]}"; do
    echo "=== Variant: ${variant} ==="
    PIDS=()
    for task in "${TASKS[@]}"; do
        for conv in "${CONVS[@]}"; do
            run_one "${variant}" "${task}" "${conv}" &
            PIDS+=($!)
            # Throttle: wait when we hit MAX_PARALLEL
            if (( ${#PIDS[@]} >= MAX_PARALLEL )); then
                wait "${PIDS[0]}"
                PIDS=("${PIDS[@]:1}")
            fi
        done
    done
    # Drain remaining
    for pid in "${PIDS[@]}"; do
        wait "$pid"
    done
    echo "=== ${variant} done ==="
done

echo "All v3 + v4 cells done."

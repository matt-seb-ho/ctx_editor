#!/usr/bin/env bash
# R6 B3 cross-benchmark: CollabLLM × winner A2 (v8 prompt) × 3 models.
# CollabLLM uses LiC's ContextCompactionStrategy; override
# strategy.compaction_prompt + strategy.open_ended_output.
# Per sign-off 6: CollabLLM continues using the LiC default analyzer
# (== compaction_model), no analyzer_model override.
#
# 3 models × 2 datasets = 6 cells, ~10 min each, ~30-40 min wall.

set -uo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
[[ -f .env ]] && { set -a; source .env; set +a; }

RUN_TAG="post_may18_r6_b3_collabllm"
OUT_ROOT="outputs/${RUN_TAG}"
LOG_DIR="${OUT_ROOT}/logs"
mkdir -p "$LOG_DIR"

STRATEGY=collabllm_compaction
TASKS=(math-hard bigcodebench)
SEED=43
MC=4

# (model_label, model_config, load_balancer, extra_overrides) tuples.
# All use DeepSeek-V4-Flash as the user-sim per existing R3 fills.
declare -a MODELS=(
    "deepseek|deepseek_v4_flash_user_deepseek|multi_endpoint_foundry|"
    "gpt5_4|gpt5_4|multi_endpoint_with_foundry|model.user.model=DeepSeek-V4-Flash"
    "kimi|kimi_k2_6_foundry|multi_endpoint_foundry|model.user.model=DeepSeek-V4-Flash"
)

run_one() {
    local model_label="$1" model="$2" lb="$3" extra="$4" dataset="$5"
    local label="${model_label}__${STRATEGY}_v8__${dataset}"
    local logfile="${LOG_DIR}/${label}.log"
    local start_ts; start_ts="$(date +%s)"
    local out_run_name="${STRATEGY}_v8_${model_label}_${dataset}_${start_ts}"
    local out_override="${OUT_ROOT}/${out_run_name}"

    local task_name
    if [[ "$dataset" == "math-hard" ]]; then task_name=collabllm_math
    else task_name=collabllm_code; fi

    echo "[$(date +%H:%M:%S)] BEGIN ${label}"
    python -m ctx_editor.run_collabllm \
        experiment="${STRATEGY}" \
        +experiment.strategy.compaction_prompt=context_compaction_v8 \
        +experiment.strategy.open_ended_output=true \
        model="${model}" \
        load_balancer="${lb}" \
        ${extra} \
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
for tup in "${MODELS[@]}"; do
    IFS='|' read -r model_label model lb extra <<<"$tup"
    for dataset in "${TASKS[@]}"; do
        run_one "$model_label" "$model" "$lb" "$extra" "$dataset" &
        PIDS+=($!)
    done
done

echo "Launched ${#PIDS[@]} CollabLLM B3 cells in parallel."
for pid in "${PIDS[@]}"; do
    wait "$pid"
done
echo "R6 B3 CollabLLM done."

#!/usr/bin/env bash
# Mega-table fill: CollabLLM × {gpt-5.4, Kimi-K2.6} × {Baseline, AO, Augment, Reset}
# on math-hard + bigcodebench. User-sim = DeepSeek-V4-Flash (per the R2
# finding that gpt-4o-mini drifts too much).
#
# Each cell is a fresh-sim multi-turn CollabLLM run (no replay-mode for
# CollabLLM yet — see post_neurips_r2_next_plan.md). Single rep N=1 to fit
# tonight's budget; multi-rep error bars are a follow-up.

set -uo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
[[ -f .env ]] && { set -a; source .env; set +a; }

RUN_TAG="post_may18_r3_collabllm_fills"
OUT_ROOT="outputs/${RUN_TAG}"
LOG_DIR="${OUT_ROOT}/logs"
mkdir -p "$LOG_DIR"

# For each (assistant model), we need a model config that ALSO uses
# DeepSeek as the user simulator. gpt-5.4 needs a fresh config; we can
# reuse deepseek_v4_flash_user_deepseek shape but with the assistant
# model swapped. Easier path: just rely on a small launcher Hydra-override.

MC=6   # was 15 in R2 — be conservative to avoid 429s while other jobs run

# (assistant_model_yaml_name, load_balancer, label)
declare -a CONFIGS=(
    "gpt5_4|multi_endpoint|gpt5_4"
    "kimi_k2_6_foundry|multi_endpoint_foundry|kimi_k2_6"
)

STRATEGIES=(collabllm_baseline collabllm_assistant_omit collabllm_ac3_augment_v8 collabllm_ac3_reset_v8)
TASKS=(math-hard bigcodebench)
SEED=43

run_one() {
    local model="$1" lb="$2" model_label="$3" strategy="$4" dataset="$5"
    local label="${model_label}__${strategy}__${dataset}"
    local logfile="${LOG_DIR}/${label}.log"
    local start_ts; start_ts="$(date +%s)"
    local out_run_name="${strategy}_${model_label}_${dataset}_${start_ts}"
    local out_override="${OUT_ROOT}/${out_run_name}"

    local task_name
    if [[ "$dataset" == "math-hard" ]]; then task_name=collabllm_math
    else task_name=collabllm_code; fi

    echo "[$(date +%H:%M:%S)] BEGIN ${label}"
    # Override user.model to DeepSeek-V4-Flash via Hydra; keep assistant from cfg.
    python -m ctx_editor.run_collabllm \
        experiment="${strategy}" \
        model="${model}" \
        load_balancer="${lb}" \
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
        echo "[$(date +%H:%M:%S)] FAIL  ${label}  (rc=${rc}, ${elapsed}s)  see ${logfile}"
    fi
}

# Run model-by-model serially; within a model, parallelize across (strategy, task).
# This keeps foundry token-rate predictable.
for cfg in "${CONFIGS[@]}"; do
    IFS='|' read -r model lb model_label <<<"$cfg"
    echo "=== ${model_label} ==="
    PIDS=()
    for strategy in "${STRATEGIES[@]}"; do
        for dataset in "${TASKS[@]}"; do
            run_one "$model" "$lb" "$model_label" "$strategy" "$dataset" &
            PIDS+=($!)
        done
    done
    for pid in "${PIDS[@]}"; do
        wait "$pid"
    done
    echo "=== ${model_label} done ==="
done

echo "CollabLLM mega-table fills done."

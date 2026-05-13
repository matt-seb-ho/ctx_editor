#!/usr/bin/env bash
# Launch CollabLLM Gated-Reset (4 runs) and Augment (2 replicates) for math/code.
# Same 20-sample slice as existing labeled+r2_ replicates (seed=42, limit=20).
set -euo pipefail

cd "$(dirname "$0")/.."

DATE_TAG="$(date +%Y-%m-%d)"
LOG_DIR="outputs/${DATE_TAG}/_launch_logs"
mkdir -p "$LOG_DIR"

run_one() {
    local label="$1"        # e.g. gr_math_r1
    local experiment="$2"   # e.g. collabllm_context_edit_v2
    local task_name="$3"    # collabllm_math | collabllm_code
    local dataset="$4"      # math-hard | bigcodebench
    local out="outputs/${DATE_TAG}/${label}"

    echo "[launch] $label -> $out"
    python -m ctx_editor.run_collabllm \
        experiment="$experiment" \
        task.name="$task_name" \
        task.dataset_name="$dataset" \
        task.limit=20 \
        execution.max_concurrent=10 \
        seed=42 \
        logging.output_dir="$out" \
        > "${LOG_DIR}/${label}.stdout.log" 2> "${LOG_DIR}/${label}.stderr.log" &
    echo "  pid=$!  log=${LOG_DIR}/${label}.{stdout,stderr}.log"
}

# Gated-Reset (4 runs)
run_one gr_math_r1 collabllm_context_edit_v2 collabllm_math math-hard
run_one gr_math_r2 collabllm_context_edit_v2 collabllm_math math-hard
run_one gr_code_r1 collabllm_context_edit_v2 collabllm_code bigcodebench
run_one gr_code_r2 collabllm_context_edit_v2 collabllm_code bigcodebench

# Augment replicates (2 runs)
run_one aug_math_r2 collabllm_append_analysis collabllm_math math-hard
run_one aug_code_r2 collabllm_append_analysis collabllm_code bigcodebench

wait
echo "all 6 runs finished"

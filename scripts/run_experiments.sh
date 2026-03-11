#!/usr/bin/env bash
# =============================================================================
# Run all experiments for math and code test subsets
#
# Experiments:
#   Phase 1 (no memory): baseline, reflection_only, context_edit, agentic_edit
#   Phase 2 (with memory): baseline_memory, context_edit_memory, agentic_edit_memory
#
# Usage:
#   bash scripts/run_experiments.sh           # Run everything
#   bash scripts/run_experiments.sh phase1    # Only no-memory experiments
#   bash scripts/run_experiments.sh phase2    # Only memory experiments
#   bash scripts/run_experiments.sh single <experiment> <task>  # Single run
# =============================================================================

set -euo pipefail

# Common settings
MODEL="gpt5_mini"
USER_MODE="sharded"
MAX_CONCURRENT=8

# Load API keys from .env
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
if [[ -f "$PROJECT_ROOT/.env" ]]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

# Task → data file mapping (test subsets)
declare -A TASK_DATA
TASK_DATA[math_v2]="data/test_math_subset.json"
TASK_DATA[code_v2]="data/test_code_subset.json"

# Phase 1: no-memory experiments (parallel execution is fine)
PHASE1_EXPERIMENTS=(baseline reflection_only context_edit agentic_edit)

# Phase 2: memory experiments (need batched execution for continual learning)
PHASE2_EXPERIMENTS=(baseline_memory context_edit_memory agentic_edit_memory)

run_experiment() {
    local experiment="$1"
    local task="$2"
    local data_file="${TASK_DATA[$task]}"

    # Determine execution mode and memory overrides for memory experiments
    local extra_args=""
    if [[ "$experiment" == *_memory ]]; then
        # Batched mode for continual learning
        # batch_size=5 for code (20 problems → 4 batches), batch_size=3 for math (9 problems → 3 batches)
        local batch_size=5
        if [[ "$task" == "math_v2" ]]; then
            batch_size=3
        fi

        # Determine memory target based on experiment type
        local mem_target="assistant"
        if [[ "$experiment" == context_edit_memory ]] || [[ "$experiment" == agentic_edit_memory ]]; then
            mem_target="context_editor"
        fi

        extra_args="execution.mode=batched execution.batch_size=${batch_size}"
        extra_args+=" memory.enabled=true memory.source=continual memory.target=${mem_target}"
        extra_args+=" memory.include_full_spec_q=true memory.include_ground_truth_a=true"
    fi

    echo "=============================================="
    echo "Running: experiment=${experiment} task=${task}"
    echo "  data_file=${data_file}"
    echo "  extra: ${extra_args:-none}"
    echo "=============================================="

    python -m ctx_editor.run_experiment \
        model="${MODEL}" \
        task="${task}" \
        task.data_file="${data_file}" \
        experiment="${experiment}" \
        user_mode="${USER_MODE}" \
        execution.max_concurrent="${MAX_CONCURRENT}" \
        ${extra_args} \
        2>&1 | tee -a "outputs/experiment_log_${experiment}_${task}.txt"

    echo ""
    echo "Completed: ${experiment} / ${task}"
    echo ""
}

phase1() {
    echo "=== PHASE 1: No-memory experiments ==="
    for experiment in "${PHASE1_EXPERIMENTS[@]}"; do
        for task in math_v2 code_v2; do
            run_experiment "$experiment" "$task"
        done
    done
}

phase2() {
    echo "=== PHASE 2: Memory experiments ==="
    for experiment in "${PHASE2_EXPERIMENTS[@]}"; do
        for task in math_v2 code_v2; do
            run_experiment "$experiment" "$task"
        done
    done
}

# Parse command
case "${1:-all}" in
    phase1) phase1 ;;
    phase2) phase2 ;;
    single)
        if [[ $# -lt 3 ]]; then
            echo "Usage: $0 single <experiment> <task>"
            exit 1
        fi
        run_experiment "$2" "$3"
        ;;
    all)
        phase1
        phase2
        ;;
    *)
        echo "Usage: $0 [all|phase1|phase2|single <experiment> <task>]"
        exit 1
        ;;
esac

echo "=== All requested experiments complete ==="

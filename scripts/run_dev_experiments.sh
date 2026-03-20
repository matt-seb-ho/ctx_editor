#!/bin/bash
# Run all dev set experiments: 3 strategies (S0/S1/S2) × 2 memory settings × 4 tasks = 24 runs
# Models: gpt-5-mini (medium reasoning) for assistant/editor/analyzer, gpt-4o-mini for user/system
# Memory runs use batched mode; non-memory runs use parallel mode.
#
# Usage:
#   ./scripts/run_dev_experiments.sh          # Run all 24
#   ./scripts/run_dev_experiments.sh nomem    # Run only no-memory (12)
#   ./scripts/run_dev_experiments.sh mem      # Run only memory (12)
#   ./scripts/run_dev_experiments.sh S0       # Run only baseline (8)
#   ./scripts/run_dev_experiments.sh S1       # Run only append_analysis (8)
#   ./scripts/run_dev_experiments.sh S2       # Run only context_edit_v2 (8)

set -uo pipefail

TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
MEMORY_DIR="outputs/dev_memories/${TIMESTAMP}"
LOG_DIR="outputs/dev_logs/${TIMESTAMP}"
mkdir -p "$MEMORY_DIR" "$LOG_DIR"

FILTER="${1:-all}"

TASKS=(dev_math dev_code dev_database dev_actions)

# Common settings
COMMON="model=gpt5_mini execution.max_concurrent=5 logging.verbose=true metadata.branch=newleaf2"

run_experiment() {
    local experiment="$1"
    local task="$2"
    local label="$3"
    local extra_args="$4"
    local logfile="${LOG_DIR}/${label}.log"

    echo "=========================================="
    echo "[$(date +%H:%M:%S)] Starting: ${label}"
    echo "=========================================="

    ctx-editor \
        experiment="${experiment}" \
        task="${task}" \
        ${COMMON} \
        ${extra_args} \
        > "${logfile}" 2>&1
    local exit_code=$?

    # Print summary from log (last lines with results)
    grep -E "(accuracy|correct|ERROR|error|Finished|complete)" "${logfile}" | tail -10 || true

    echo "[$(date +%H:%M:%S)] Finished: ${label} (exit=${exit_code})"
    echo ""
}

###############################################################################
# NO-MEMORY RUNS (parallel mode)
###############################################################################
run_nomem() {
    local strategy_name="$1"   # e.g. baseline, append_analysis, context_edit_v2
    local short="$2"           # e.g. S0, S1, S2

    for task in "${TASKS[@]}"; do
        local label="${short}_nomem_${task}"
        run_experiment \
            "${strategy_name}" \
            "${task}" \
            "${label}" \
            "execution.mode=parallel"
    done
}

###############################################################################
# MEMORY RUNS (batched mode)
###############################################################################
run_mem() {
    local strategy_name="$1"   # e.g. baseline_memory, append_analysis_memory, context_edit_v2_memory
    local short="$2"           # e.g. S0, S1, S2
    local mem_target="$3"      # memory.target: assistant (S0) or analyzer (S1/S2)

    for task in "${TASKS[@]}"; do
        local label="${short}_mem_${task}"
        local mem_path="${MEMORY_DIR}/${label}_cheatsheet.json"
        run_experiment \
            "${strategy_name}" \
            "${task}" \
            "${label}" \
            "execution.mode=batched execution.batch_size=5 memory.enabled=true memory.source=continual memory.target=${mem_target} memory.save_path=${mem_path} memory.include_full_spec_q=true memory.include_ground_truth_a=true"
    done
}

###############################################################################
# Main dispatch
###############################################################################
echo "============================================================"
echo "Dev Set Experiment Suite — ${TIMESTAMP}"
echo "Filter: ${FILTER}"
echo "Memory checkpoints: ${MEMORY_DIR}/"
echo "Logs: ${LOG_DIR}/"
echo "============================================================"
echo ""

# S0 — Baseline
if [[ "$FILTER" == "all" || "$FILTER" == "nomem" || "$FILTER" == "S0" ]]; then
    run_nomem "baseline" "S0"
fi
if [[ "$FILTER" == "all" || "$FILTER" == "mem" || "$FILTER" == "S0" ]]; then
    run_mem "baseline_memory" "S0" "assistant"
fi

# S1 — Append Analysis
if [[ "$FILTER" == "all" || "$FILTER" == "nomem" || "$FILTER" == "S1" ]]; then
    run_nomem "append_analysis" "S1"
fi
if [[ "$FILTER" == "all" || "$FILTER" == "mem" || "$FILTER" == "S1" ]]; then
    run_mem "append_analysis_memory" "S1" "analyzer"
fi

# S2 — Context Edit V2
if [[ "$FILTER" == "all" || "$FILTER" == "nomem" || "$FILTER" == "S2" ]]; then
    run_nomem "context_edit_v2" "S2"
fi
if [[ "$FILTER" == "all" || "$FILTER" == "mem" || "$FILTER" == "S2" ]]; then
    run_mem "context_edit_v2_memory" "S2" "analyzer"
fi

echo ""
echo "============================================================"
echo "All requested experiments complete!"
echo "Memory checkpoints saved in: ${MEMORY_DIR}/"
echo "Logs saved in: ${LOG_DIR}/"
echo "============================================================"

#!/bin/bash
# Replay mode experiments: reuse S0 baseline conversation prefixes,
# regenerate only the final assistant turn with S1/S2 (± memory).
#
# This is faster/cheaper than full simulation and controls for conversational
# prefix, isolating the effect of the context intervention on the final turn.
#
# Usage:
#   ./scripts/run_replay_experiments.sh          # Run all
#   ./scripts/run_replay_experiments.sh nomem    # No-memory only
#   ./scripts/run_replay_experiments.sh mem      # Memory only

set -uo pipefail

TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
MEMORY_DIR="outputs/replay_memories/${TIMESTAMP}"
LOG_DIR="outputs/replay_logs/${TIMESTAMP}"
mkdir -p "$MEMORY_DIR" "$LOG_DIR"

FILTER="${1:-all}"

# S0 baseline trace directories (from the main dev experiment run)
S0_MATH="outputs/2026-03-13/13-44-00/traces/math/baseline"
S0_CODE="outputs/2026-03-13/13-53-02/traces/code/baseline"
S0_ACTIONS="outputs/2026-03-13/14-15-27/traces/actions/baseline"

# Common settings
COMMON="model=gpt5_mini execution.max_concurrent=8 logging.verbose=true metadata.branch=newleaf2"

# Task configs paired with their S0 trace sources
declare -A TRACE_SOURCES
TRACE_SOURCES[dev_math]="$S0_MATH"
TRACE_SOURCES[dev_code]="$S0_CODE"
TRACE_SOURCES[dev_actions]="$S0_ACTIONS"

TASKS=(dev_math dev_code dev_actions)

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

    grep -E "(accuracy|correct|Results:|complete)" "${logfile}" | tail -5 || true
    echo "[$(date +%H:%M:%S)] Finished: ${label} (exit=${exit_code})"
    echo ""
}

###############################################################################
# NO-MEMORY REPLAY RUNS
###############################################################################
run_replay_nomem() {
    local strategy="$1"    # e.g. append_analysis, context_edit_v2
    local short="$2"       # e.g. S1, S2

    for task in "${TASKS[@]}"; do
        local label="${short}_replay_nomem_${task}"
        local trace_src="${TRACE_SOURCES[$task]}"
        run_experiment \
            "${strategy}" \
            "${task}" \
            "${label}" \
            "execution.replay_source=${trace_src}"
    done
}

###############################################################################
# MEMORY REPLAY RUNS (batched)
###############################################################################
run_replay_mem() {
    local strategy="$1"    # e.g. append_analysis_memory, context_edit_v2_memory
    local short="$2"       # e.g. S1, S2
    local mem_target="$3"  # analyzer

    for task in "${TASKS[@]}"; do
        local label="${short}_replay_mem_${task}"
        local trace_src="${TRACE_SOURCES[$task]}"
        local mem_path="${MEMORY_DIR}/${label}_cheatsheet.json"
        run_experiment \
            "${strategy}" \
            "${task}" \
            "${label}" \
            "execution.replay_source=${trace_src} execution.mode=batched execution.batch_size=5 memory.enabled=true memory.source=continual memory.target=${mem_target} memory.save_path=${mem_path} memory.include_full_spec_q=true memory.include_ground_truth_a=true"
    done
}

###############################################################################
# Main dispatch
###############################################################################
echo "============================================================"
echo "Replay Experiment Suite — ${TIMESTAMP}"
echo "Filter: ${FILTER}"
echo "Memory checkpoints: ${MEMORY_DIR}/"
echo "Logs: ${LOG_DIR}/"
echo "============================================================"
echo ""

# S1 — Append Analysis
if [[ "$FILTER" == "all" || "$FILTER" == "nomem" ]]; then
    run_replay_nomem "append_analysis" "S1"
fi
if [[ "$FILTER" == "all" || "$FILTER" == "mem" ]]; then
    run_replay_mem "append_analysis_memory" "S1" "analyzer"
fi

# S2 — Context Edit V2
if [[ "$FILTER" == "all" || "$FILTER" == "nomem" ]]; then
    run_replay_nomem "context_edit_v2" "S2"
fi
if [[ "$FILTER" == "all" || "$FILTER" == "mem" ]]; then
    run_replay_mem "context_edit_v2_memory" "S2" "analyzer"
fi

echo ""
echo "============================================================"
echo "All replay experiments complete!"
echo "Memory checkpoints: ${MEMORY_DIR}/"
echo "Logs: ${LOG_DIR}/"
echo "============================================================"

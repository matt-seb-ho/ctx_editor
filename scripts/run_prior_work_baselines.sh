#!/bin/bash
# Prior work baseline comparisons: Huang (omit assistant) + ERGO (concatenate user)
# All 4 tasks × 2 strategies = 8 runs, replay last turn
#
# Tasks: dev_math (20), dev_code (19), dev_database (25), dev_actions (23)
# Model: gpt5_mini

set -uo pipefail

TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
LOG_DIR="outputs/prior_baselines_logs/${TIMESTAMP}"
mkdir -p "$LOG_DIR"

COMMON="model=gpt5_mini execution.max_concurrent=8 execution.replay_turns=1 logging.verbose=true metadata.branch=main"

# Trace sources per task
declare -A TRACE_SOURCES
TRACE_SOURCES[dev_math]="data/baseline_traces_v2/math"
TRACE_SOURCES[dev_code]="data/baseline_traces_v2/code"
TRACE_SOURCES[dev_database]="data/baseline_traces_v2/database"
TRACE_SOURCES[dev_actions]="data/baseline_traces/actions"

TASKS=(dev_math dev_code dev_database dev_actions)

run_experiment() {
    local experiment="$1"
    local task="$2"
    local label="$3"
    local trace_src="$4"
    local logfile="${LOG_DIR}/${label}.log"

    echo "=========================================="
    echo "[$(date +%H:%M:%S)] Starting: ${label}"
    echo "=========================================="

    ctx-editor \
        experiment="${experiment}" \
        task="${task}" \
        ${COMMON} \
        execution.replay_source="${trace_src}" \
        > "${logfile}" 2>&1
    local exit_code=$?

    grep -E "(Results:|user-sim-induced skipped|Accuracy)" "${logfile}" | tail -5 || true
    echo "[$(date +%H:%M:%S)] Finished: ${label} (exit=${exit_code})"
    echo ""
}

echo "============================================"
echo "Prior Work Baselines — ${TIMESTAMP}"
echo "============================================"
echo ""

# Run all tasks × both strategies
for task in "${TASKS[@]}"; do
    trace_src="${TRACE_SOURCES[$task]}"

    # Huang et al.: Omit assistant messages
    run_experiment "omit_assistant" "$task" "omit_assistant_${task}" "$trace_src"

    # ERGO-style: Concatenate user messages
    run_experiment "concatenate_user" "$task" "concatenate_user_${task}" "$trace_src"
done

echo "============================================"
echo "All runs complete. Logs in: ${LOG_DIR}"
echo "============================================"

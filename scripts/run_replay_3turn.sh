#!/bin/bash
# Multi-turn replay experiments: replay last 3 turns with S1/S2 (± memory)
# Uses v2 task configs and baseline_traces_v2 source traces.
#
# Tasks: math_v2, code_v2
# Strategies: S1 (append_analysis), S2 (context_edit_v2), both ± memory
# Model: gpt5_mini (gpt-5-mini for assistant/strategy, gpt-4o-mini for user/system)

set -uo pipefail

TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
MEMORY_DIR="outputs/replay_memories/${TIMESTAMP}"
LOG_DIR="outputs/replay_logs/${TIMESTAMP}"
mkdir -p "$MEMORY_DIR" "$LOG_DIR"

TRACE_DIR="data/baseline_traces_v2"
REPLAY_TURNS=3

COMMON="model=gpt5_mini execution.max_concurrent=8 execution.replay_turns=${REPLAY_TURNS} logging.verbose=true metadata.branch=newleaf2"

declare -A TRACE_SOURCES
TRACE_SOURCES[math_v2]="${TRACE_DIR}/math"
TRACE_SOURCES[code_v2]="${TRACE_DIR}/code"

TASKS=(math_v2 code_v2)

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

echo "============================================================"
echo "3-Turn Replay Experiment Suite — ${TIMESTAMP}"
echo "Replaying last ${REPLAY_TURNS} turns"
echo "Memory checkpoints: ${MEMORY_DIR}/"
echo "Logs: ${LOG_DIR}/"
echo "============================================================"
echo ""

# S1 no-memory
for task in "${TASKS[@]}"; do
    label="S1_replay3_nomem_${task}"
    trace_src="${TRACE_SOURCES[$task]}"
    run_experiment "append_analysis" "${task}" "${label}" \
        "execution.replay_source=${trace_src}"
done

# S1 with memory (batched continual)
for task in "${TASKS[@]}"; do
    label="S1_replay3_mem_${task}"
    trace_src="${TRACE_SOURCES[$task]}"
    mem_path="${MEMORY_DIR}/${label}_cheatsheet.json"
    run_experiment "append_analysis_memory" "${task}" "${label}" \
        "execution.replay_source=${trace_src} execution.mode=batched execution.batch_size=5 memory.enabled=true memory.source=continual memory.target=analyzer memory.save_path=${mem_path} memory.include_full_spec_q=true memory.include_ground_truth_a=true"
done

# S2 no-memory
for task in "${TASKS[@]}"; do
    label="S2_replay3_nomem_${task}"
    trace_src="${TRACE_SOURCES[$task]}"
    run_experiment "context_edit_v2" "${task}" "${label}" \
        "execution.replay_source=${trace_src}"
done

# S2 with memory (batched continual)
for task in "${TASKS[@]}"; do
    label="S2_replay3_mem_${task}"
    trace_src="${TRACE_SOURCES[$task]}"
    mem_path="${MEMORY_DIR}/${label}_cheatsheet.json"
    run_experiment "context_edit_v2_memory" "${task}" "${label}" \
        "execution.replay_source=${trace_src} execution.mode=batched execution.batch_size=5 memory.enabled=true memory.source=continual memory.target=analyzer memory.save_path=${mem_path} memory.include_full_spec_q=true memory.include_ground_truth_a=true"
done

echo ""
echo "============================================================"
echo "All 3-turn replay experiments complete!"
echo "Memory checkpoints: ${MEMORY_DIR}/"
echo "Logs: ${LOG_DIR}/"
echo "============================================================"

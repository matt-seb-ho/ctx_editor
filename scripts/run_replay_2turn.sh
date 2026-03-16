#!/bin/bash
# Multi-turn replay experiments: replay last 2 turns with S0+mem, S1, S1+mem, S2, S2+mem
# Uses dev task configs and baseline_traces_v2 source traces.
#
# Tasks: dev_math (23 samples), dev_code (25 samples)
# Strategies: S0+mem (baseline_memory), S1 (append_analysis), S1+mem, S2 (context_edit_v2), S2+mem
# Model: gpt5_mini (gpt-5-mini for assistant/strategy, gpt-4o-mini for user/system)

set -uo pipefail

TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
MEMORY_DIR="outputs/replay_memories/${TIMESTAMP}"
LOG_DIR="outputs/replay_logs/${TIMESTAMP}"
mkdir -p "$MEMORY_DIR" "$LOG_DIR"

TRACE_DIR="data/baseline_traces_v2"
REPLAY_TURNS=2

COMMON="model=gpt5_mini execution.max_concurrent=8 execution.replay_turns=${REPLAY_TURNS} logging.verbose=true metadata.branch=newleaf2"

declare -A TRACE_SOURCES
TRACE_SOURCES[dev_math]="${TRACE_DIR}/math"
TRACE_SOURCES[dev_code]="${TRACE_DIR}/code"

TASKS=(dev_math dev_code)

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
echo "2-Turn Replay Experiment Suite — ${TIMESTAMP}"
echo "Replaying last ${REPLAY_TURNS} turns"
echo "Memory checkpoints: ${MEMORY_DIR}/"
echo "Logs: ${LOG_DIR}/"
echo "============================================================"
echo ""

# S0 + memory (batched continual, memory.target=assistant)
for task in "${TASKS[@]}"; do
    label="S0_replay2_mem_${task}"
    trace_src="${TRACE_SOURCES[$task]}"
    mem_path="${MEMORY_DIR}/${label}_cheatsheet.json"
    run_experiment "baseline_memory" "${task}" "${label}" \
        "execution.replay_source=${trace_src} execution.mode=batched execution.batch_size=5 memory.enabled=true memory.source=continual memory.target=assistant memory.save_path=${mem_path} memory.include_full_spec_q=true memory.include_ground_truth_a=true"
done

# S1 no-memory
for task in "${TASKS[@]}"; do
    label="S1_replay2_nomem_${task}"
    trace_src="${TRACE_SOURCES[$task]}"
    run_experiment "append_analysis" "${task}" "${label}" \
        "execution.replay_source=${trace_src}"
done

# S1 with memory (batched continual, memory.target=analyzer)
for task in "${TASKS[@]}"; do
    label="S1_replay2_mem_${task}"
    trace_src="${TRACE_SOURCES[$task]}"
    mem_path="${MEMORY_DIR}/${label}_cheatsheet.json"
    run_experiment "append_analysis_memory" "${task}" "${label}" \
        "execution.replay_source=${trace_src} execution.mode=batched execution.batch_size=5 memory.enabled=true memory.source=continual memory.target=analyzer memory.save_path=${mem_path} memory.include_full_spec_q=true memory.include_ground_truth_a=true"
done

# S2 no-memory
for task in "${TASKS[@]}"; do
    label="S2_replay2_nomem_${task}"
    trace_src="${TRACE_SOURCES[$task]}"
    run_experiment "context_edit_v2" "${task}" "${label}" \
        "execution.replay_source=${trace_src}"
done

# S2 with memory (batched continual, memory.target=analyzer)
for task in "${TASKS[@]}"; do
    label="S2_replay2_mem_${task}"
    trace_src="${TRACE_SOURCES[$task]}"
    mem_path="${MEMORY_DIR}/${label}_cheatsheet.json"
    run_experiment "context_edit_v2_memory" "${task}" "${label}" \
        "execution.replay_source=${trace_src} execution.mode=batched execution.batch_size=5 memory.enabled=true memory.source=continual memory.target=analyzer memory.save_path=${mem_path} memory.include_full_spec_q=true memory.include_ground_truth_a=true"
done

echo ""
echo "============================================================"
echo "All 2-turn replay experiments complete!"
echo "Memory checkpoints: ${MEMORY_DIR}/"
echo "Logs: ${LOG_DIR}/"
echo "============================================================"

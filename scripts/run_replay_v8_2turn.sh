#!/bin/bash
# Replay-last-2-turns experiments with v8 prompts
# All 4 tasks × {S0, S1, S2} × {no mem, mem} = 24 runs
# Uses pre-computed false_negatives.json to skip user-sim-induced samples
#
# Tasks: dev_math (20 after skip), dev_code (19), dev_database (25), dev_actions (23)
# Model: gpt5_mini
# Analyzer prompts: v8 (for S1/S2)

set -uo pipefail

TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
MEMORY_DIR="outputs/replay_memories/${TIMESTAMP}"
LOG_DIR="outputs/replay_logs/${TIMESTAMP}"
mkdir -p "$MEMORY_DIR" "$LOG_DIR"

COMMON="model=gpt5_mini execution.max_concurrent=8 execution.replay_turns=2 logging.verbose=true metadata.branch=newleaf2"

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

    grep -E "(Results:|user-sim-induced skipped)" "${logfile}" | tail -3 || true
    echo "[$(date +%H:%M:%S)] Finished: ${label} (exit=${exit_code})"
    echo ""
}

echo "============================================================"
echo "V8 Replay-Last-2-Turns Experiment Suite — ${TIMESTAMP}"
echo "Analyzer prompt version: v8"
echo "Memory checkpoints: ${MEMORY_DIR}/"
echo "Logs: ${LOG_DIR}/"
echo "============================================================"
echo ""

# --- S0 (baseline) no-memory — no analyzer, so no v8 needed ---
for task in "${TASKS[@]}"; do
    label="S0_nomem_${task}"
    trace_src="${TRACE_SOURCES[$task]}"
    run_experiment "baseline" "${task}" "${label}" \
        "execution.replay_source=${trace_src}"
done

# --- S0 + memory — no analyzer ---
for task in "${TASKS[@]}"; do
    label="S0_mem_${task}"
    trace_src="${TRACE_SOURCES[$task]}"
    mem_path="${MEMORY_DIR}/${label}_cheatsheet.json"
    run_experiment "baseline_memory" "${task}" "${label}" \
        "execution.replay_source=${trace_src} execution.mode=batched execution.batch_size=5 memory.enabled=true memory.source=continual memory.target=assistant memory.save_path=${mem_path} memory.include_full_spec_q=true memory.include_ground_truth_a=true"
done

# --- S1 no-memory (v8 prompts) ---
for task in "${TASKS[@]}"; do
    label="S1_nomem_${task}"
    trace_src="${TRACE_SOURCES[$task]}"
    run_experiment "append_analysis" "${task}" "${label}" \
        "execution.replay_source=${trace_src}"
done

# --- S1 + memory (v8 prompts) ---
for task in "${TASKS[@]}"; do
    label="S1_mem_${task}"
    trace_src="${TRACE_SOURCES[$task]}"
    mem_path="${MEMORY_DIR}/${label}_cheatsheet.json"
    run_experiment "append_analysis_memory" "${task}" "${label}" \
        "execution.replay_source=${trace_src} execution.mode=batched execution.batch_size=5 memory.enabled=true memory.source=continual memory.target=analyzer memory.save_path=${mem_path} memory.include_full_spec_q=true memory.include_ground_truth_a=true"
done

# --- S2 no-memory (v8 prompts) ---
for task in "${TASKS[@]}"; do
    label="S2_nomem_${task}"
    trace_src="${TRACE_SOURCES[$task]}"
    run_experiment "context_edit_v2" "${task}" "${label}" \
        "execution.replay_source=${trace_src}"
done

# --- S2 + memory (v8 prompts) ---
for task in "${TASKS[@]}"; do
    label="S2_mem_${task}"
    trace_src="${TRACE_SOURCES[$task]}"
    mem_path="${MEMORY_DIR}/${label}_cheatsheet.json"
    run_experiment "context_edit_v2_memory" "${task}" "${label}" \
        "execution.replay_source=${trace_src} execution.mode=batched execution.batch_size=5 memory.enabled=true memory.source=continual memory.target=analyzer memory.save_path=${mem_path} memory.include_full_spec_q=true memory.include_ground_truth_a=true"
done

echo ""
echo "============================================================"
echo "All v8 2-turn replay experiments complete!"
echo "Memory checkpoints: ${MEMORY_DIR}/"
echo "Logs: ${LOG_DIR}/"
echo "============================================================"

#!/bin/bash
# S1.5 experiment: always-reset context using S1's pre-computed analysis
# Tests whether removing bad context helps beyond S1's appended analysis
# Runs on both S1 no-mem and S1+mem traces for all 4 tasks

set -uo pipefail

LOG_DIR="outputs/replay_logs/s15_$(date +%Y-%m-%d_%H-%M-%S)"
mkdir -p "$LOG_DIR"

echo "============================================================"
echo "S1.5 Experiment Suite"
echo "Logs: ${LOG_DIR}/"
echo "============================================================"
echo ""

run() {
    local s1_dir="$1"
    local task="$2"
    local label="$3"
    local logfile="${LOG_DIR}/${label}.log"

    echo "=========================================="
    echo "[$(date +%H:%M:%S)] Starting: ${label}"
    echo "=========================================="

    python scripts/run_s15_experiment.py \
        --s1-dir "${s1_dir}" \
        --task "${task}" \
        --model gpt-5-mini \
        --label "${label}" \
        > "${logfile}" 2>&1
    local exit_code=$?

    grep -E "Results:" "${logfile}" | tail -1 || true
    echo "[$(date +%H:%M:%S)] Finished: ${label} (exit=${exit_code})"
    echo ""
}

# S1.5 from S1 no-mem traces
run "outputs/2026-03-16/20-08-42" "math"     "S15_nomem_math"
run "outputs/2026-03-16/20-12-21" "code"     "S15_nomem_code"
run "outputs/2026-03-16/20-25-09" "database" "S15_nomem_database"
run "outputs/2026-03-16/20-29-27" "actions"  "S15_nomem_actions"

# S1.5 from S1+mem traces
run "outputs/2026-03-16/20-33-21" "math"     "S15_mem_math"
run "outputs/2026-03-16/20-42-35" "code"     "S15_mem_code"
run "outputs/2026-03-16/20-52-20" "database" "S15_mem_database"
run "outputs/2026-03-16/21-02-17" "actions"  "S15_mem_actions"

echo ""
echo "============================================================"
echo "All S1.5 experiments complete!"
echo "Logs: ${LOG_DIR}/"
echo "============================================================"

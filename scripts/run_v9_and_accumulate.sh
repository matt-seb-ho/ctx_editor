#!/bin/bash
# V9 LiC experiments + actions accumulate fairness runs
#
# Two workstreams:
# 1. Actions accumulate fairness (v8): baseline+accum, S1+accum for actions only
# 2. V9 LiC experiments: S1, S1.5, S2, S3 across all tasks
#
# All use replay from existing traces.

set -uo pipefail

LOG_DIR="outputs/replay_logs/v9_$(date +%Y-%m-%d_%H-%M-%S)"
mkdir -p "$LOG_DIR"

MODEL="gpt-5-mini"
MAX_CONCURRENT=20

# Shared flags for S1.5-style runs
S15_FLAGS="--no-notes --sanitize --no-clarification"

echo "============================================================"
echo "V9 LiC + Actions Accumulate Fairness"
echo "Max concurrent: ${MAX_CONCURRENT}"
echo "Logs: ${LOG_DIR}/"
echo "============================================================"
echo ""

run_s15() {
    local s1_dir="$1"
    local task="$2"
    local label="$3"
    shift 3
    local extra_flags="$*"
    local logfile="${LOG_DIR}/${label}.log"

    echo "[$(date +%H:%M:%S)] Starting: ${label} ..."

    python scripts/run_s15_experiment.py \
        --s1-dir "${s1_dir}" \
        --task "${task}" \
        --model "${MODEL}" \
        --label "${label}" \
        --max-concurrent ${MAX_CONCURRENT} \
        ${extra_flags} \
        2>&1 | tee "${logfile}"

    echo "[$(date +%H:%M:%S)] Finished: ${label}"
    echo ""
}

# =============================================================
# PART 1: Actions Accumulate Fairness (v8)
# =============================================================
echo "============================================"
echo "Part 1: Actions Accumulate Fairness (v8)"
echo "============================================"

# S0 (baseline) + accumulate — replay from baseline actions traces
run_s15 "outputs/2026-03-16/19-26-46" actions \
    "v8_S0_accum_actions" \
    --mode s0-accum --accumulate --no-clarification

# S1 (append analysis) + accumulate — replay from S1 actions traces
run_s15 "outputs/2026-03-16/20-29-27" actions \
    "v8_S1_accum_actions" \
    --mode s1-accum --accumulate --no-clarification

# S1.5 + accumulate — already done (52%), but also do S3 for completeness
# S3 (v8, hard attention) — replay from S1 actions traces
run_s15 "outputs/2026-03-16/20-29-27" actions \
    "v8_S3_actions" \
    --mode s3

# =============================================================
# PART 2: V8 S3 for LiC (never tested with hard attention)
# =============================================================
echo "============================================"
echo "Part 2: V8 S3 for LiC (hard attention)"
echo "============================================"

# S3 from S1 hard-attention traces (v8)
run_s15 "outputs/2026-03-16/20-08-42" math     "v8_S3_math"     --mode s3
run_s15 "outputs/2026-03-16/20-12-21" code     "v8_S3_code"     --mode s3
run_s15 "outputs/2026-03-16/20-25-09" database "v8_S3_database" --mode s3

# =============================================================
# PART 3: V9 experiments — S1 full simulation via ctx-editor
# =============================================================
echo "============================================"
echo "Part 3: V9 S1 (full simulation)"
echo "============================================"

# S1 v9 needs full simulation (analysis at every turn)
for task in math code database actions; do
    echo "[$(date +%H:%M:%S)] Starting: v9_S1_${task} ..."
    ctx-editor experiment=append_analysis_v9 task=dev_${task} model=gpt5_mini \
        execution.max_concurrent=${MAX_CONCURRENT} \
        2>&1 | tee "${LOG_DIR}/v9_S1_${task}.log"
    echo "[$(date +%H:%M:%S)] Finished: v9_S1_${task}"
    echo ""
done

# Find the most recent v9 S1 output directories
echo "Finding v9 S1 output directories..."
V9_S1_MATH=$(ls -td outputs/*/  2>/dev/null | head -4 | tail -1)
V9_S1_CODE=$(ls -td outputs/*/  2>/dev/null | head -3 | tail -1)
V9_S1_DB=$(ls -td outputs/*/    2>/dev/null | head -2 | tail -1)
V9_S1_ACT=$(ls -td outputs/*/   2>/dev/null | head -1)

echo "V9 S1 dirs: math=${V9_S1_MATH}, code=${V9_S1_CODE}, db=${V9_S1_DB}, act=${V9_S1_ACT}"

# =============================================================
# PART 4: V9 S1.5 (replay from v9 S1 traces)
# =============================================================
echo "============================================"
echo "Part 4: V9 S1.5 (replay from V9 S1)"
echo "============================================"

# These will be run manually after Part 3 outputs are confirmed
echo ">> Run S1.5 manually after confirming S1 output dirs <<"

# =============================================================
# PART 5: V9 S2 (full simulation)
# =============================================================
echo "============================================"
echo "Part 5: V9 S2 (full simulation)"
echo "============================================"

for task in math code database actions; do
    echo "[$(date +%H:%M:%S)] Starting: v9_S2_${task} ..."
    ctx-editor experiment=context_edit_v2_v9 task=dev_${task} model=gpt5_mini \
        execution.max_concurrent=${MAX_CONCURRENT} \
        execution.replay_source=outputs/2026-03-16/19-26-46 \
        2>&1 | tee "${LOG_DIR}/v9_S2_${task}.log"
    echo "[$(date +%H:%M:%S)] Finished: v9_S2_${task}"
    echo ""
done

echo ""
echo "============================================================"
echo "All automated runs complete!"
echo "Remaining: V9 S1.5 and S3 (replay from V9 S1 traces)"
echo "Logs: ${LOG_DIR}/"
echo "============================================================"

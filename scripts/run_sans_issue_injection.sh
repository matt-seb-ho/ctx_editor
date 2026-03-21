#!/bin/bash
# Sans-Issue-Injection Redux: Re-run all S1.5 experiments with --no-notes
#
# Fixes:
#   1. --no-notes: Do not inject <context_edit_notes> (issues) into system message
#   2. --sanitize: Strip clarification-seeking patterns from analysis
#   3. --no-clarification: Tell assistant not to ask clarifying questions
#   4. --accumulate: For actions, include all function calls in response
#
# 14 runs total:
#   v8_batch: 8 (4 no-mem + 4 +mem, actions gets --accumulate)
#   soft_attention: 6 (3 S1.5-single + 3 S1.5-soft)

set -uo pipefail

LOG_DIR="outputs/replay_logs/sans_issue_$(date +%Y-%m-%d_%H-%M-%S)"
mkdir -p "$LOG_DIR"

COMMON_FLAGS="--no-notes --sanitize --no-clarification"
MODEL="gpt-5-mini"
MAX_CONCURRENT=8

echo "============================================================"
echo "Sans-Issue-Injection Redux (14 runs)"
echo "Flags: ${COMMON_FLAGS}"
echo "Logs: ${LOG_DIR}/"
echo "============================================================"
echo ""

run() {
    local s1_dir="$1"
    local task="$2"
    local label="$3"
    shift 3
    local extra_flags="$*"
    local logfile="${LOG_DIR}/${label}.log"

    echo "=========================================="
    echo "[$(date +%H:%M:%S)] Starting: ${label}"
    echo "  Source: ${s1_dir}"
    echo "  Flags: ${COMMON_FLAGS} ${extra_flags}"
    echo "=========================================="

    python scripts/run_s15_experiment.py \
        --s1-dir "${s1_dir}" \
        --task "${task}" \
        --model "${MODEL}" \
        --label "${label}" \
        --max-concurrent ${MAX_CONCURRENT} \
        ${COMMON_FLAGS} \
        ${extra_flags} \
        2>&1 | tee "${logfile}"
    local exit_code=$?

    echo "[$(date +%H:%M:%S)] Finished: ${label} (exit=${exit_code})"
    echo ""
}

# ===== V8 BATCH: S1.5 no-mem =====
echo "============================================"
echo "Phase 1: V8 Batch — S1.5 (no memory)"
echo "============================================"

run "outputs/2026-03-16/20-08-42" math     "v8_S15_nomem_math"
run "outputs/2026-03-16/20-12-21" code     "v8_S15_nomem_code"
run "outputs/2026-03-16/20-25-09" database "v8_S15_nomem_database"
run "outputs/2026-03-16/20-29-27" actions  "v8_S15_nomem_actions" --accumulate

# ===== V8 BATCH: S1.5+mem =====
echo "============================================"
echo "Phase 2: V8 Batch — S1.5 + memory"
echo "============================================"

run "outputs/2026-03-16/20-33-21" math     "v8_S15_mem_math"
run "outputs/2026-03-16/20-42-35" code     "v8_S15_mem_code"
run "outputs/2026-03-16/20-52-20" database "v8_S15_mem_database"
run "outputs/2026-03-16/21-02-17" actions  "v8_S15_mem_actions" --accumulate

# ===== SOFT ATTENTION: S1.5 from S1-single =====
echo "============================================"
echo "Phase 3: Soft Attention — S1.5 from S1-single"
echo "============================================"

run "outputs/2026-03-17/03-02-33" math     "soft_S15_single_math"
run "outputs/2026-03-17/03-02-34" code     "soft_S15_single_code"
run "outputs/2026-03-17/03-02-35" database "soft_S15_single_database"

# ===== SOFT ATTENTION: S1.5 from S1-soft =====
echo "============================================"
echo "Phase 4: Soft Attention — S1.5 from S1-soft"
echo "============================================"

run "outputs/2026-03-17/04-12-12" math     "soft_S15_soft_math"
run "outputs/2026-03-17/04-12-14" code     "soft_S15_soft_code"
run "outputs/2026-03-17/04-12-14" database "soft_S15_soft_database"

echo ""
echo "============================================================"
echo "All 14 runs complete!"
echo "Logs: ${LOG_DIR}/"
echo "============================================================"

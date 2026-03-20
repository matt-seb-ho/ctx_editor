#!/bin/bash
# Soft-attention ablation: S1.5 and S3 on S1-single and S1-soft traces
#
# Tests whether context editing (S1.5 programmatic, S3 LLM-based) can rescue
# soft-attention analysis that performs at/below baseline in the S1 (append) setting.
#
# 12 runs total: 3 tasks × 2 analysis sources × 2 context prep modes
#
# Usage:
#   bash scripts/run_soft_attention_s15_s3.sh

set -uo pipefail

LOG_DIR="outputs/replay_logs/soft_s15_s3_$(date +%Y-%m-%d_%H-%M-%S)"
mkdir -p "$LOG_DIR"

echo "============================================================"
echo "Soft-Attention S1.5 + S3 Ablation (12 runs)"
echo "Logs: ${LOG_DIR}/"
echo "============================================================"
echo ""

run() {
    local mode="$1"
    local s1_dir="$2"
    local task="$3"
    local label="$4"
    local logfile="${LOG_DIR}/${label}.log"

    echo "=========================================="
    echo "[$(date +%H:%M:%S)] Starting: ${label} (mode=${mode})"
    echo "=========================================="

    python scripts/run_s15_experiment.py \
        --mode "${mode}" \
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

# --- S1-single source dirs (1q, soft attention) ---
S1_SINGLE_MATH="outputs/2026-03-17/03-02-33"
S1_SINGLE_CODE="outputs/2026-03-17/03-02-34"
S1_SINGLE_DB="outputs/2026-03-17/03-02-35"

# --- S1-soft source dirs (2q, soft attention) ---
S1_SOFT_MATH="outputs/2026-03-17/04-12-12"
S1_SOFT_CODE="outputs/2026-03-17/04-12-14"
S1_SOFT_DB="outputs/2026-03-17/04-12-14"

echo "============================================"
echo "Phase 1: S1.5 (programmatic compaction)"
echo "============================================"

# S1.5 from S1-single traces
run s15 "$S1_SINGLE_MATH" math     "S15_single_math"
run s15 "$S1_SINGLE_CODE" code     "S15_single_code"
run s15 "$S1_SINGLE_DB"   database "S15_single_database"

# S1.5 from S1-soft traces
run s15 "$S1_SOFT_MATH" math     "S15_soft_math"
run s15 "$S1_SOFT_CODE" code     "S15_soft_code"
run s15 "$S1_SOFT_DB"   database "S15_soft_database"

echo "============================================"
echo "Phase 2: S3 (LLM compaction)"
echo "============================================"

# S3 from S1-single traces
run s3 "$S1_SINGLE_MATH" math     "S3_single_math"
run s3 "$S1_SINGLE_CODE" code     "S3_single_code"
run s3 "$S1_SINGLE_DB"   database "S3_single_database"

# S3 from S1-soft traces
run s3 "$S1_SOFT_MATH" math     "S3_soft_math"
run s3 "$S1_SOFT_CODE" code     "S3_soft_code"
run s3 "$S1_SOFT_DB"   database "S3_soft_database"

echo ""
echo "============================================================"
echo "All 12 runs complete!"
echo "Logs: ${LOG_DIR}/"
echo "============================================================"

#!/bin/bash
# Spec-Curation Memory Experiment
#
# Tests whether memory-based learning can teach the soft-attention analyzer
# to resist assistant contamination and produce cleaner task specs.
#
# Design:
#   Phase 1 (TRAIN): Run soft-attention S1-speconly on the TRAIN split.
#     Memory learns from each batch, grounded by oracle hard-attention specs.
#   Phase 2 (EVAL): Run soft-attention+memory S1-speconly on the TEST split.
#     Compare against: soft-no-memory (baseline) and hard-attention (upper bound).
#
# The experiment uses v8_soft_cot (CoT decontamination prompt) as the soft
# attention variant, with memory injected into the spec query (Query 1).
#
# Usage:
#   bash scripts/run_spec_curation_memory_experiment.sh

set -euo pipefail

MODEL=gpt5_mini
MAX_CONCURRENT=8
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
MEM_BASE="outputs/spec_curation_mem/${TIMESTAMP}"

echo "=========================================="
echo "Spec-Curation Memory Experiment"
echo "Timestamp: ${TIMESTAMP}"
echo "Memory save base: ${MEM_BASE}"
echo "=========================================="

# ─────────────────────────────────────────────────
# PHASE 1: Train memory on TRAIN split
# ─────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════"
echo "PHASE 1: Training memory on train splits"
echo "═══════════════════════════════════════════"

for TASK in math code database; do
    echo ""
    echo "--- Training memory: ${TASK} ---"
    ctx-editor experiment=append_analysis_soft_cot_spec_mem task=dev_${TASK}_train model=${MODEL} \
        execution.replay_source=data/baseline_traces_v2/${TASK}_train \
        execution.mode=batched execution.batch_size=5 \
        execution.max_concurrent=${MAX_CONCURRENT} logging.verbose=true \
        memory.enabled=true memory.source=continual \
        memory.target=spec_curation \
        memory.save_path=${MEM_BASE}/train_${TASK}_cheatsheet.json \
        memory.include_oracle_spec=true \
        memory.oracle_spec_path=data/oracle_specs/all_oracle_specs.json \
        memory.include_full_spec_q=true memory.include_ground_truth_a=true
done

echo ""
echo "Phase 1 complete. Trained memories saved to ${MEM_BASE}/"

# ─────────────────────────────────────────────────
# PHASE 2: Evaluate on TEST split
# ─────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════"
echo "PHASE 2: Evaluating on test splits"
echo "═══════════════════════════════════════════"

for TASK in math code database; do
    echo ""
    echo "--- Eval: S1-soft-cot (no memory) on ${TASK} test ---"
    ctx-editor experiment=append_analysis_soft_cot task=dev_${TASK}_test model=${MODEL} \
        execution.replay_source=data/baseline_traces_v2/${TASK}_test \
        execution.mode=parallel execution.max_concurrent=${MAX_CONCURRENT} \
        logging.verbose=true

    echo ""
    echo "--- Eval: S1-soft-cot+memory on ${TASK} test ---"
    ctx-editor experiment=append_analysis_soft_cot_spec_mem task=dev_${TASK}_test model=${MODEL} \
        execution.replay_source=data/baseline_traces_v2/${TASK}_test \
        execution.mode=parallel execution.max_concurrent=${MAX_CONCURRENT} \
        logging.verbose=true \
        memory.enabled=true memory.source=${MEM_BASE}/train_${TASK}_cheatsheet.json \
        memory.target=spec_curation

    echo ""
    echo "--- Eval: S1-speconly (hard attention, upper bound) on ${TASK} test ---"
    ctx-editor experiment=append_analysis_spec_only task=dev_${TASK}_test model=${MODEL} \
        execution.replay_source=data/baseline_traces_v2/${TASK}_test \
        execution.mode=parallel execution.max_concurrent=${MAX_CONCURRENT} \
        logging.verbose=true
done

echo ""
echo "=========================================="
echo "Experiment complete."
echo "Results in outputs/ directories timestamped during this run."
echo ""
echo "Compare across conditions:"
echo "  - S1-soft-cot (no memory): soft attention baseline"
echo "  - S1-soft-cot+memory: our intervention"
echo "  - S1-speconly (hard attention): oracle upper bound"
echo ""
echo "Also compare against S0 (baseline) test results from prior runs."
echo "=========================================="

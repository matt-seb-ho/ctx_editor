#!/bin/bash
# Spec-Curation Memory: Evaluation V2
#
# Two ablations on the test splits:
#
# A) S1 with analysis AFTER last user message (flipped ordering)
#    - S1-soft-cot (no mem), S1-soft-cot+mem, S1-speconly (hard attn)
#
# B) S1.5 (spec-only reset): conversation replaced with just the task spec
#    - Uses S1 traces from Part A as source for the analysis
#    - S1.5-soft-cot (no mem), S1.5-soft-cot+mem, S1.5-speconly (hard attn)
#
# Requires: trained memories from run_spec_curation_memory_experiment.sh
#
# Usage:
#   bash scripts/run_spec_curation_eval_v2.sh <MEM_BASE>
#   e.g. bash scripts/run_spec_curation_eval_v2.sh outputs/spec_curation_mem/2026-03-17_21-51-41

set -euo pipefail

MEM_BASE="${1:?Usage: $0 <MEM_BASE path to trained memories>}"
MODEL=gpt5_mini
ASSISTANT_MODEL=gpt-5-mini
MAX_CONCURRENT=8

# Helper: find the most recently created output dir
latest_output_dir() {
    ls -dt outputs/????-??-??/??-??-??/ 2>/dev/null | head -1
}

echo "=========================================="
echo "Spec-Curation Eval V2"
echo "Memory base: ${MEM_BASE}"
echo "=========================================="

# ─────────────────────────────────────────────────
# PART A: S1 with analysis AFTER last user message
# ─────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════"
echo "PART A: S1 with analysis AFTER last user msg"
echo "═══════════════════════════════════════════"

declare -A S1_DIRS

for TASK in math code database; do
    echo ""
    echo "--- A1: S1-soft-cot-after (no mem) ${TASK} test ---"
    ctx-editor experiment=append_analysis_soft_cot_after task=dev_${TASK}_test model=${MODEL} \
        execution.replay_source=data/baseline_traces_v2/${TASK}_test \
        execution.mode=parallel execution.max_concurrent=${MAX_CONCURRENT} \
        logging.verbose=true
    S1_DIRS["${TASK}_soft"]="$(latest_output_dir)"
    echo "  → output: ${S1_DIRS[${TASK}_soft]}"

    echo ""
    echo "--- A2: S1-soft-cot+mem-after ${TASK} test ---"
    ctx-editor experiment=append_analysis_soft_cot_spec_mem_after task=dev_${TASK}_test model=${MODEL} \
        execution.replay_source=data/baseline_traces_v2/${TASK}_test \
        execution.mode=parallel execution.max_concurrent=${MAX_CONCURRENT} \
        logging.verbose=true \
        memory.enabled=true memory.source=${MEM_BASE}/train_${TASK}_cheatsheet.json \
        memory.target=spec_curation
    S1_DIRS["${TASK}_mem"]="$(latest_output_dir)"
    echo "  → output: ${S1_DIRS[${TASK}_mem]}"

    echo ""
    echo "--- A3: S1-speconly-after (hard attn) ${TASK} test ---"
    ctx-editor experiment=append_analysis_spec_only_after task=dev_${TASK}_test model=${MODEL} \
        execution.replay_source=data/baseline_traces_v2/${TASK}_test \
        execution.mode=parallel execution.max_concurrent=${MAX_CONCURRENT} \
        logging.verbose=true
    S1_DIRS["${TASK}_hard"]="$(latest_output_dir)"
    echo "  → output: ${S1_DIRS[${TASK}_hard]}"
done

echo ""
echo "Part A complete. S1 output dirs:"
for key in "${!S1_DIRS[@]}"; do
    echo "  ${key}: ${S1_DIRS[${key}]}"
done

# ─────────────────────────────────────────────────
# PART B: S1.5 (spec-only reset)
# ─────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════"
echo "PART B: S1.5 (reset context, spec only)"
echo "═══════════════════════════════════════════"

for TASK in math code database; do
    echo ""
    echo "--- B1: S1.5-soft-cot (no mem) ${TASK} test ---"
    python scripts/run_s15_experiment.py \
        --s1-dir "${S1_DIRS[${TASK}_soft]}" \
        --task ${TASK} --model ${ASSISTANT_MODEL} \
        --label "S15_soft_cot_${TASK}" --max-concurrent ${MAX_CONCURRENT}

    echo ""
    echo "--- B2: S1.5-soft-cot+mem ${TASK} test ---"
    python scripts/run_s15_experiment.py \
        --s1-dir "${S1_DIRS[${TASK}_mem]}" \
        --task ${TASK} --model ${ASSISTANT_MODEL} \
        --label "S15_soft_cot_mem_${TASK}" --max-concurrent ${MAX_CONCURRENT}

    echo ""
    echo "--- B3: S1.5-speconly (hard attn) ${TASK} test ---"
    python scripts/run_s15_experiment.py \
        --s1-dir "${S1_DIRS[${TASK}_hard]}" \
        --task ${TASK} --model ${ASSISTANT_MODEL} \
        --label "S15_speconly_hard_${TASK}" --max-concurrent ${MAX_CONCURRENT}
done

echo ""
echo "=========================================="
echo "All done. Check outputs/ for results."
echo "=========================================="

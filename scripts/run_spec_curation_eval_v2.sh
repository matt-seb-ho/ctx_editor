#!/bin/bash
# Spec-Curation Memory: Evaluation V2
#
# A) S1 with analysis AFTER last user message (flipped ordering)
# B) S1.5 (spec-only reset) using S1 traces from Part A
#
# Usage:
#   bash scripts/run_spec_curation_eval_v2.sh <MEM_BASE>

set -euo pipefail

MEM_BASE="${1:?Usage: $0 <MEM_BASE path to trained memories>}"
MODEL=gpt5_mini
ASSISTANT_MODEL=gpt-5-mini
MAX_CONCURRENT=8

LOGFILE=$(mktemp)
trap "rm -f $LOGFILE" EXIT

# Run ctx-editor, show output, and extract the output dir
run_ctx() {
    ctx-editor "$@" 2>&1 | tee "$LOGFILE"
    # Extract output dir — python avoids SIGPIPE issues with pipefail
    python3 -c "
import re, sys
text = open('$LOGFILE').read()
m = re.findall(r'Results saved to: (.+)', text)
print(m[-1] if m else '')
"
}

echo "=========================================="
echo "Spec-Curation Eval V2"
echo "=========================================="

declare -A S1_DIRS

# ── PART A: S1 with analysis AFTER last user message ──

for TASK in math code database; do
    echo ""
    echo "=== A1: S1-soft-cot-after (no mem) ${TASK} test ==="
    S1_DIRS["${TASK}_soft"]="$(run_ctx \
        experiment=append_analysis_soft_cot_after task=dev_${TASK}_test model=${MODEL} \
        execution.replay_source=data/baseline_traces_v2/${TASK}_test \
        execution.mode=parallel execution.max_concurrent=${MAX_CONCURRENT} \
        logging.verbose=true)"
    echo "Dir: ${S1_DIRS[${TASK}_soft]}"

    echo ""
    echo "=== A2: S1-soft-cot+mem-after ${TASK} test ==="
    S1_DIRS["${TASK}_mem"]="$(run_ctx \
        experiment=append_analysis_soft_cot_spec_mem_after task=dev_${TASK}_test model=${MODEL} \
        execution.replay_source=data/baseline_traces_v2/${TASK}_test \
        execution.mode=parallel execution.max_concurrent=${MAX_CONCURRENT} \
        logging.verbose=true \
        memory.enabled=true memory.source=${MEM_BASE}/train_${TASK}_cheatsheet.json \
        memory.target=spec_curation)"
    echo "Dir: ${S1_DIRS[${TASK}_mem]}"

    echo ""
    echo "=== A3: S1-speconly-after (hard attn) ${TASK} test ==="
    S1_DIRS["${TASK}_hard"]="$(run_ctx \
        experiment=append_analysis_spec_only_after task=dev_${TASK}_test model=${MODEL} \
        execution.replay_source=data/baseline_traces_v2/${TASK}_test \
        execution.mode=parallel execution.max_concurrent=${MAX_CONCURRENT} \
        logging.verbose=true)"
    echo "Dir: ${S1_DIRS[${TASK}_hard]}"
done

echo ""
echo "Part A complete."
echo ""

# ── PART B: S1.5 (spec-only reset) ──

for TASK in math code database; do
    echo "=== B1: S1.5-soft-cot (no mem) ${TASK} test ==="
    python scripts/run_s15_experiment.py \
        --s1-dir "${S1_DIRS[${TASK}_soft]}" \
        --task ${TASK} --model ${ASSISTANT_MODEL} \
        --label "S15_soft_cot_${TASK}" --max-concurrent ${MAX_CONCURRENT}

    echo ""
    echo "=== B2: S1.5-soft-cot+mem ${TASK} test ==="
    python scripts/run_s15_experiment.py \
        --s1-dir "${S1_DIRS[${TASK}_mem]}" \
        --task ${TASK} --model ${ASSISTANT_MODEL} \
        --label "S15_soft_cot_mem_${TASK}" --max-concurrent ${MAX_CONCURRENT}

    echo ""
    echo "=== B3: S1.5-speconly (hard attn) ${TASK} test ==="
    python scripts/run_s15_experiment.py \
        --s1-dir "${S1_DIRS[${TASK}_hard]}" \
        --task ${TASK} --model ${ASSISTANT_MODEL} \
        --label "S15_speconly_hard_${TASK}" --max-concurrent ${MAX_CONCURRENT}
    echo ""
done

echo "All done."

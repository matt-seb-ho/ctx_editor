#!/bin/bash
# Spec-targeted memory experiment: Memory injected into task spec query (Query 1)
# instead of comparison query (Query 2).
#
# Tests whether memory helps more when it informs task spec consolidation
# vs. when it informs the comparison/issues analysis.
#
# Runs S1+spec_mem across math, code, database (same settings as v8 batch).
# After S1 runs complete, use S1.5 script on the output dirs.
#
# Usage:
#   bash scripts/run_spec_mem_experiment.sh

set -euo pipefail

MODEL=gpt5_mini
MAX_CONCURRENT=8
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
MEM_BASE="outputs/replay_memories/spec_mem_${TIMESTAMP}"

echo "=========================================="
echo "Spec-Targeted Memory: S1+spec_mem"
echo "Memory save base: ${MEM_BASE}"
echo "=========================================="

for TASK in math code database; do
    echo ""
    echo "--- S1+spec_mem ${TASK} ---"
    ctx-editor experiment=append_analysis_spec_mem task=dev_${TASK} model=${MODEL} \
        execution.replay_source=data/baseline_traces_v2/${TASK} \
        execution.mode=batched execution.batch_size=5 \
        execution.max_concurrent=${MAX_CONCURRENT} logging.verbose=true \
        memory.enabled=true memory.source=continual memory.target=analyzer \
        memory.save_path=${MEM_BASE}/${TASK} \
        memory.include_full_spec_q=true memory.include_ground_truth_a=true
done

echo ""
echo "=========================================="
echo "S1+spec_mem runs complete."
echo ""
echo "Now run S1.5 using the S1+spec_mem output dirs:"
echo "  python scripts/run_s15_experiment.py --s1-dir <S1_SPEC_MEM_OUTPUT_DIR> --task <TASK> --model gpt-5-mini --label S15_spec_mem_<TASK>"
echo "=========================================="

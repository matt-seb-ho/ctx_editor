#!/bin/bash
# Single-query analysis ablation: S1-single and S1.5-single across all 4 tasks.
#
# Compares against the two-query S1/S1.5 results from the v8 batch.
# Tests whether the "hard attention" separation (task spec query sees only user
# messages) matters, or if a single combined query can match performance.
#
# Usage:
#   bash scripts/run_single_query_ablation.sh
#
# After S1-single runs complete, run S1.5-single using the S1-single output dirs.

set -euo pipefail

MODEL=gpt5_mini
MAX_CONCURRENT=8

echo "=========================================="
echo "Single-Query Ablation: S1-single (no mem)"
echo "=========================================="

# S1-single no-memory: all 4 tasks
for TASK in math code database actions; do
    echo ""
    echo "--- S1-single ${TASK} (no mem) ---"
    ctx-editor experiment=append_analysis_single task=dev_${TASK} model=${MODEL} \
        execution.replay_source=data/baseline_traces_v2/${TASK} \
        execution.max_concurrent=${MAX_CONCURRENT} logging.verbose=true
done

echo ""
echo "=========================================="
echo "Single-Query Ablation: S1-single (+ mem)"
echo "=========================================="

# S1-single with memory: all 4 tasks
for TASK in math code database actions; do
    echo ""
    echo "--- S1-single ${TASK} (+ mem) ---"
    ctx-editor experiment=append_analysis_single_memory task=dev_${TASK} model=${MODEL} \
        execution.replay_source=data/baseline_traces_v2/${TASK} \
        execution.mode=batched execution.batch_size=5 \
        memory.enabled=true memory.source=continual memory.target=analyzer \
        memory.save_path=outputs/replay_memories/single_query_ablation/${TASK} \
        memory.include_full_spec_q=true memory.include_ground_truth_a=true
done

echo ""
echo "=========================================="
echo "S1-single runs complete."
echo ""
echo "Now run S1.5-single using the S1-single output dirs:"
echo "  python scripts/run_s15_experiment.py --s1-dir <S1_SINGLE_OUTPUT_DIR> --task <TASK> --model gpt-5-mini --label S15_single_nomem_<TASK>"
echo "=========================================="

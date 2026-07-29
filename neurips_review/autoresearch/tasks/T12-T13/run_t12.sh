#!/bin/bash
# T12 — memory order-sensitivity, online (paper-faithful) protocol.
# Usage: bash run_t12.sh <task: database|math>
set -uo pipefail
cd /home/t-matthewho/ac3/ctx_editor
. .venv/bin/activate

TASK="${1:?usage: run_t12.sh <database|math>}"
D=neurips_review/autoresearch/tasks/T12-T13
OUT=outputs/T12_T13/${TASK}
MEM=${D}/memories/${TASK}
mkdir -p "${OUT}" "${MEM}"

COMMON=(
  model=gpt5_4_mini_trapi
  load_balancer=trapi
  task=dev_${TASK}
  execution.replay_source=data/baseline_traces_v2/${TASK}
  execution.replay_turns=1
  execution.max_concurrent=5
  false_negative_analysis.model=gpt-5.4-mini_2026-03-17
  logging.verbose=false
  metadata.branch=T12_T13
)

# 1. No-memory reference (analysis cache disabled for a fair comparison)
if [[ ! -f ${OUT}/ref_nomem/run_summary.json ]]; then
  echo "=== [$(date +%T)] ref_nomem ${TASK}"
  ctx-editor experiment=append_analysis "${COMMON[@]}" \
    task.data_file=${D}/data/dev_${TASK}_ord0.json \
    experiment.strategy.analysis_cache_dir=null \
    execution.mode=parallel \
    experiment_name=T12_ref_nomem_${TASK} \
    logging.output_dir=${OUT}/ref_nomem 2>&1 | tail -25
fi

# 2. Memory arms, one per trajectory ordering
for ORD in ord0 ord1001 ord1002 ord1003; do
  if [[ -f ${OUT}/mem_${ORD}/run_summary.json ]]; then echo "skip ${ORD}"; continue; fi
  echo "=== [$(date +%T)] mem_${ORD} ${TASK}"
  ctx-editor experiment=append_analysis_memory "${COMMON[@]}" \
    task.data_file=${D}/data/dev_${TASK}_${ORD}.json \
    execution.mode=batched execution.batch_size=5 \
    memory.enabled=true memory.source=continual memory.target=analyzer \
    memory.include_full_spec_q=true memory.include_ground_truth_a=true \
    memory.save_path=${MEM}/${ORD}_cheatsheet.json \
    experiment_name=T12_mem_${ORD}_${TASK} \
    logging.output_dir=${OUT}/mem_${ORD} 2>&1 | tail -25
done

echo "=== [$(date +%T)] T12 ${TASK} done"
grep -H -E 'Accuracy|Adjusted' ${OUT}/*/summary.txt 2>/dev/null

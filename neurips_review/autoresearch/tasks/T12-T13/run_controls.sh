#!/bin/bash
# Variance controls for T12: how much of the across-ordering spread is *ordering*
# and how much is temperature-1.0 sampling noise?
#   A. same frozen cheatsheet, repeated eval      -> pure eval-sampling noise
#   B. same ordering, cheatsheet relearned        -> ordering-fixed total noise
# Usage: bash run_controls.sh <task: database|math>
set -uo pipefail
cd /home/t-matthewho/ac3/ctx_editor
. .venv/bin/activate

TASK="${1:?usage: run_controls.sh <database|math>}"
D=neurips_review/autoresearch/tasks/T12-T13
OUT=outputs/T12_T13/${TASK}
MEM=${D}/memories/${TASK}

COMMON=(
  model=gpt5_4_mini_trapi
  load_balancer=trapi
  task=dev_${TASK}
  execution.replay_source=data/baseline_traces_v2/${TASK}
  execution.replay_turns=1
  execution.max_concurrent=5
  false_negative_analysis.model=gpt-5.4-mini_2026-03-17
  metadata.branch=T12_T13
)

# A. identical frozen cheatsheet (offline ord0), 3 independent evals
for REP in rep1 rep2 rep3; do
  [[ -f ${OUT}/ctrlA_${REP}/run_summary.json ]] && { echo "skip ctrlA_${REP}"; continue; }
  echo "=== [$(date +%T)] ctrlA_${REP} (${TASK}) fixed cheatsheet, resampled eval"
  ctx-editor experiment=append_analysis_memory "${COMMON[@]}" \
    task.data_file=${D}/data/dev_${TASK}_ord0.json \
    execution.mode=parallel \
    memory.enabled=true memory.source=${MEM}/offline_ord0_cheatsheet.json memory.target=analyzer \
    experiment_name=T12_ctrlA_${REP}_${TASK} \
    logging.output_dir=${OUT}/ctrlA_${REP} 2>&1 | tail -8
done

# B. identical ordering (ord0), cheatsheet relearned online each time
for REP in rep2 rep3; do
  [[ -f ${OUT}/ctrlB_${REP}/run_summary.json ]] && { echo "skip ctrlB_${REP}"; continue; }
  echo "=== [$(date +%T)] ctrlB_${REP} (${TASK}) fixed ordering, relearned cheatsheet"
  ctx-editor experiment=append_analysis_memory "${COMMON[@]}" \
    task.data_file=${D}/data/dev_${TASK}_ord0.json \
    execution.mode=batched execution.batch_size=5 \
    memory.enabled=true memory.source=continual memory.target=analyzer \
    memory.include_full_spec_q=true memory.include_ground_truth_a=true \
    memory.save_path=${MEM}/ord0_${REP}_cheatsheet.json \
    experiment_name=T12_ctrlB_${REP}_${TASK} \
    logging.output_dir=${OUT}/ctrlB_${REP} 2>&1 | tail -8
done

echo "=== [$(date +%T)] controls ${TASK} done"

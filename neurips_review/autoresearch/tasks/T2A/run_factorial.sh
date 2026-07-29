#!/usr/bin/env bash
# T2A — Baseline (no editing) across the single-span arms, completing the
# 2x2 factorial {harmful present/absent} x {useful present/absent}. This is a
# detector-free measurement of what each injected span is worth.
set -u
cd /home/t-matthewho/ac3/ctx_editor
. .venv/bin/activate
[[ -f .env ]] && { set -a; source .env; set +a; }
LOG=neurips_review/autoresearch/tasks/T2A/run_factorial.log
: > "$LOG"
declare -A DATAFILE=( [database_v2]=data/htn50_52_database_subset.json \
                      [code_v2]=data/htn50_52_code_subset.json )
for ARM in harm_only use_only; do
  for TASK in database_v2 code_v2; do
    for CONV in conv0 conv1; do
      OUT=outputs/T2A/base_${ARM}_${TASK}_${CONV}
      [[ -f $OUT/run_summary.json ]] && { echo "SKIP $OUT" | tee -a "$LOG"; continue; }
      echo "=== $(date +%H:%M:%S) START $OUT" | tee -a "$LOG"
      ctx-editor experiment=baseline \
        model=gpt5_4_mini_trapi load_balancer=trapi \
        task=$TASK task.data_file=${DATAFILE[$TASK]} \
        execution.replay_source=data/t2a_${ARM}/$TASK/$CONV execution.replay_turns=1 \
        execution.max_concurrent=5 \
        false_negative_analysis.model=gpt-5.4-mini_2026-03-17 \
        experiment_name=T2A_base_${ARM}_${TASK}_${CONV} \
        logging.output_dir=$OUT >>"$LOG" 2>&1
      echo "=== $(date +%H:%M:%S) DONE  $OUT rc=$?" | tee -a "$LOG"
    done
  done
done
echo "FACTORIAL ALL DONE $(date +%H:%M:%S)" | tee -a "$LOG"

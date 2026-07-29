#!/usr/bin/env bash
# T2A — second arm: AC3-Rewrite (S3, ContextCompactionStrategy) on the injected
# conversations. Rewrite *compacts* rather than resetting, so it is the natural
# contrast for "is AC3's removal rate just an artifact of deleting everything?".
# analysis_cache_dir is forced to null: the shipped config points at
# outputs/analysis_cache, which was built with a different model/prompt and
# would silently serve stale analyses.
set -u
cd /home/t-matthewho/ac3/ctx_editor
. .venv/bin/activate
[[ -f .env ]] && { set -a; source .env; set +a; }
LOG=neurips_review/autoresearch/tasks/T2A/run_rewrite.log
: > "$LOG"
declare -A DATAFILE=( [database_v2]=data/htn50_52_database_subset.json \
                      [code_v2]=data/htn50_52_code_subset.json )
for ARM in injected clean; do
  case $ARM in injected) SRC=data/t2a_injected ;; clean) SRC=data/t2a_clean ;; esac
  for TASK in database_v2 code_v2; do
    for CONV in conv0 conv1; do
      OUT=outputs/T2A/rw_${ARM}_${TASK}_${CONV}
      [[ -f $OUT/run_summary.json ]] && { echo "SKIP $OUT" | tee -a "$LOG"; continue; }
      echo "=== $(date +%H:%M:%S) START $OUT" | tee -a "$LOG"
      ctx-editor \
        experiment=ac3_rewrite_v8_lic \
        experiment.strategy.analysis_cache_dir=null \
        model=gpt5_4_mini_trapi load_balancer=trapi \
        task=$TASK task.data_file=${DATAFILE[$TASK]} \
        execution.replay_source=$SRC/$TASK/$CONV execution.replay_turns=1 \
        execution.max_concurrent=5 \
        false_negative_analysis.model=gpt-5.4-mini_2026-03-17 \
        experiment_name=T2A_rw_${ARM}_${TASK}_${CONV} \
        logging.output_dir=$OUT >>"$LOG" 2>&1
      echo "=== $(date +%H:%M:%S) DONE  $OUT rc=$?" | tee -a "$LOG"
    done
  done
done
echo "REWRITE ALL DONE $(date +%H:%M:%S)" | tee -a "$LOG"

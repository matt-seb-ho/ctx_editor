#!/usr/bin/env bash
# T2B — AC3 arms on the *present* corpus, for the alignment table.
# These runs produce nothing that enters a causal label; they are only read to
# find out which spans AC3 carried forward and which it dropped.
#   AC3-Reset   = context_edit_v2_no_gate   (rebuilds the context)
#   AC3-Rewrite = ac3_rewrite_v8_lic        (compacts the context)
# analysis_cache_dir is forced to null for Rewrite, per T2A/run_rewrite.sh: the
# shipped config points at a cache built with a different model/prompt.
set -u
cd /home/t-matthewho/ac3/ctx_editor
. .venv/bin/activate
LOG=neurips_review/autoresearch/tasks/T2B/run_ac3.log
touch "$LOG"
declare -A DATAFILE=( [database_v2]=data/htn50_52_database_subset.json \
                      [code_v2]=data/htn50_52_code_subset.json )
R_AC3=${R_AC3:-3}
for (( R=1; R<=R_AC3; R++ )); do
  for TASK in database_v2 code_v2; do
    for ARM in reset rewrite; do
      case $ARM in
        reset)   EXTRA=(experiment=context_edit_v2_no_gate) ;;
        rewrite) EXTRA=(experiment=ac3_rewrite_v8_lic experiment.strategy.analysis_cache_dir=null) ;;
      esac
      OUT=outputs/T2B/ac3${ARM}_${TASK}_r${R}
      [[ -f $OUT/run_summary.json ]] && { echo "SKIP $OUT" | tee -a "$LOG"; continue; }
      echo "=== $(date +%H:%M:%S) START $OUT" | tee -a "$LOG"
      ctx-editor "${EXTRA[@]}" \
        model=gpt5_4_mini_trapi load_balancer=trapi \
        task=$TASK task.data_file=${DATAFILE[$TASK]} \
        execution.replay_source=data/t2b_present/$TASK execution.replay_turns=1 \
        execution.max_concurrent=${CONC:-3} \
        false_negative_analysis.model=gpt-5.4-mini_2026-03-17 \
        experiment_name=T2B_ac3${ARM}_${TASK}_r${R} \
        logging.output_dir=$OUT >>"$LOG" 2>&1
      echo "=== $(date +%H:%M:%S) DONE  $OUT rc=$?" | tee -a "$LOG"
    done
  done
done
echo "AC3 ALL DONE $(date +%H:%M:%S)" | tee -a "$LOG"

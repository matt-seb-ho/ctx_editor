#!/usr/bin/env bash
# T2B — pilot: N replicate runs of the *unablated* prefix, used ONLY to select
# conversations with headroom in both directions (present-accuracy strictly
# between floor and ceiling). Pilot data is DISCARDED for the analysis; fresh
# present-condition replicates are run afterwards so selection cannot induce
# regression-to-the-mean bias in the measured effect.
set -u
cd /home/t-matthewho/ac3/ctx_editor
. .venv/bin/activate
[[ -f .env ]] && { set -a; source .env; set +a; }
LOG=neurips_review/autoresearch/tasks/T2B/run_pilot.log
: > "$LOG"
declare -A DATAFILE=( [database_v2]=data/htn50_52_database_subset.json \
                      [code_v2]=data/htn50_52_code_subset.json )
REPS=${REPS:-6}
for R in $(seq 1 $REPS); do
  for TASK in database_v2 code_v2; do
    OUT=outputs/T2B/pilot_${TASK}_r${R}
    [[ -f $OUT/run_summary.json ]] && { echo "SKIP $OUT" | tee -a "$LOG"; continue; }
    echo "=== $(date +%H:%M:%S) START $OUT" | tee -a "$LOG"
    ctx-editor experiment=baseline \
      model=gpt5_4_mini_trapi load_balancer=trapi \
      task=$TASK task.data_file=${DATAFILE[$TASK]} \
      execution.replay_source=data/t2b_full/$TASK execution.replay_turns=1 \
      execution.max_concurrent=5 \
      false_negative_analysis.model=gpt-5.4-mini_2026-03-17 \
      experiment_name=T2B_pilot_${TASK}_r${R} \
      logging.output_dir=$OUT >>"$LOG" 2>&1
    echo "=== $(date +%H:%M:%S) DONE  $OUT rc=$?" | tee -a "$LOG"
  done
done
echo "PILOT ALL DONE $(date +%H:%M:%S)" | tee -a "$LOG"

#!/usr/bin/env bash
# T2B — main counterfactual span-ablation matrix.
#
# Conditions per task:
#   present            : canonicalised prefix, nothing removed   (reference arm)
#   abl1..ablK         : present minus exactly one natural span
#   ctl_filler         : present + a contentless span  (negative control, expect ~0)
#   ctl_harm           : present + the T2A H_PHANTOM_* span (expect ablation effect > 0)
#   ctl_answer         : present + the fully specified question (+ gold SQL for
#                        database) (expect ablation effect << 0)
# For the three controls the "span removed" arm is `present` itself, so each
# control costs one condition rather than two.
#
# Loop order is REP-MAJOR on purpose: if the session is cut short, every
# condition has the same number of replicates rather than some having none.
#
# Metric is RAW accuracy (trap 2): adjusted_accuracy is not comparable across
# arms, and for span ablation the assistant's raw success rate under a fixed
# prefix is exactly the quantity of interest.
set -u
cd /home/t-matthewho/ac3/ctx_editor
. .venv/bin/activate

LOG=neurips_review/autoresearch/tasks/T2B/run_main.log
touch "$LOG"
declare -A DATAFILE=( [database_v2]=data/htn50_52_database_subset.json \
                      [code_v2]=data/htn50_52_code_subset.json )
K=${K:-4}
R_ABL=${R_ABL:-10}
R_CTL=${R_CTL:-6}
R_PRE=${R_PRE:-12}

run_cell () {  # $1 cond  $2 task  $3 rep
  local COND=$1 TASK=$2 R=$3
  local SRC=data/t2b_${COND}/$TASK
  local OUT=outputs/T2B/${COND}_${TASK}_r${R}
  [[ -d $SRC ]] || { echo "MISSING $SRC" | tee -a "$LOG"; return; }
  [[ -f $OUT/run_summary.json ]] && { echo "SKIP $OUT" | tee -a "$LOG"; return; }
  echo "=== $(date +%H:%M:%S) START $OUT" | tee -a "$LOG"
  ctx-editor experiment=baseline \
    model=gpt5_4_mini_trapi load_balancer=trapi \
    task=$TASK task.data_file=${DATAFILE[$TASK]} \
    execution.replay_source=$SRC execution.replay_turns=1 \
    execution.max_concurrent=5 \
    false_negative_analysis.model=gpt-5.4-mini_2026-03-17 \
    experiment_name=T2B_${COND}_${TASK}_r${R} \
    logging.output_dir=$OUT >>"$LOG" 2>&1
  echo "=== $(date +%H:%M:%S) DONE  $OUT rc=$?" | tee -a "$LOG"
}

MAXR=$R_PRE
for (( R=1; R<=MAXR; R++ )); do
  for TASK in database_v2 code_v2; do
    (( R <= R_PRE )) && run_cell present "$TASK" "$R"
    if (( R <= R_ABL )); then
      for (( J=1; J<=K; J++ )); do run_cell "abl${J}" "$TASK" "$R"; done
    fi
    if (( R <= R_CTL )); then
      for C in ctl_filler ctl_harm ctl_answer; do run_cell "$C" "$TASK" "$R"; done
    fi
  done
done
echo "MAIN ALL DONE $(date +%H:%M:%S)" | tee -a "$LOG"

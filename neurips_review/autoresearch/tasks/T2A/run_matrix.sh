#!/usr/bin/env bash
# T2A — run matrix. 2 arms (injected / clean) x 2 strategies (AC3-Reset / Baseline)
#                  x 2 tasks (database / code) x 2 conversation prefixes.
# Output is T2A-scoped (outputs/T2A/...) so it cannot collide with other agents.
set -u
cd /home/t-matthewho/ac3/ctx_editor
. .venv/bin/activate
[[ -f .env ]] && { set -a; source .env; set +a; }

LOG=neurips_review/autoresearch/tasks/T2A/run_matrix.log
: > "$LOG"

declare -A DATAFILE=( [database_v2]=data/htn50_52_database_subset.json \
                      [code_v2]=data/htn50_52_code_subset.json )

for ARM in injected clean; do
  case $ARM in
    injected) SRCROOT=data/t2a_injected ;;
    clean)    SRCROOT=data/t2a_clean ;;
  esac
  for EXP in context_edit_v2_no_gate baseline; do
    case $EXP in
      context_edit_v2_no_gate) TAG=ac3 ;;
      baseline)                TAG=base ;;
    esac
    for TASK in database_v2 code_v2; do
      for CONV in conv0 conv1; do
        OUT=outputs/T2A/${TAG}_${ARM}_${TASK}_${CONV}
        if [[ -f $OUT/run_summary.json ]]; then
          echo "SKIP $OUT (already complete)" | tee -a "$LOG"; continue
        fi
        echo "=== $(date +%H:%M:%S) START $OUT" | tee -a "$LOG"
        ctx-editor \
          experiment=$EXP \
          model=gpt5_4_mini_trapi load_balancer=trapi \
          task=$TASK task.data_file=${DATAFILE[$TASK]} \
          execution.replay_source=$SRCROOT/$TASK/$CONV \
          execution.replay_turns=1 \
          execution.max_concurrent=5 \
          false_negative_analysis.model=gpt-5.4-mini_2026-03-17 \
          experiment_name=T2A_${TAG}_${ARM}_${TASK}_${CONV} \
          logging.output_dir=$OUT >>"$LOG" 2>&1
        echo "=== $(date +%H:%M:%S) DONE  $OUT rc=$?" | tee -a "$LOG"
        grep -E 'Adjusted Accuracy:|^Accuracy:' $OUT/summary.txt 2>/dev/null | tee -a "$LOG"
      done
    done
  done
done
echo "ALL DONE $(date +%H:%M:%S)" | tee -a "$LOG"

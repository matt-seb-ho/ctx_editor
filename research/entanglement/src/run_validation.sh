#!/usr/bin/env bash
# Validation pass: baseline strategy across entanglement levels, to validate the knob.
set -euo pipefail
cd /home/t-matthewho/ac3/ctx_editor
source .venv/bin/activate

N=${N:-5}
LEVELS=${LEVELS:-"0 1 2 3"}
TASK=${TASK:-dev_math}
EXP=${EXP:-baseline}
OUTROOT=${OUTROOT:-research/entanglement/artifacts/val_${EXP}_${TASK}}
mkdir -p "$OUTROOT"

for lvl in $LEVELS; do
  echo "=== $EXP @ entanglement=$lvl (N=$N, task=$TASK) ==="
  ctx-editor \
    experiment=$EXP model=gpt5_4_mini_trapi task=$TASK load_balancer=trapi \
    user_mode=entangled user_mode.entanglement_level=$lvl \
    task.limit=$N false_negative_analysis.enabled=false \
    execution.max_concurrent=5 logging.verbose=false \
    logging.output_dir=$OUTROOT/lvl$lvl 2>&1 | grep -E "Accuracy|Average Score|Total Cost|ERROR|Error" || true
done
echo "VALIDATION_PASS_DONE"

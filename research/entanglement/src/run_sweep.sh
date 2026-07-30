#!/usr/bin/env bash
# Main sweep: methods x entanglement levels on a single benchmark.
set -euo pipefail
cd /home/t-matthewho/ac3/ctx_editor
source .venv/bin/activate

N=${N:-8}
LEVELS=${LEVELS:-"0 1 2 3"}
# method label -> experiment config name
METHODS=${METHODS:-"baseline omit_assistant summarize_v1 context_edit_v2"}
TASK=${TASK:-dev_math}
OUTROOT=${OUTROOT:-research/entanglement/artifacts/sweep_main}
mkdir -p "$OUTROOT"

for method in $METHODS; do
  for lvl in $LEVELS; do
    cell="$OUTROOT/${method}__lvl${lvl}"
    if [ -f "$cell/metrics.json" ]; then
      echo "=== SKIP (exists) $method @ e$lvl ==="; continue
    fi
    echo "=== $method @ entanglement=$lvl (N=$N, task=$TASK) ==="
    ctx-editor \
      experiment=$method model=gpt5_4_mini_trapi task=$TASK load_balancer=trapi \
      user_mode=entangled user_mode.entanglement_level=$lvl \
      task.limit=$N false_negative_analysis.enabled=false \
      execution.max_concurrent=6 logging.verbose=false \
      logging.output_dir="$cell" 2>&1 | grep -E "Accuracy|Average Score|Total Cost|ERROR|Error" || true
  done
done
echo "SWEEP_DONE"

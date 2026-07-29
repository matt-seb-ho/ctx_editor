#!/usr/bin/env bash
# T18 — same-model comparator arms on the SAME filtered pools as the ERGO replays.
#
# Rationale: the ERGO/database positive control did not reproduce (44.0 vs published
# 12.0) because gpt-5-mini (the published-era model) is unreachable under the current
# identity. Absolute levels therefore cannot be compared to tab:main. Ordering CAN be,
# if every arm is run through the identical pipeline. That is what this does.
#
# Arms: the six no-memory tab:main rows. Operator->config from RECON/worklog.md §A.1.
set -u
cd /home/t-matthewho/ac3/ctx_editor
. .venv/bin/activate

declare -A POOL=(
  [math]=data/baseline_traces_v2/math
  [code]=data/baseline_traces_v2/code
  [database]=data/baseline_traces_v2/database
  [actions]=data/baseline_traces/actions
)

ARMS="baseline omit_assistant concatenate_user append_analysis context_edit_v2_no_gate context_edit_v2_gated"

for arm in $ARMS; do
  for task in math code database actions; do
    out="outputs/T18/${arm}_${task}"
    [ -f "$out/metrics.json" ] && { echo "skip $arm/$task (done)"; continue; }
    echo "=== $(date -Is) START $arm / $task ==="
    ctx-editor \
      experiment="$arm" \
      model=gpt5_4_mini_trapi \
      load_balancer=trapi \
      task="dev_${task}" \
      user_mode=sharded \
      execution.replay_source="${POOL[$task]}" \
      execution.replay_turns=1 \
      execution.max_concurrent=5 \
      false_negative_analysis.model=gpt-5.4-mini_2026-03-17 \
      experiment_name="T18_${arm}_${task}" \
      logging.output_dir="$out" \
      > "/tmp/t18c_${arm}_${task}.log" 2>&1
    rc=$?
    echo "=== $(date -Is) DONE $arm / $task rc=$rc ==="
    grep -E '^Accuracy:' "/tmp/t18c_${arm}_${task}.log" | tail -1
  done
done
echo "=== $(date -Is) ALL COMPARATORS DONE ==="

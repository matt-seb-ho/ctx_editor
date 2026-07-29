#!/usr/bin/env bash
# T18 — ERGO last-turn replays on the pool-filtered baseline traces. ATTEMPT 2.
#
# Attempt 1 used task=<t>_v2, whose data_file is data/lic_eval_subset.json; that
# subset intersects the replay pools by only 5-10 samples, so the runs came back
# n=6/7/9/? instead of 25/19/20/25. Caught by the ERGO/database positive control.
# The pools ARE data/dev_<t>_subset.json (23/25/25/25, 100% id coverage), which is
# what T17's recommended command said. Fixed here.
set -u
cd /home/t-matthewho/ac3/ctx_editor
. .venv/bin/activate

run () {
  local task="$1" pool="$2" tag="${3:-}" ; local extra="${4:-}"
  local name="dev_${task}${tag}"
  echo "=== $(date -Is) START $name pool=$pool ==="
  ctx-editor \
    experiment=ergo \
    model=gpt5_4_mini_trapi \
    load_balancer=trapi \
    task="dev_${task}" \
    user_mode=sharded \
    execution.replay_source="$pool" \
    execution.replay_turns=1 \
    execution.max_concurrent=5 \
    false_negative_analysis.model=gpt-5.4-mini_2026-03-17 \
    experiment_name="T18_ergo_${task}${tag}" \
    logging.output_dir="outputs/T18/ergo_${task}${tag}" \
    $extra \
    > "/tmp/t18b_${task}${tag}.log" 2>&1
  echo "=== $(date -Is) DONE $name rc=$? ==="
  grep -E 'Accuracy:|user-sim|total_samples' "/tmp/t18b_${task}${tag}.log" | tail -6
}

run database data/baseline_traces_v2/database
run code     data/baseline_traces_v2/code
run math     data/baseline_traces_v2/math
run actions  data/baseline_traces/actions
# robustness: dev_actions has no task_version_map, so it uses the v1 actions
# evaluator/system prompt. Re-run with the v2 evaluator as a cross-check.
run actions  data/baseline_traces/actions "_v2eval" "+task.task_version_map.actions=actions_v2"
echo "=== $(date -Is) ALL DONE ==="

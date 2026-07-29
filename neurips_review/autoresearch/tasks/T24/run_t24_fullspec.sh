#!/usr/bin/env bash
# T24 — fully-specified single-turn ceiling for T1's venue.
# Same harness/evaluator/judge as T1; the only change is that each sample's shard
# list is replaced by ONE shard containing the original fully-specified question,
# so `user_mode=sharded` degenerates to a single-turn LiC "full" condition.
set -u
cd /home/t-matthewho/ac3/ctx_editor
. .venv/bin/activate
DATA=data/t24_fullspec_single_shard.json
OUT=outputs/T24
LOG=neurips_review/autoresearch/tasks/T24/run_log_fullspec.txt
mkdir -p "$OUT"
run_cell () {
  local task="$1" tag="$2"
  local dir="$OUT/${tag}"
  [[ -f "$dir/run_summary.json" ]] && { echo "[skip] $tag" | tee -a "$LOG"; return 0; }
  echo "=== [$(date -Is)] START $tag task=$task" | tee -a "$LOG"
  ctx-editor experiment=baseline model=gpt5_4_mini_trapi load_balancer=trapi \
    task="$task" task.data_file="$DATA" user_mode=sharded \
    execution.max_concurrent=5 \
    false_negative_analysis.model=gpt-5.4-mini_2026-03-17 \
    experiment_name="T24_${tag}" logging.output_dir="$dir" >> "$LOG" 2>&1
  echo "=== [$(date -Is)] END $tag rc=$?" | tee -a "$LOG"
  grep -E 'Accuracy:' "$dir/summary.txt" 2>/dev/null | tee -a "$LOG"
}
run_cell database_v2 db_fullspec
run_cell code_v2     code_fullspec
echo "=== [$(date -Is)] T24 FULLSPEC DONE" | tee -a "$LOG"

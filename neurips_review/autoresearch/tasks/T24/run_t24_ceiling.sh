#!/usr/bin/env bash
# T24 — pollution-ceiling arms for T1's venue (full LiC pool, gpt-5.4-mini/TRAPI).
# Adds the two design-oracle arms T1 lacked (Concat User, AO) so we can state the
# pollution damage in T1's venue: ceiling - baseline, against AC3's recovery.
set -u
cd /home/t-matthewho/ac3/ctx_editor
. .venv/bin/activate

DATA=data/sharded_instructions_600.json
OUT=outputs/T24
LOG=neurips_review/autoresearch/tasks/T24/run_log.txt
mkdir -p "$OUT"

run_cell () {
  local exp="$1" task="$2" tag="$3"; shift 3
  local dir="$OUT/${tag}"
  if [[ -f "$dir/run_summary.json" ]]; then
    echo "[skip] $tag already complete" | tee -a "$LOG"; return 0
  fi
  echo "=== [$(date -Is)] START $tag (experiment=$exp task=$task)" | tee -a "$LOG"
  ctx-editor \
    experiment="$exp" \
    model=gpt5_4_mini_trapi \
    load_balancer=trapi \
    task="$task" \
    task.data_file="$DATA" \
    user_mode=sharded \
    execution.max_concurrent=5 \
    false_negative_analysis.model=gpt-5.4-mini_2026-03-17 \
    experiment_name="T24_${tag}" \
    logging.output_dir="$dir" \
    "$@" >> "$LOG" 2>&1
  echo "=== [$(date -Is)] END $tag rc=$?" | tee -a "$LOG"
  grep -E 'Accuracy:|Adjusted Accuracy:' "$dir/summary.txt" 2>/dev/null | tee -a "$LOG"
}

run_cell concatenate_user database_v2 db_concat
run_cell omit_assistant   database_v2 db_ao
run_cell concatenate_user code_v2     code_concat
run_cell omit_assistant   code_v2     code_ao
echo "=== [$(date -Is)] T24 CEILING ARMS DONE" | tee -a "$LOG"

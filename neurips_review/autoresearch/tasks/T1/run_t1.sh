#!/usr/bin/env bash
# T1 — Condensation / summarisation baseline at matched call budget.
# LiC database + code, gpt-5.4-mini via TRAPI, N=30 per task (lic_eval_subset).
#
# Cells are ordered so the core result (Baseline / Summarise-1pass / AC3-Reset
# on both tasks) lands first; the budget-parity arm and Gated-Reset follow.
set -u
cd /home/t-matthewho/ac3/ctx_editor
. .venv/bin/activate

OUT=outputs/T1
LOG=neurips_review/autoresearch/tasks/T1/run_log.txt
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
    user_mode=sharded \
    execution.max_concurrent=5 \
    false_negative_analysis.model=gpt-5.4-mini_2026-03-17 \
    experiment_name="T1_${tag}" \
    logging.output_dir="$dir" \
    "$@" >> "$LOG" 2>&1
  local rc=$?
  echo "=== [$(date -Is)] END $tag rc=$rc" | tee -a "$LOG"
  grep -E 'Accuracy:|Adjusted Accuracy:' "$dir/summary.txt" 2>/dev/null | tee -a "$LOG"
}

# --- core result -----------------------------------------------------------
run_cell baseline                database_v2 db_baseline
run_cell summarize_v1            database_v2 db_summarize1
run_cell context_edit_v2_no_gate database_v2 db_reset       experiment.strategy.analysis_cache_dir=null
run_cell baseline                code_v2     code_baseline
run_cell summarize_v1            code_v2     code_summarize1
run_cell context_edit_v2_no_gate code_v2     code_reset     experiment.strategy.analysis_cache_dir=null

# --- budget-parity arm (2 condenser calls/turn == AC3-Reset's 2 analyzer calls)
run_cell summarize_v1_2pass      database_v2 db_summarize2
run_cell summarize_v1_2pass      code_v2     code_summarize2

# --- paper-default gated variant ------------------------------------------
run_cell context_edit_v2_gated   database_v2 db_gated       experiment.strategy.analysis_cache_dir=null
run_cell context_edit_v2_gated   code_v2     code_gated     experiment.strategy.analysis_cache_dir=null

echo "=== [$(date -Is)] ALL CELLS DONE" | tee -a "$LOG"

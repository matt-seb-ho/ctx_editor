#!/usr/bin/env bash
# T1 main sweep — full LiC pool (data/sharded_instructions_600.json).
#
# Why the full pool and not data/lic_eval_subset.json: the n=30 pilot put
# LiC-code baseline at 93.3% (28/30) — at ceiling, hence non-discriminating,
# exactly the failure mode that wasted session 1's T5. The full pool gives
# n=107 database / n=100 code with no baseline-failure selection bias, and its
# code half is 55% LiveCodeBench (vs 43% in the 30-sample subset).
#
# 7 arms x 2 tasks. Database first: it is the discriminating venue (pilot
# baseline 53.3%).
set -u
cd /home/t-matthewho/ac3/ctx_editor
. .venv/bin/activate

DATA=data/sharded_instructions_600.json
OUT=outputs/T1/main
LOG=neurips_review/autoresearch/tasks/T1/run_log_main.txt
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
    experiment_name="T1_${tag}" \
    logging.output_dir="$dir" \
    "$@" >> "$LOG" 2>&1
  local rc=$?
  echo "=== [$(date -Is)] END $tag rc=$rc" | tee -a "$LOG"
  grep -E 'Accuracy:|Adjusted Accuracy:' "$dir/summary.txt" 2>/dev/null | tee -a "$LOG"
}

NOCACHE=experiment.strategy.analysis_cache_dir=null

# --- database (n=107): the discriminating venue --------------------------
run_cell baseline                database_v2 db_baseline
run_cell summarize_v1            database_v2 db_summarize1
run_cell context_edit_v2_no_gate database_v2 db_reset      $NOCACHE
run_cell summarize_v1_2pass      database_v2 db_summarize2
run_cell mtosc_w2                database_v2 db_mtosc_w2
run_cell context_edit_v2_gated   database_v2 db_gated      $NOCACHE
run_cell mtosc_w4                database_v2 db_mtosc_w4

# --- code (n=100) ---------------------------------------------------------
run_cell baseline                code_v2     code_baseline
run_cell summarize_v1            code_v2     code_summarize1
run_cell context_edit_v2_no_gate code_v2     code_reset    $NOCACHE
run_cell summarize_v1_2pass      code_v2     code_summarize2
run_cell mtosc_w2                code_v2     code_mtosc_w2
run_cell context_edit_v2_gated   code_v2     code_gated    $NOCACHE
run_cell mtosc_w4                code_v2     code_mtosc_w4

echo "=== [$(date -Is)] ALL CELLS DONE" | tee -a "$LOG"

# --- robustness arm: neutral summariser prompt (no "compression not evaluation")
run_cell summarize_v2_neutral    database_v2 db_summarize_neutral
run_cell summarize_v2_neutral    code_v2     code_summarize_neutral

echo "=== [$(date -Is)] ALL CELLS + ROBUSTNESS DONE" | tee -a "$LOG"

#!/usr/bin/env bash
# T27 — MEDIUM red-team items that need runs.
#
# Cells:
#   db_summarize1_rep2  POSITIVE CONTROL + replicate. Known value 53.3% (57/107)
#                       from outputs/T1/main/db_summarize1. Same strategy class,
#                       same harness, same evaluator, same FN model as the
#                       neutral arm. Also supplies the run-to-run noise floor
#                       needed to interpret neutral-vs-v1 at all.
#   db_summarize_neutral  M11 — the condenser-prompt robustness control that
#                       "did not finish in the window" per replies/v5.
#   db_mtosc_w2         M12 (the tractable half) — MT-OSC at the smallest window
#                       in the paper's own sweep, post-c1dd523 fix. Answers
#                       "then scale the window to the conversation length".
#
# Output is T27-scoped (trap 7). Idempotent: skips completed cells.
set -u
cd /home/t-matthewho/ac3/ctx_editor
. .venv/bin/activate

DATA=data/sharded_instructions_600.json
OUT=outputs/T27
LOG=neurips_review/autoresearch/tasks/T27/run_log.txt
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
    experiment_name="T27_${tag}" \
    logging.output_dir="$dir" \
    "$@" >> "$LOG" 2>&1
  local rc=$?
  echo "=== [$(date -Is)] END $tag rc=$rc" | tee -a "$LOG"
  grep -E 'Accuracy:|Adjusted Accuracy:' "$dir/summary.txt" 2>/dev/null | tee -a "$LOG"
}

STREAM="${1:-A}"

if [[ "$STREAM" == "A" ]]; then
  run_cell summarize_v1         database_v2 db_summarize1_rep2
  run_cell summarize_v2_neutral database_v2 db_summarize_neutral
  run_cell summarize_v2_neutral code_v2     code_summarize_neutral
elif [[ "$STREAM" == "B" ]]; then
  run_cell mtosc_w2             database_v2 db_mtosc_w2
fi

echo "=== [$(date -Is)] STREAM $STREAM DONE" | tee -a "$LOG"

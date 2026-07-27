#!/usr/bin/env bash
# Exp3 (rebuttal): a MORE DISCRIMINATING unbiased-subset test. Random GSM8K (Exp1)
# left baseline near ceiling (90%). LiC-database has low multi-turn baseline
# (lots of headroom), so it separates methods better — and the standard 30-problem
# lic_eval database set is curated for eval, NOT selected on baseline failure, so it
# still answers iNYK Q1 (subset independent of baseline results) + concern G (end-to-end).
# Assistant = gpt-5.4-mini/TRAPI. Conditions: baseline, reset, gated.
set -uo pipefail
cd /home/t-matthewho/ac3/ctx_editor
. .venv/bin/activate

OUT=outputs/rebuttal_random
DATA=data/lic_eval_subset.json
MC=10
SUMMARY=neurips_review/experiments/exp3_results.txt
echo "Exp3 database end-to-end LiC (standard lic_eval database n=30), gpt-5.4-mini/TRAPI" > "$SUMMARY"
echo "started: $(date -u +%FT%TZ)" >> "$SUMMARY"; echo "" >> "$SUMMARY"

declare -A EXP
EXP[baseline]=baseline
EXP[reset]=context_edit_v2_no_gate
EXP[gated]=context_edit_v2_gated

for cond in baseline reset gated; do
  exp="${EXP[$cond]}"
  log="${OUT}/db_${cond}.log"
  t0=$(date +%s)
  echo "[$(date +%H:%M:%S)] BEGIN db ${cond} (exp=${exp})"
  ctx-editor \
    experiment="${exp}" \
    model=gpt5_4_mini_trapi \
    task=database_v2 \
    task.data_file="${DATA}" \
    user_mode=sharded \
    load_balancer=trapi \
    execution.max_concurrent="${MC}" \
    false_negative_analysis.model=gpt-4o_2024-11-20 \
    experiment_name="rebuttal_db_${cond}" \
    logging.output_dir="${OUT}/db_${cond}" \
    > "${log}" 2>&1
  rc=$?
  t1=$(date +%s); elapsed=$((t1-t0))
  {
    echo "=== db ${cond} (exp=${exp}) rc=${rc} wallclock=${elapsed}s ==="
    grep -E 'Accuracy:' "${log}" | tail -2
    grep -E 'Total Cost:' "${log}" | tail -1
    grep -E 'Average Turns:' "${log}" | tail -1
    echo ""
  } >> "$SUMMARY"
  echo "[$(date +%H:%M:%S)] DONE db ${cond} (${elapsed}s)"
done
echo "finished: $(date -u +%FT%TZ)" >> "$SUMMARY"
echo "ALL EXP3 DONE"; cat "$SUMMARY"

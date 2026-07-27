#!/usr/bin/env bash
# Exp1 (rebuttal): fresh END-TO-END LiC math on a RANDOM, non-baseline-selected
# N=40 subset (data/rebuttal_random_math40.json, seed 42 from math_full_subset).
# Assistant = gpt-5.4-mini via TRAPI (a fresh model not in the mega-table).
# Answers iNYK Q1 (random subset) + concern G (end-to-end, not replay) at once.
#
# Conditions: baseline, reset (context_edit_v2_no_gate), gated (context_edit_v2_gated).
# Records accuracy (from the run log) + wall-clock per condition.
set -uo pipefail
cd /home/t-matthewho/ac3/ctx_editor
. .venv/bin/activate

OUT=outputs/rebuttal_random
DATA=data/rebuttal_random_math40.json
MC=10
SUMMARY=neurips_review/experiments/exp1_results.txt
echo "Exp1 random-subset end-to-end LiC math, gpt-5.4-mini/TRAPI, N=40, seed=42" > "$SUMMARY"
echo "started: $(date -u +%FT%TZ)" >> "$SUMMARY"
echo "" >> "$SUMMARY"

declare -A EXP
EXP[baseline]=baseline
EXP[reset]=context_edit_v2_no_gate
EXP[gated]=context_edit_v2_gated

for cond in baseline reset gated; do
  exp="${EXP[$cond]}"
  log="${OUT}/full_${cond}.log"
  t0=$(date +%s)
  echo "[$(date +%H:%M:%S)] BEGIN ${cond} (exp=${exp})"
  ctx-editor \
    experiment="${exp}" \
    model=gpt5_4_mini_trapi \
    task=math_v2 \
    task.data_file="${DATA}" \
    user_mode=sharded \
    load_balancer=trapi \
    execution.max_concurrent="${MC}" \
    false_negative_analysis.model=gpt-4o_2024-11-20 \
    experiment_name="rebuttal_random_${cond}" \
    logging.output_dir="${OUT}/full_${cond}" \
    > "${log}" 2>&1
  rc=$?
  t1=$(date +%s); elapsed=$((t1-t0))
  acc=$(grep -E 'Accuracy:' "${log}" | tail -1)
  cost=$(grep -E 'Total Cost:' "${log}" | tail -1)
  turns=$(grep -E 'Average Turns:' "${log}" | tail -1)
  echo "=== ${cond} (exp=${exp}) rc=${rc} wallclock=${elapsed}s ===" >> "$SUMMARY"
  echo "  ${acc}" >> "$SUMMARY"
  echo "  ${cost}" >> "$SUMMARY"
  echo "  ${turns}" >> "$SUMMARY"
  echo "" >> "$SUMMARY"
  echo "[$(date +%H:%M:%S)] DONE ${cond} (${elapsed}s) ${acc}"
done

echo "finished: $(date -u +%FT%TZ)" >> "$SUMMARY"
echo "ALL EXP1 CONDITIONS DONE"
cat "$SUMMARY"

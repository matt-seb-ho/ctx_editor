#!/usr/bin/env bash
# Exp2 (rebuttal): EQUAL-BUDGET control for Vg97 Q3 ("is the gain decontamination
# or just more compute?"). ReflectionStrategy makes an extra analyzer-style LLM
# call per turn reading the FULL (polluted) context and appends advice, WITHOUT
# structural exclusion / reset. Same call budget as AC3-Reset, no decontamination.
# Same random N=40 subset + gpt-5.4-mini/TRAPI as Exp1, so numbers are comparable.
set -uo pipefail
cd /home/t-matthewho/ac3/ctx_editor
. .venv/bin/activate

OUT=outputs/rebuttal_random
DATA=data/rebuttal_random_math40.json
MC=10
SUMMARY=neurips_review/experiments/exp2_results.txt
echo "Exp2 equal-budget reflection control, gpt-5.4-mini/TRAPI, N=40, seed=42" > "$SUMMARY"
echo "started: $(date -u +%FT%TZ)" >> "$SUMMARY"

cond=reflection
log="${OUT}/full_${cond}.log"
t0=$(date +%s)
echo "[$(date +%H:%M:%S)] BEGIN ${cond}"
ctx-editor \
  experiment=legacy/reflection_only \
  experiment.strategy.min_turns_for_reflection=1 \
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
{
  echo "=== ${cond} rc=${rc} wallclock=${elapsed}s ==="
  grep -E 'Accuracy:' "${log}" | tail -1
  grep -E 'Total Cost:' "${log}" | tail -1
  grep -E 'Average Turns:' "${log}" | tail -1
  echo "finished: $(date -u +%FT%TZ)"
} >> "$SUMMARY"
echo "[$(date +%H:%M:%S)] DONE ${cond} (${elapsed}s)"
cat "$SUMMARY"

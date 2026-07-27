#!/usr/bin/env bash
# Exp1-reps: 2 additional reruns (rep2, rep3) of the random-subset end-to-end
# LiC-math experiment, so the NEW rebuttal result can be reported as mean±std
# (N=3) instead of single-seed — pre-empting the reviewers' "single seed / no
# variance" complaint about our own new experiment. Same fixed 40-item subset;
# temperature=1.0 supplies the run-to-run variance (matches paper rerun protocol).
set -uo pipefail
cd /home/t-matthewho/ac3/ctx_editor
. .venv/bin/activate

OUT=outputs/rebuttal_random
DATA=data/rebuttal_random_math40.json
MC=10
SUMMARY=neurips_review/experiments/exp1_reps_results.txt
echo "Exp1 reps (rep2,rep3) random N=40 end-to-end LiC-math, gpt-5.4-mini/TRAPI" > "$SUMMARY"
echo "started: $(date -u +%FT%TZ)" >> "$SUMMARY"; echo "" >> "$SUMMARY"

declare -A EXP
EXP[baseline]=baseline
EXP[reset]=context_edit_v2_no_gate
EXP[gated]=context_edit_v2_gated

for rep in 2 3; do
  seed=$((41+rep))   # 43, 44
  for cond in baseline reset gated; do
    exp="${EXP[$cond]}"
    log="${OUT}/rep${rep}_${cond}.log"
    t0=$(date +%s)
    echo "[$(date +%H:%M:%S)] BEGIN rep${rep} ${cond}"
    ctx-editor \
      experiment="${exp}" model=gpt5_4_mini_trapi task=math_v2 \
      task.data_file="${DATA}" user_mode=sharded load_balancer=trapi \
      execution.max_concurrent="${MC}" seed=${seed} \
      false_negative_analysis.model=gpt-4o_2024-11-20 \
      experiment_name="rebuttal_rep${rep}_${cond}" \
      logging.output_dir="${OUT}/rep${rep}_${cond}" > "${log}" 2>&1
    rc=$?; t1=$(date +%s)
    raw=$(tr '\r' '\n' < "${log}" | grep -E "Accuracy: [0-9]" | grep -v Adjusted | tail -1)
    adj=$(tr '\r' '\n' < "${log}" | grep -E "Adjusted Accuracy" | tail -1)
    {
      echo "=== rep${rep} ${cond} (seed=${seed}) rc=${rc} wallclock=$((t1-t0))s ==="
      echo "  ${raw}"; echo "  ${adj}"
    } >> "$SUMMARY"
    echo "[$(date +%H:%M:%S)] DONE rep${rep} ${cond} ${raw}"
  done
done
echo "finished: $(date -u +%FT%TZ)" >> "$SUMMARY"
echo "ALL EXP1 REPS DONE"; cat "$SUMMARY"

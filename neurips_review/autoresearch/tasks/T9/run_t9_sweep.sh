#!/usr/bin/env bash
# T9 — analyzer-model sensitivity sweep.
# Assistant held FIXED at DeepSeek-V4-Flash; only model.ctx_editor.model varies.
# Last-turn replay on the phase-1 conv0 prefix pools (code_v2 n=40, database_v2 n=49).
#
# Usage: bash run_t9_sweep.sh <task>   # task in {code, database}
set -u
cd /home/t-matthewho/ac3/ctx_editor
. .venv/bin/activate

TASK="${1:?usage: run_t9_sweep.sh <code|database>}"
REP="${2:-rep1}"
TCFG="${TASK}_v2"
PREFIX="data/valid_prefixes_htn50_52/deepseek_v4_flash_foundry/${TCFG}/conv0"
DATA="data/htn50_52_${TASK}_subset.json"

COMMON=(
  model=deepseek_v4_flash_foundry
  load_balancer=t9_foundry_trapi
  "task=${TCFG}"
  "task.data_file=${DATA}"
  "execution.replay_source=${PREFIX}"
  execution.replay_turns=1
  execution.max_concurrent=5
)

run_arm () {  # $1 = arm label, $2 = analyzer model ("" => baseline)
  local arm="$1" analyzer="$2"
  local out="outputs/T9/${REP}/${TASK}_${arm}"
  if [[ -f "${out}/run_summary.json" ]]; then
    echo "[T9] SKIP ${TASK}/${arm} (already done)"; return 0
  fi
  echo "[T9] === ${TASK} / ${arm} (analyzer=${analyzer:-none}) $(date -Is)"
  if [[ -z "$analyzer" ]]; then
    ctx-editor experiment=baseline "${COMMON[@]}" \
      "experiment_name=T9_${REP}_${TASK}_${arm}" "logging.output_dir=${out}" \
      > "/tmp/t9_${REP}_${TASK}_${arm}.log" 2>&1
  else
    ctx-editor experiment=context_edit_v2_no_gate "${COMMON[@]}" \
      "model.ctx_editor.model=${analyzer}" \
      experiment.strategy.analysis_cache_dir=null \
      "experiment_name=T9_${REP}_${TASK}_${arm}" "logging.output_dir=${out}" \
      > "/tmp/t9_${REP}_${TASK}_${arm}.log" 2>&1
  fi
  local rc=$?
  echo "[T9] --- ${TASK}/${arm} rc=${rc} $(date -Is)"
  grep -E '^(Accuracy|Adjusted Accuracy):' "${out}/summary.txt" 2>/dev/null || tail -5 "/tmp/t9_${REP}_${TASK}_${arm}.log"
}

run_arm baseline    ""
run_arm ds_v4_flash "DeepSeek-V4-Flash"
run_arm gpt54mini   "gpt-5.4-mini_2026-03-17"
run_arm kimi_k26    "Kimi-K2.6"
run_arm gpt4o_mini  "gpt-4o-mini"
run_arm llama70b    "Llama-3.3-70B-Instruct"

echo "[T9] SWEEP DONE ${TASK} ${REP} $(date -Is)"

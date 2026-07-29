#!/usr/bin/env bash
# T21 — CollabLLM assistant-omission (AO) column to N=3.
#
# Matches T8's per-cell invocation EXACTLY (see tasks/T8/run_t8.sh) with the arm
# swapped to `collabllm_assistant_omit`. AO runs NO analyzer, so
# `experiment.strategy.analysis_cache_dir` is omitted (AssistantOmitStrategy has
# no such key -> passing it is a Hydra struct error, same as for Baseline).
#
# `seed=` is a NO-OP on CollabLLM: these are REPLICATE RUNS AT temperature=1.0
# on a FIXED 20-problem draw, not seeds. rep1 is reused from the recovered
# snapshot; we run rep2/rep3.

set -u
cd /home/t-matthewho/ac3/ctx_editor
[[ -f .env ]] && { set -a; source .env; set +a; }

STREAM="$1"   # "math" or "code"
OUT=neurips_review/autoresearch/tasks/T21
mkdir -p "$OUT/logs"

run_cell_ao () {
  local taskname="$1" ds="$2" rep="$3"
  local tag="collabllm_assistant_omit_${ds}_rep${rep}"
  local dir="outputs/T21/${tag}"
  if [[ -f "$dir/run_summary.json" ]]; then
    echo "[skip] $tag already complete"; return 0
  fi
  echo "[start] $tag $(date -Is)"
  .venv/bin/python -m ctx_editor.run_collabllm \
    experiment=collabllm_assistant_omit \
    model=deepseek_v4_flash_user_deepseek \
    load_balancer=multi_endpoint_foundry \
    task.name="$taskname" \
    task.dataset_name="$ds" \
    task.limit=20 \
    execution.max_concurrent=5 \
    experiment_name="T21_${tag}" \
    logging.output_dir="$dir" \
    metadata.branch=T21_collabllm_ao_n3 \
    > "$OUT/logs/${tag}.log" 2>&1
  local rc=$?
  echo "[done rc=$rc] $tag $(date -Is)"
  return $rc
}

if [[ "$STREAM" == "math" ]]; then
  for rep in 2 3; do run_cell_ao collabllm_math math-hard "$rep"; done
else
  for rep in 2 3; do run_cell_ao collabllm_code bigcodebench "$rep"; done
fi
echo "STREAM $STREAM COMPLETE $(date -Is)"

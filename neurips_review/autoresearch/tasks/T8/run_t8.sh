#!/usr/bin/env bash
# T8 — CollabLLM N=3 replicates with the competent (DeepSeek-V4-Flash) user simulator.
#
# NOTE: `seed=` is a NO-OP on CollabLLM (loaders hardcode random.Random(42)).
# These are REPLICATE RUNS AT temperature=1.0 on a FIXED 20-problem draw,
# not seeds. rep1 is reused from the recovered snapshot; we run rep2/rep3.
#
# Each replicate gets its OWN analysis_cache_dir so no analyzer output is
# shared between replicates (guarantees independent reps).

set -u
cd /home/t-matthewho/ac3/ctx_editor
[[ -f .env ]] && { set -a; source .env; set +a; }

STREAM="$1"   # "math" or "code"
OUT=neurips_review/autoresearch/tasks/T8
mkdir -p "$OUT/logs"

run_cell () {
  local exp="$1" taskname="$2" ds="$3" rep="$4"
  local tag="${exp}_${ds}_rep${rep}"
  local dir="outputs/T8/${tag}"
  if [[ -f "$dir/run_summary.json" ]]; then
    echo "[skip] $tag already complete"; return 0
  fi
  echo "[start] $tag $(date -Is)"
  .venv/bin/python -m ctx_editor.run_collabllm \
    experiment="$exp" \
    model=deepseek_v4_flash_user_deepseek \
    load_balancer=multi_endpoint_foundry \
    task.name="$taskname" \
    task.dataset_name="$ds" \
    task.limit=20 \
    execution.max_concurrent=5 \
    experiment.strategy.analysis_cache_dir="outputs/T8/cache/${tag}" \
    experiment_name="T8_${tag}" \
    logging.output_dir="$dir" \
    metadata.branch=T8_collabllm_n3 \
    > "$OUT/logs/${tag}.log" 2>&1
  local rc=$?
  echo "[done rc=$rc] $tag $(date -Is)"
  return $rc
}

# BaselineStrategy config has no analysis_cache_dir key -> override would fail.
run_cell_baseline () {
  local taskname="$1" ds="$2" rep="$3"
  local tag="collabllm_baseline_${ds}_rep${rep}"
  local dir="outputs/T8/${tag}"
  if [[ -f "$dir/run_summary.json" ]]; then
    echo "[skip] $tag already complete"; return 0
  fi
  echo "[start] $tag $(date -Is)"
  .venv/bin/python -m ctx_editor.run_collabllm \
    experiment=collabllm_baseline \
    model=deepseek_v4_flash_user_deepseek \
    load_balancer=multi_endpoint_foundry \
    task.name="$taskname" \
    task.dataset_name="$ds" \
    task.limit=20 \
    execution.max_concurrent=5 \
    experiment_name="T8_${tag}" \
    logging.output_dir="$dir" \
    metadata.branch=T8_collabllm_n3 \
    > "$OUT/logs/${tag}.log" 2>&1
  local rc=$?
  echo "[done rc=$rc] $tag $(date -Is)"
  return $rc
}

if [[ "$STREAM" == "math" ]]; then
  for rep in 2 3; do
    run_cell collabllm_ac3_augment_v8 collabllm_math math-hard "$rep"
    run_cell_baseline collabllm_math math-hard "$rep"
  done
else
  for rep in 2 3; do
    run_cell collabllm_ac3_reset_v8 collabllm_code bigcodebench "$rep"
    run_cell_baseline collabllm_code bigcodebench "$rep"
  done
fi
echo "STREAM $STREAM COMPLETE $(date -Is)"

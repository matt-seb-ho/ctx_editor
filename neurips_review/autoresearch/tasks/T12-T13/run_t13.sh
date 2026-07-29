#!/bin/bash
# T13 — clean (inductive) train/eval split arm + offline-regime order sensitivity.
#   Train pool: data/lic_mem_learn_set.json  (disjoint-by-design designated learn set)
#   Eval:       dev_<task> replay on data/baseline_traces_v2/<task>  (same eval as T12)
# Usage: bash run_t13.sh <task: database|math>
set -uo pipefail
cd /home/t-matthewho/ac3/ctx_editor
. .venv/bin/activate

TASK="${1:?usage: run_t13.sh <database|math>}"
D=neurips_review/autoresearch/tasks/T12-T13
OUT=outputs/T12_T13/${TASK}
MEM=${D}/memories/${TASK}
mkdir -p "${OUT}" "${MEM}"

COMMON=(
  model=gpt5_4_mini_trapi
  load_balancer=trapi
  task=dev_${TASK}
  execution.max_concurrent=5
  false_negative_analysis.model=gpt-5.4-mini_2026-03-17
  metadata.branch=T12_T13
)

# ── 1. Training trajectories on the disjoint learn set (end-to-end, no replay) ──
if [[ ! -f ${OUT}/train_traj/results.json ]]; then
  echo "=== [$(date +%T)] train trajectories (${TASK}) on lic_mem_learn_set"
  ctx-editor experiment=append_analysis "${COMMON[@]}" \
    task.data_file=data/lic_mem_learn_set.json \
    experiment.strategy.analysis_cache_dir=null \
    execution.mode=parallel \
    experiment_name=T13_train_traj_${TASK} \
    logging.output_dir=${OUT}/train_traj 2>&1 | tail -20
fi

# ── 2. Shuffle the training trajectories, offline-learn one cheatsheet per order ──
python - "$TASK" <<'PY'
import json, random, sys, os
task = sys.argv[1]
src = f"outputs/T12_T13/{task}/train_traj/results.json"
d = json.load(open(src))
if isinstance(d, dict):
    d = d.get("results", d)
out = f"neurips_review/autoresearch/tasks/T12-T13/data/train_traj_{task}"
os.makedirs(out, exist_ok=True)
json.dump(d, open(f"{out}/ord0.json", "w"))
for s in (1001, 1002, 1003):
    dd = list(d); random.Random(s).shuffle(dd)
    json.dump(dd, open(f"{out}/ord{s}.json", "w"))
print("training trajectories:", len(d))
PY

for ORD in ord0 ord1001 ord1002 ord1003; do
  CS=${MEM}/offline_${ORD}_cheatsheet.json
  if [[ ! -f ${CS} ]]; then
    echo "=== [$(date +%T)] offline-learn ${ORD} (${TASK})"
    ctx-editor experiment=append_analysis "${COMMON[@]}" \
      memory.enabled=true memory.source=offline memory.target=analyzer \
      memory.offline_trajectories=${D}/data/train_traj_${TASK}/${ORD}.json \
      memory.offline_batch_size=5 \
      memory.include_full_spec_q=true memory.include_ground_truth_a=true \
      memory.save_path=${CS} \
      experiment_name=T13_offlinelearn_${ORD}_${TASK} \
      logging.output_dir=${OUT}/offlinelearn_${ORD} 2>&1 | tail -12
  fi
done

# ── 3. Frozen-cheatsheet eval on the same replay eval set (memory ON, inductive) ──
for ORD in ord0 ord1001 ord1002 ord1003; do
  CS=${MEM}/offline_${ORD}_cheatsheet.json
  [[ -f ${CS} ]] || { echo "MISSING ${CS}"; continue; }
  [[ -f ${OUT}/frozen_${ORD}/run_summary.json ]] && { echo "skip frozen_${ORD}"; continue; }
  echo "=== [$(date +%T)] frozen-mem eval ${ORD} (${TASK})"
  ctx-editor experiment=append_analysis_memory "${COMMON[@]}" \
    task.data_file=${D}/data/dev_${TASK}_ord0.json \
    execution.replay_source=data/baseline_traces_v2/${TASK} \
    execution.replay_turns=1 \
    execution.mode=parallel \
    memory.enabled=true memory.source=${CS} memory.target=analyzer \
    experiment_name=T13_frozen_${ORD}_${TASK} \
    logging.output_dir=${OUT}/frozen_${ORD} 2>&1 | tail -20
done

echo "=== [$(date +%T)] T13 ${TASK} done"

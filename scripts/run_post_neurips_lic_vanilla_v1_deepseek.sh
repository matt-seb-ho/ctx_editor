#!/usr/bin/env bash
# v1-task sharded baselines for DeepSeek-V4-Flash to quantify v2 task impact.
# Same sharded LiC setup as the main vanilla matrix, only difference is the
# task config: uses the v1 task files (math, code, database, actions) instead
# of the v2 variants. 4 tasks × 3 runs sequentially in one pipeline.
#
# Output dirs are uniquely named per-run to avoid the Hydra default
# date/time collision.

set -uo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
[[ -f .env ]] && { set -a; source .env; set +a; }

RUN_TAG="post_neurips_lic_vanilla_v1"
LOG_DIR="outputs/${RUN_TAG}/logs"
mkdir -p "$LOG_DIR"

MODEL=deepseek_v4_flash_foundry
LB=multi_endpoint_foundry
MC=30

TASKS=(math code database actions)
declare -A DATA_FILE
DATA_FILE[math]="data/htn50_52_math_subset.json"
DATA_FILE[code]="data/htn50_52_code_subset.json"
DATA_FILE[database]="data/htn50_52_database_subset.json"
DATA_FILE[actions]="data/htn50_52_actions_subset.json"

for task in "${TASKS[@]}"; do
    for i in 1 2 3; do
        label="${MODEL}__${task}__run${i}"
        logfile="${LOG_DIR}/${label}.log"
        start_ts="$(date +%s)"
        exp_name="baseline_sharded_${MODEL}_${task}_run${i}"
        out_override="outputs/${RUN_TAG}/${exp_name}_${start_ts}"

        echo "[$(date +%H:%M:%S)] BEGIN ${label}"
        ctx-editor \
            experiment=baseline \
            model="${MODEL}" \
            task="${task}" \
            task.data_file="${DATA_FILE[$task]}" \
            user_mode=sharded \
            load_balancer="${LB}" \
            execution.max_concurrent="${MC}" \
            experiment_name="${exp_name}" \
            logging.output_dir="${out_override}" \
            logging.verbose=false \
            metadata.branch="${RUN_TAG}" \
            > "${logfile}" 2>&1
        rc=$?
        elapsed=$(( $(date +%s) - start_ts ))
        acc="$(grep -E '^Accuracy:' "${logfile}" | head -1 | sed 's/^Accuracy: //' || true)"
        if [[ $rc -eq 0 ]]; then
            echo "[$(date +%H:%M:%S)] DONE  ${label}  (${elapsed}s)  ${acc}"
        else
            echo "[$(date +%H:%M:%S)] FAIL  ${label}  (rc=${rc})"
        fi
    done
done
echo "v1 sharded DeepSeek pipeline done."

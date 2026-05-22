#!/usr/bin/env bash
# R6 B3 cross-benchmark: WildChat (huang_eval phase2) × winner A2 (v8 prompt) × 3 models.
# Per sign-off 6: analyzer is LOCKED to gpt-5-mini across all respondents
# (hits the 76 cached gpt-5-mini analyses imported earlier this session).
# This isolates the rewriter-prompt variable from analyzer differences.
#
# 3 respondents × 1 variant (s3) = 3 cells, ~25-30 min each parallel.

set -uo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
[[ -f .env ]] && { set -a; source .env; set +a; }

RUN_TAG="post_may18_r6_b3_wildchat"
OUT_ROOT="outputs/${RUN_TAG}"
LOG_DIR="${OUT_ROOT}/logs"
mkdir -p "$LOG_DIR"

PHASE1_DIR="outputs/huang_eval/phase1/2026-03-24/02-22-57"
SEED=42

# Respondents to run
declare -a RESPONDENTS=("gpt-5-mini" "DeepSeek-V4-Flash" "Kimi-K2.6")

run_one() {
    local respondent="$1"
    local label="${respondent//[^a-zA-Z0-9]/_}__s3_v8"
    local logfile="${LOG_DIR}/${label}.log"
    local start_ts; start_ts="$(date +%s)"
    local out_run_name="s3_v8_${respondent//[^a-zA-Z0-9]/_}_seed${SEED}_${start_ts}"
    local out_override="${OUT_ROOT}/${out_run_name}"

    # gpt-5-mini → Azure OAI; foundry models route via multi_endpoint_foundry
    local lb_arg=""
    if [[ "$respondent" != "gpt-5-mini" ]]; then
        lb_arg="load_balancer=multi_endpoint_foundry"
    fi

    echo "[$(date +%H:%M:%S)] BEGIN ${label}"
    python -m ctx_editor.huang_eval.run_phase2 \
        ${lb_arg} \
        phase1_dir="${PHASE1_DIR}" \
        respondent_model="${respondent}" \
        judge_model="gpt-5-mini" \
        analyzer_model="gpt-5-mini" \
        variants.s3=true variants.s15=false variants.s2=false variants.augment=false \
        analyzer_prompt_versions.s3=v8 \
        s3_compaction_prompt_name=context_compaction_v8 \
        s3_open_ended_output=true \
        analysis_cache_dir=outputs/analysis_cache \
        seed="${SEED}" \
        max_concurrent=4 \
        experiment_name="${out_run_name}" \
        logging.output_dir="${out_override}" \
        > "${logfile}" 2>&1
    local rc=$?
    local elapsed=$(( $(date +%s) - start_ts ))
    if [[ $rc -eq 0 ]]; then
        echo "[$(date +%H:%M:%S)] DONE  ${label}  (${elapsed}s)"
    else
        echo "[$(date +%H:%M:%S)] FAIL  ${label}  (rc=${rc}, ${elapsed}s) — see ${logfile}"
    fi
}

PIDS=()
for r in "${RESPONDENTS[@]}"; do
    run_one "$r" &
    PIDS+=($!)
done

echo "Launched ${#PIDS[@]} WildChat B3 cells in parallel; pids=${PIDS[*]}"
for pid in "${PIDS[@]}"; do
    wait "$pid"
done
echo "R6 B3 WildChat done."

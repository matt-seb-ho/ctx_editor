#!/usr/bin/env bash
# WildChat (huang_eval phase2) × gpt-5.4 respondent. Fills the gpt-rep column
# of the WildChat sub-table that was previously gpt-5-mini. All four AC3
# variants (S3 = Rewrite v8, S15 = Reset, S2 = Gated-Reset, Augment).
# Per R6 sign-off 6: analyzer locked to gpt-5-mini across all respondents.

set -uo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
[[ -f .env ]] && { set -a; source .env; set +a; }

RUN_TAG="post_may26_wildchat_gpt54"
OUT_ROOT="outputs/${RUN_TAG}"
LOG_DIR="${OUT_ROOT}/logs"
mkdir -p "$LOG_DIR"

PHASE1_DIR="outputs/huang_eval/phase1/2026-03-24/02-22-57"
SEED=42
RESPONDENT="gpt-5.4"

run_variant() {
    local variant="$1"
    local label="${RESPONDENT//[^a-zA-Z0-9]/_}__${variant}"
    local logfile="${LOG_DIR}/${label}.log"
    local start_ts; start_ts="$(date +%s)"
    local out_run_name="${variant}_gpt5_4_seed${SEED}_${start_ts}"
    local out_override="${OUT_ROOT}/${out_run_name}"

    # Variant flags
    local vflags=""
    case "$variant" in
        s3)       vflags="variants.s3=true variants.s15=false variants.s2=false variants.augment=false";;
        s15)      vflags="variants.s3=false variants.s15=true variants.s2=false variants.augment=false";;
        s2)       vflags="variants.s3=false variants.s15=false variants.s2=true variants.augment=false";;
        augment)  vflags="variants.s3=false variants.s15=false variants.s2=false variants.augment=true";;
    esac

    # S3-specific: use the v8 (R6 winner) compaction prompt + open-ended mode
    local s3_args=""
    if [[ "$variant" == "s3" ]]; then
        s3_args="s3_compaction_prompt_name=context_compaction_v8 s3_open_ended_output=true"
    fi

    echo "[$(date +%H:%M:%S)] BEGIN ${label}"
    python -m ctx_editor.huang_eval.run_phase2 \
        phase1_dir="${PHASE1_DIR}" \
        respondent_model="${RESPONDENT}" \
        judge_model="gpt-5-mini" \
        analyzer_model="gpt-5-mini" \
        ${vflags} \
        analyzer_prompt_versions.s3=v8 \
        analyzer_prompt_versions.s15=v8 \
        analyzer_prompt_versions.augment=v8 \
        analyzer_prompt_versions.s2=v11 \
        ${s3_args} \
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

# Run variants in parallel — all use the same Azure OAI gpt-5.4 endpoint;
# load-balancer handles concurrency. Analyzer cache means the gpt-5-mini
# analyzer calls hit the 76 cached results for free.
PIDS=()
for v in s3 s15 s2 augment; do
    run_variant "$v" &
    PIDS+=($!)
done
echo "Launched ${#PIDS[@]} variants in parallel: ${PIDS[*]}"
for pid in "${PIDS[@]}"; do
    wait "$pid"
done
echo "WildChat × gpt-5.4 sweep done."

#!/usr/bin/env bash
# Mega-table fill: WildChat × Rewrite (s3) on gpt-5-mini, DeepSeek-V4-Flash,
# Kimi-K2.6; plus Augment on Kimi (the missing R2 cell).
# WildChat phase2 is already last-turn replay over 76 fixed prefixes, so each
# cell is ~25-30 min (foundry-side) and these can be parallelized across models.

set -uo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
[[ -f .env ]] && { set -a; source .env; set +a; }

RUN_TAG="post_may18_r3_wildchat_fills"
OUT_ROOT="outputs/${RUN_TAG}"
LOG_DIR="${OUT_ROOT}/logs"
mkdir -p "$LOG_DIR"

PHASE1_DIR="outputs/huang_eval/phase1/2026-03-24/02-22-57"
SEED=42

# (respondent, variant) tuples to run
declare -a RUNS=(
    "gpt-5-mini|s3"
    "DeepSeek-V4-Flash|s3"
    "Kimi-K2.6|s3"
    "Kimi-K2.6|augment"
)

run_one() {
    local respondent="$1" variant="$2"
    local label="${respondent//[^a-zA-Z0-9]/_}__${variant}__seed${SEED}"
    local logfile="${LOG_DIR}/${label}.log"
    local start_ts; start_ts="$(date +%s)"
    local out_run_name="${variant}_${respondent//[^a-zA-Z0-9]/_}_seed${SEED}_${start_ts}"
    local out_override="${OUT_ROOT}/${out_run_name}"

    local vflags="variants.s3=false variants.s15=false variants.s2=false variants.augment=false"
    case "$variant" in
        s3)      vflags="variants.s3=true variants.s15=false variants.s2=false variants.augment=false" ;;
        s15)     vflags="variants.s3=false variants.s15=true variants.s2=false variants.augment=false" ;;
        augment) vflags="variants.s3=false variants.s15=false variants.s2=false variants.augment=true" ;;
    esac

    # gpt-5-mini still routes through Azure OAI; pass load_balancer only for foundry models
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
        ${vflags} \
        analyzer_prompt_versions.s3=v8 \
        analyzer_prompt_versions.s15=v8 \
        analyzer_prompt_versions.augment=v8 \
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

# Run in parallel — different respondent models route to different endpoints/quotas.
PIDS=()
for tup in "${RUNS[@]}"; do
    IFS='|' read -r respondent variant <<<"$tup"
    run_one "$respondent" "$variant" &
    PIDS+=($!)
done

echo "Launched ${#PIDS[@]} WildChat cells in parallel; pids=${PIDS[*]}"
for pid in "${PIDS[@]}"; do
    wait "$pid"
done

echo "R3 WildChat fills all done."

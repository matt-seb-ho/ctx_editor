#!/usr/bin/env bash
# Post-NeurIPS R2 — Huang/WildChat re-run on stronger / non-OAI models.
#
# Now that run_phase2.py threads load_balancer_config through, we can probe
# AC3-Reset and AC3-Augment with foundry-routed models (DeepSeek-V4-Flash,
# Kimi-K2.6) in addition to gpt-5-mini. We reuse the existing Phase 1
# selection (gpt-5-mini AO failures) to keep the comparison tight.

set -uo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
[[ -f .env ]] && { set -a; source .env; set +a; }

RUN_TAG="post_neurips_r2_huang_models"
OUT_ROOT="outputs/${RUN_TAG}"
LOG_DIR="${OUT_ROOT}/logs"
mkdir -p "$LOG_DIR"

PHASE1_DIR="outputs/huang_eval/phase1/2026-03-24/02-22-57"
[[ -d "$PHASE1_DIR" ]] || { echo "ERROR: phase1 dir missing: $PHASE1_DIR" >&2; exit 2; }

# Single-seed (42) to control runtime; we can scale to 3 seeds for the
# winner afterwards if there's budget.
SEEDS=(42)

# Variants enabled:
#   - DeepSeek-V4-Flash: probe both s15 (Reset) and augment.
#   - Kimi-K2.6: just s15 — the gpt-5-mini gold standard was already augment;
#     priority is "does AC3-Reset generalize to a stronger non-OAI model".
declare -A MODEL_VARIANTS=(
    [DeepSeek-V4-Flash]="s15 augment"
    [Kimi-K2.6]="s15"
)

run_one() {
    local respondent="$1" seed="$2" variant="$3"
    local label="${respondent//[^a-zA-Z0-9]/_}__${variant}__seed${seed}"
    local logfile="${LOG_DIR}/${label}.log"
    local start_ts; start_ts="$(date +%s)"
    local out_run_name="${variant}_${respondent//[^a-zA-Z0-9]/_}_seed${seed}_${start_ts}"
    local out_override="${OUT_ROOT}/${out_run_name}"

    local vflags="variants.s3=false variants.s15=false variants.s2=false variants.augment=false"
    case "$variant" in
        s15)     vflags="variants.s3=false variants.s15=true variants.s2=false variants.augment=false" ;;
        augment) vflags="variants.s3=false variants.s15=false variants.s2=false variants.augment=true" ;;
    esac

    echo "[$(date +%H:%M:%S)] BEGIN ${label}"
    python -m ctx_editor.huang_eval.run_phase2 \
        load_balancer=multi_endpoint_foundry \
        phase1_dir="${PHASE1_DIR}" \
        respondent_model="${respondent}" \
        judge_model="gpt-5-mini" \
        analyzer_model="gpt-5-mini" \
        ${vflags} \
        analyzer_prompt_versions.s15=v8 \
        analyzer_prompt_versions.augment=v8 \
        seed="${seed}" \
        max_concurrent=4 \
        experiment_name="${out_run_name}" \
        logging.output_dir="${out_override}" \
        > "${logfile}" 2>&1
    local rc=$?
    local elapsed=$(( $(date +%s) - start_ts ))
    if [[ $rc -eq 0 ]]; then
        echo "[$(date +%H:%M:%S)] DONE  ${label}  (${elapsed}s)"
    else
        echo "[$(date +%H:%M:%S)] FAIL  ${label}  (rc=${rc}, ${elapsed}s)  see ${logfile}"
    fi
}

for respondent in "${!MODEL_VARIANTS[@]}"; do
    for variant in ${MODEL_VARIANTS[$respondent]}; do
        for seed in "${SEEDS[@]}"; do
            run_one "${respondent}" "${seed}" "${variant}"
        done
    done
done

echo "Post-NeurIPS R2 (Huang/WildChat) all done."

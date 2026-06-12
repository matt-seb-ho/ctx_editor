#!/usr/bin/env bash
# Phase 3b — Huang/WildChat redo with the Phase 1/2 AC3 winner (Reset = s15).
#
# Reuses the existing March-2026 Phase 1 output (30 WildChat conversations
# scored on gpt-5-mini's AO failures) for sample selection. We then run
# Phase 2 with DeepSeek-V4-Flash as the *respondent* model on those same
# failure turns, with 3 seeds for variance.
#
# Caveat (documented in the report): sample selection from gpt-5-mini's
# failure pattern. A fresh Phase 1 on DeepSeek would be more faithful, but
# the question "does AC3-Reset recover on the same conversations AO struggles
# with" is roughly seed-equivalent here.

set -uo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
[[ -f .env ]] && { set -a; source .env; set +a; }

RUN_TAG="post_neurips_ac3_phase3_huang"
OUT_ROOT="outputs/${RUN_TAG}"
LOG_DIR="${OUT_ROOT}/logs"
mkdir -p "$LOG_DIR"

PHASE1_DIR="outputs/huang_eval/phase1/2026-03-24/02-22-57"
if [[ ! -d "$PHASE1_DIR" ]]; then
    echo "ERROR: phase1 dir not found at $PHASE1_DIR" >&2
    exit 2
fi

RESPONDENT="gpt-5-mini"  # Huang's pipeline doesn't go through our Foundry
                          # load balancer; restrict to Azure-OAI-routable models
                          # for this batch. (Paper used gpt-5-mini too.)
JUDGE="gpt-5-mini"
ANALYZER="gpt-5-mini"

SEEDS=(42 43 44)

run_one() {
    local seed="$1" variant="$2"
    # variant in {s15, augment} — both flip on for one run
    local label="${variant}__seed${seed}"
    local logfile="${LOG_DIR}/${label}.log"
    local start_ts; start_ts="$(date +%s)"
    local out_run_name="${variant}_seed${seed}_${start_ts}"
    local out_override="${OUT_ROOT}/${out_run_name}"

    # Build variant flags
    local vflags="variants.s3=false variants.s15=false variants.s2=false variants.augment=false"
    case "$variant" in
        s15)     vflags="variants.s3=false variants.s15=true variants.s2=false variants.augment=false" ;;
        augment) vflags="variants.s3=false variants.s15=false variants.s2=false variants.augment=true" ;;
        s2)      vflags="variants.s3=false variants.s15=false variants.s2=true variants.augment=false" ;;
    esac

    echo "[$(date +%H:%M:%S)] BEGIN ${label}"
    python -m ctx_editor.huang_eval.run_phase2 \
        phase1_dir="${PHASE1_DIR}" \
        respondent_model="${RESPONDENT}" \
        judge_model="${JUDGE}" \
        analyzer_model="${ANALYZER}" \
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

for variant in s15 augment; do
    for seed in "${SEEDS[@]}"; do
        run_one "${seed}" "${variant}"
    done
done

echo "Phase 3b (Huang/WildChat) all done."

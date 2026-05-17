#!/usr/bin/env bash
# Phase 2 — scale up Phase 1's winning strategy + Augment (ablation) to the
# other 3 assistant models (gpt-5.4, Kimi-K2.6, gpt-5.5).
#
# Reads the winner from outputs/post_neurips_ac3_phase1/winners.json
# (produced by scripts/aggregate_ac3_phase.py --winners-out).
#
# Foundry pipelines (Kimi, gpt-5.5) are serialized across each other to
# respect the per-model RPM bucket; gpt-5.4 runs in parallel on the OpenAI
# endpoint pool.
#
# Drop gpt-5.5 from the matrix by passing --skip-gpt5_5 (per user note that
# gpt-5.5 is optional if too slow/expensive).

set -uo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
[[ -f .env ]] && { set -a; source .env; set +a; }

SKIP_GPT5_5=0
for arg in "$@"; do
    case "$arg" in
        --skip-gpt5_5|--skip-gpt5.5) SKIP_GPT5_5=1 ;;
    esac
done

RUN_TAG="post_neurips_ac3_phase2"
OUT_ROOT="outputs/${RUN_TAG}"
LOG_DIR="${OUT_ROOT}/logs"
mkdir -p "$LOG_DIR"

WINNERS_PATH="outputs/post_neurips_ac3_phase1/winners.json"
if [[ ! -f "$WINNERS_PATH" ]]; then
    echo "ERROR: winners.json not found at $WINNERS_PATH" >&2
    exit 2
fi
WINNER=$(python -c "import json; print(json.load(open('${WINNERS_PATH}')).get('winner') or '')")
if [[ -z "$WINNER" ]]; then
    echo "ERROR: winner is empty in $WINNERS_PATH" >&2
    exit 2
fi
echo "Phase 2 promoting AC3 winner: $WINNER"

# Map the strategy name to experiment-config name (default + actions variant)
case "$WINNER" in
    "Reset")
        WINNER_EXP_DEFAULT=context_edit_v2_no_gate
        WINNER_EXP_ACTIONS=context_edit_v2_no_gate_accumulate
        ;;
    "Gated-Reset")
        WINNER_EXP_DEFAULT=context_edit_v2_gated
        WINNER_EXP_ACTIONS=context_edit_v2_gated_accumulate
        ;;
    "Rewrite")
        WINNER_EXP_DEFAULT=ac3_rewrite_lic
        WINNER_EXP_ACTIONS=ac3_rewrite_lic
        ;;
    *)
        echo "ERROR: unknown winner '$WINNER'"
        exit 2
        ;;
esac

TASKS=(math_v2 code_v2 database_v2 actions_v2)
CONVS=(0 1 2)
declare -A DATA_FILE
DATA_FILE[math_v2]="data/htn50_52_math_subset.json"
DATA_FILE[code_v2]="data/htn50_52_code_subset.json"
DATA_FILE[database_v2]="data/htn50_52_database_subset.json"
DATA_FILE[actions_v2]="data/htn50_52_actions_subset.json"

# Strategies for Phase 2: S0, AO, Augment (ablation, always), + winner.
STRATEGY_KEYS=(baseline ao augment winner)
declare -A SK_TO_EXP_DEFAULT
SK_TO_EXP_DEFAULT[baseline]=baseline
SK_TO_EXP_DEFAULT[ao]=omit_assistant
SK_TO_EXP_DEFAULT[augment]=append_analysis
SK_TO_EXP_DEFAULT[winner]="$WINNER_EXP_DEFAULT"
declare -A SK_TO_EXP_ACTIONS
SK_TO_EXP_ACTIONS[baseline]=baseline
SK_TO_EXP_ACTIONS[ao]=omit_assistant
SK_TO_EXP_ACTIONS[augment]=append_analysis
SK_TO_EXP_ACTIONS[winner]="$WINNER_EXP_ACTIONS"

run_one() {
    local model_key="$1" lb="$2" mc="$3" strategy_key="$4" task="$5" conv="$6"

    local exp_name
    if [[ "$task" == "actions_v2" ]]; then
        exp_name="${SK_TO_EXP_ACTIONS[$strategy_key]}"
    else
        exp_name="${SK_TO_EXP_DEFAULT[$strategy_key]}"
    fi

    local label="${model_key}__${strategy_key}__${task}__conv${conv}"
    local logfile="${LOG_DIR}/${label}.log"
    local start_ts; start_ts="$(date +%s)"
    local out_run_name="${exp_name}_${task}_conv${conv}_${start_ts}"
    local out_override="${OUT_ROOT}/${model_key}/${out_run_name}"

    local replay_source="data/valid_prefixes_htn50_52/${model_key}/${task}/conv${conv}"
    if [[ ! -d "$replay_source" ]]; then
        echo "[$(date +%H:%M:%S)] SKIP ${label} — no replay source at ${replay_source}"
        return
    fi

    local extra=""
    if [[ "$strategy_key" == "augment" ]]; then
        extra="experiment.strategy.min_turns=1"
    fi

    echo "[$(date +%H:%M:%S)] BEGIN ${label} (exp=${exp_name})"
    ctx-editor \
        experiment="${exp_name}" \
        model="${model_key}" \
        task="${task}" \
        task.data_file="${DATA_FILE[$task]}" \
        user_mode=sharded \
        load_balancer="${lb}" \
        execution.max_concurrent="${mc}" \
        execution.replay_source="${replay_source}" \
        execution.replay_turns=1 \
        experiment_name="${out_run_name}" \
        logging.output_dir="${out_override}" \
        metadata.branch="${RUN_TAG}" \
        ${extra} \
        > "${logfile}" 2>&1
    local rc=$?
    local elapsed=$(( $(date +%s) - start_ts ))
    local acc; acc="$(grep -E '^Accuracy:' "${logfile}" | head -1 | sed 's/^Accuracy: //')"
    if [[ $rc -eq 0 ]]; then
        echo "[$(date +%H:%M:%S)] DONE  ${label}  (${elapsed}s)  ${acc}"
    else
        echo "[$(date +%H:%M:%S)] FAIL  ${label}  (rc=${rc}, ${elapsed}s)  see ${logfile}"
    fi
}

# Sequential within a model: keeps cache hot per (task, conv).
pipeline_for_model() {
    local model_key="$1" lb="$2" mc="$3"
    for task in "${TASKS[@]}"; do
        for conv in "${CONVS[@]}"; do
            for sk in "${STRATEGY_KEYS[@]}"; do
                run_one "${model_key}" "${lb}" "${mc}" "${sk}" "${task}" "${conv}"
            done
        done
    done
}

# Launch pipelines: gpt-5.4 in parallel (different endpoint), foundry models
# serialized after each other so they don't burst-overwhelm the shared
# Foundry endpoint.
pipeline_for_model gpt5_4 multi_endpoint 20 > "${LOG_DIR}/_pipeline_gpt5_4.log" 2>&1 &
pa=$!
(
    pipeline_for_model kimi_k2_6_foundry multi_endpoint_foundry 8 > "${LOG_DIR}/_pipeline_kimi.log" 2>&1
    if [[ "$SKIP_GPT5_5" -eq 0 ]]; then
        pipeline_for_model gpt5_5_foundry multi_endpoint_foundry 12 > "${LOG_DIR}/_pipeline_gpt5_5.log" 2>&1
    else
        echo "(gpt5_5 pipeline skipped per --skip-gpt5_5)" > "${LOG_DIR}/_pipeline_gpt5_5.log"
    fi
) &
pb=$!

echo "Launched Phase 2 pipelines: gpt5_4(parallel)=${pa}  foundry-serialized=${pb}"
wait "${pa}" "${pb}"
echo "All Phase 2 cells launched."

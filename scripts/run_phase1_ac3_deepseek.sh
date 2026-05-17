#!/usr/bin/env bash
# Phase 1 of the post-NeurIPS AC3 study.
#
# Last-turn replay on DeepSeek-V4-Flash, all 6 strategies × 4 tasks × 3
# prefixes from data/valid_prefixes_htn50_52/. Cache is shared across all
# variants on the same prefix so Augment / Reset / Gated-Reset / (Rewrite
# uses its own analyzer prompt) only do the LLM analyzer call once per
# (task, prefix, analyzer-knob) tuple.
#
# Per cell we save outputs under
#   outputs/post_neurips_ac3_phase1/{exp}_{task}_conv{c}_{ts}/
# (≥ 2 levels deep — avoids the ledger-write footgun).

set -uo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
[[ -f .env ]] && { set -a; source .env; set +a; }

RUN_TAG="post_neurips_ac3_phase1"
OUT_ROOT="outputs/${RUN_TAG}"
LOG_DIR="${OUT_ROOT}/logs"
mkdir -p "$LOG_DIR"

MODEL=deepseek_v4_flash_foundry
LB=multi_endpoint_foundry
MC=20  # max_concurrent per ctx-editor invocation; foundry endpoint cap is 250

TASKS=(math_v2 code_v2 database_v2 actions_v2)
CONVS=(0 1 2)

# strategy_name -> experiment_config, with task-specific override for actions
declare -A STRATEGY_EXP_DEFAULT
STRATEGY_EXP_DEFAULT[baseline]=baseline
STRATEGY_EXP_DEFAULT[ao]=omit_assistant
STRATEGY_EXP_DEFAULT[augment]=append_analysis
STRATEGY_EXP_DEFAULT[reset]=context_edit_v2_no_gate
STRATEGY_EXP_DEFAULT[gated]=context_edit_v2_gated
STRATEGY_EXP_DEFAULT[rewrite]=ac3_rewrite_lic

declare -A STRATEGY_EXP_ACTIONS
STRATEGY_EXP_ACTIONS[baseline]=baseline
STRATEGY_EXP_ACTIONS[ao]=omit_assistant
STRATEGY_EXP_ACTIONS[augment]=append_analysis
STRATEGY_EXP_ACTIONS[reset]=context_edit_v2_no_gate_accumulate
STRATEGY_EXP_ACTIONS[gated]=context_edit_v2_gated_accumulate
STRATEGY_EXP_ACTIONS[rewrite]=ac3_rewrite_lic

STRATEGY_ORDER=(baseline ao augment reset gated rewrite)

declare -A DATA_FILE
DATA_FILE[math_v2]="data/htn50_52_math_subset.json"
DATA_FILE[code_v2]="data/htn50_52_code_subset.json"
DATA_FILE[database_v2]="data/htn50_52_database_subset.json"
DATA_FILE[actions_v2]="data/htn50_52_actions_subset.json"

run_one() {
    local strategy_key="$1" task="$2" conv="$3"

    # Pick the right experiment config (actions has accumulate variants)
    local exp_name
    if [[ "$task" == "actions_v2" ]]; then
        exp_name="${STRATEGY_EXP_ACTIONS[$strategy_key]}"
    else
        exp_name="${STRATEGY_EXP_DEFAULT[$strategy_key]}"
    fi

    local label="${strategy_key}__${task}__conv${conv}"
    local logfile="${LOG_DIR}/${label}.log"
    local start_ts; start_ts="$(date +%s)"
    local out_run_name="${exp_name}_${task}_conv${conv}_${start_ts}"
    local out_override="${OUT_ROOT}/${out_run_name}"

    # AC3-Augment defaults to min_turns=3; in last-turn replay where prefixes
    # may be 5 turns we want to make sure Augment fires. Hard-set min_turns=1
    # for replay mode.
    local extra=""
    if [[ "$strategy_key" == "augment" ]]; then
        extra="experiment.strategy.min_turns=1"
    fi

    local replay_source="data/valid_prefixes_htn50_52/${MODEL}/${task}/conv${conv}"
    if [[ ! -d "$replay_source" ]]; then
        echo "[$(date +%H:%M:%S)] SKIP ${label} — no replay source at ${replay_source}"
        return
    fi

    echo "[$(date +%H:%M:%S)] BEGIN ${label} (exp=${exp_name})"
    ctx-editor \
        experiment="${exp_name}" \
        model="${MODEL}" \
        task="${task}" \
        task.data_file="${DATA_FILE[$task]}" \
        user_mode=sharded \
        load_balancer="${LB}" \
        execution.max_concurrent="${MC}" \
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

# For each (task, conv), run all 6 strategies sequentially so the analyzer
# cache populates on the first call and the remaining 5 hit cache. We DON'T
# parallelize across tasks because all roads lead to the same foundry
# endpoint and we want predictable cache behavior.
for task in "${TASKS[@]}"; do
    for conv in "${CONVS[@]}"; do
        for strategy_key in "${STRATEGY_ORDER[@]}"; do
            run_one "${strategy_key}" "${task}" "${conv}"
        done
    done
done

echo "All Phase 1 cells launched."

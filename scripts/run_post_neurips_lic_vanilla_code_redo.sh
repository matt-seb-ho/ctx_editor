#!/usr/bin/env bash
# Re-run only the code_v2 experiments tainted by the pre-enrichment data bug.
# After fixing data/htn50_52_code_subset.json (commits 7de964e + 10cd44d), we
# need clean replacements for:
#   - gpt5_4 code_v2 runs 1, 2 (run 3 was post-fix and clean)
#   - deepseek_v4_flash_foundry code_v2 runs 1, 2, 3 (all tainted)
#   - gpt5_5_foundry code_v2 runs 1, 2 (run 3 was post-fix and clean)
# Total: 7 runs. Runs are labelled "_redo" so they're distinguishable from the
# original (tainted) ones. The three model pipelines run in parallel.

set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ -f "$PROJECT_ROOT/.env" ]]; then
    set -a
    # shellcheck source=/dev/null
    source "$PROJECT_ROOT/.env"
    set +a
fi

RUN_TAG="post_neurips_lic_vanilla"
RESULTS_MD="$PROJECT_ROOT/docs/reports/${RUN_TAG}.md"
ROWS_DIR="$PROJECT_ROOT/outputs/${RUN_TAG}/rows"
LAUNCHER_LOG_DIR="$PROJECT_ROOT/outputs/${RUN_TAG}/logs"
mkdir -p "$LAUNCHER_LOG_DIR" "$ROWS_DIR"

run_one() {
    local model="$1"; local lb="$2"; local mc="$3"; local run_idx="$4"
    local label="${model}__code_v2__redo${run_idx}"
    local logfile="${LAUNCHER_LOG_DIR}/${label}.log"

    local start_ts start_human
    start_ts="$(date +%s)"
    start_human="$(date -Iseconds)"

    echo "[$(date +%H:%M:%S)] BEGIN ${label}"

    local exp_name="baseline_sharded_${model}_code_v2_redo${run_idx}"

    # Force a unique output_dir per run so parallel pipelines that start in the
    # same second don't all collide on outputs/{date}/{HH-MM-SS}/. We embed the
    # experiment_name + epoch seconds.
    local out_override="outputs/${RUN_TAG}_redo/${exp_name}_${start_ts}"

    ctx-editor \
        experiment=baseline \
        model="${model}" \
        task=code_v2 \
        task.data_file=data/htn50_52_code_subset.json \
        user_mode=sharded \
        load_balancer="${lb}" \
        execution.max_concurrent="${mc}" \
        experiment_name="${exp_name}" \
        logging.output_dir="${out_override}" \
        logging.verbose=false \
        metadata.branch="${RUN_TAG}_redo" \
        > "${logfile}" 2>&1
    local rc=$?

    local end_ts elapsed
    end_ts="$(date +%s)"; elapsed=$((end_ts - start_ts))

    local out_dir acc_line cost_line turns_line
    out_dir="$(grep -oE 'outputs/[0-9-]+/[0-9-]+' "${logfile}" | head -1 || true)"
    acc_line="$(grep -E '^Accuracy:' "${logfile}" | head -1 | sed 's/^Accuracy: //' || true)"
    cost_line="$(grep -E '^Total Cost:' "${logfile}" | head -1 | sed 's/^Total Cost: //' || true)"
    turns_line="$(grep -E '^Average Turns:' "${logfile}" | head -1 | sed 's/^Average Turns: //' || true)"

    if [[ $rc -eq 0 ]]; then
        echo "[$(date +%H:%M:%S)] DONE  ${label}  (${elapsed}s)  ${acc_line}"
    else
        echo "[$(date +%H:%M:%S)] FAIL  ${label}  (rc=${rc}, ${elapsed}s)"
    fi

    {
        printf '| %s | %s | code_v2 | redo%s | %s | %ss | %s | %s | %s | `%s` | `%s` |\n' \
            "${start_human}" "${model}" "${run_idx}" "${rc}" "${elapsed}" \
            "${acc_line}" "${cost_line}" "${turns_line}" "${out_dir:-?}" "${label}.log"
    } > "${ROWS_DIR}/${start_ts}_${label}.row"
}

# Sequentially within each model pipeline.
pipeline_gpt5_4()    { for i in 1 2; do run_one gpt5_4 multi_endpoint 30 "$i"; done; }
pipeline_deepseek()  { for i in 1 2 3; do run_one deepseek_v4_flash_foundry multi_endpoint_foundry 30 "$i"; done; }
pipeline_gpt5_5()    { for i in 1 2; do run_one gpt5_5_foundry multi_endpoint_foundry 30 "$i"; done; }

pipeline_gpt5_4   > "${LAUNCHER_LOG_DIR}/_redo_gpt5_4.log"   2>&1 &
pid_a=$!
pipeline_deepseek > "${LAUNCHER_LOG_DIR}/_redo_deepseek.log" 2>&1 &
pid_b=$!
pipeline_gpt5_5   > "${LAUNCHER_LOG_DIR}/_redo_gpt5_5.log"   2>&1 &
pid_c=$!
echo "Launched redos: gpt5_4=${pid_a} deepseek=${pid_b} gpt5_5=${pid_c}"
wait "${pid_a}" "${pid_b}" "${pid_c}"
echo "All redos done."

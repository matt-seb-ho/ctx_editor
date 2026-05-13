#!/usr/bin/env bash
# Launch 2 replicates of WildChat Gated-Reset (S2) for error bars.
# Mirrors outputs/huang_eval/phase2_s2_full/2026-03-25/06-13-04 exactly:
# same analyzer prompt (v11, the default in replay.generate_s2), same models,
# same phase1 dir, same all_turns.json (n=178), same seed=42.
set -euo pipefail

cd "$(dirname "$0")/.."

DATE_TAG="$(date +%Y-%m-%d)"
LOG_DIR="outputs/huang_eval/phase2_s2_full/${DATE_TAG}/_launch_logs"
mkdir -p "$LOG_DIR"

PHASE1_DIR="outputs/huang_eval/phase1/2026-03-24/02-22-57"
TURNS_FILE="${PHASE1_DIR}/all_turns.json"

run_one() {
    local label="$1"   # r1, r2
    local out="outputs/huang_eval/phase2_s2_full/${DATE_TAG}/${label}"

    echo "[launch] wildchat gr ${label} -> $out"
    python -m ctx_editor.huang_eval.run_phase2 \
        --phase1-dir "$PHASE1_DIR" \
        --respondent-model gpt-5-mini \
        --judge-model gpt-5-mini \
        --analyzer-model gpt-5-mini \
        --max-concurrent 10 \
        --turns-file "$TURNS_FILE" \
        --run-s2 \
        --seed 42 \
        --output-dir "$out" \
        > "${LOG_DIR}/${label}.stdout.log" 2> "${LOG_DIR}/${label}.stderr.log" &
    echo "  pid=$!"
}

run_one r1
run_one r2

wait
echo "both wildchat gr replicates finished"

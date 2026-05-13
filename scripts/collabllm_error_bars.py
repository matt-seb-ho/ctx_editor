"""Aggregate CollabLLM accuracy across replicates with error bars.

Source-of-truth scoring per task (matching the paper):
  - math: raw `is_correct` from results.json (boxed-answer eval)
  - code: GPT-5 conversation judge from `reeval_gpt-5_conversation_judge/`
          (raw signature-based pass_rate is systematically 0; see paper §B.2)
  - doc:  GPT-5 conversation judge if present; else raw `is_correct`

Reports per-replicate accuracy, mean, range, pooled accuracy and Wilson 95% CI.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import mean, stdev

OUTPUTS = Path("/home/v-homatthew/ctx_editor/outputs")

CELLS = [
    ("Baseline",     "math", ["2026-03-17/04-16-54", "2026-03-23/r2_baseline_math"]),
    ("Baseline",     "code", ["2026-03-20/10-22-05", "2026-03-23/r2_baseline_code"]),
    ("Baseline",     "doc",  ["2026-03-23/baseline_doc"]),
    ("Rewrite",      "math", ["2026-03-18/20-49-55", "2026-03-23/r2_compaction_math"]),
    ("Rewrite",      "code", ["2026-03-20/10-22-06", "2026-03-23/r2_compaction_code"]),
    ("Rewrite",      "doc",  ["2026-03-23/compaction_doc"]),
    ("ERGO",         "math", ["2026-03-23/ergo_math",        "2026-03-23/r2_ergo_math"]),
    ("ERGO",         "code", ["2026-03-23/ergo_code",        "2026-03-23/r2_ergo_code"]),
    ("ERGO",         "doc",  ["2026-03-23/ergo_doc"]),
    ("AO",           "math", ["2026-03-23/ao_math",          "2026-03-23/r2_ao_math"]),
    ("AO",           "code", ["2026-03-23/ao_code",          "2026-03-23/r2_ao_code"]),
    ("AO",           "doc",  ["2026-03-23/assistant_omit_doc"]),
    # Augment / Gated-Reset use 2026-05-07 v12 runs only.
    # Older s1_* (2026-03-24) and 2026-05-06 runs are CF-poisoned (see docs).
    ("Augment",      "math", ["2026-05-07/aug_math_r2"]),
    ("Augment",      "code", ["2026-05-07/aug_code_r2"]),
    ("Augment",      "doc",  ["2026-03-24/s1_doc"]),
    ("Gated-Reset",  "math", ["2026-05-07/gr_math_r1",       "2026-05-07/gr_math_r2"]),
    ("Gated-Reset",  "code", ["2026-05-07/gr_code_r1",       "2026-05-07/gr_code_r2"]),
]


def load_run_scores(run_dir: Path, task: str) -> list[float] | None:
    """Return per-sample binary scores for a run dir, using the right eval source."""
    rejudge = run_dir / "reeval_gpt-5_conversation_judge" / "results.json"
    raw = run_dir / "results.json"

    if task == "code":
        if not rejudge.exists():
            return None
        with open(rejudge) as f:
            data = json.load(f)
        return [float(r["accuracy"]) for r in data]

    # math, doc: prefer rejudge if present
    if task == "doc" and rejudge.exists():
        with open(rejudge) as f:
            data = json.load(f)
        return [float(r["accuracy"]) for r in data]

    if not raw.exists():
        return None
    with open(raw) as f:
        data = json.load(f)
    return [1.0 if r.get("is_correct") else 0.0 for r in data if "is_correct" in r]


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (centre - half, centre + half)


def main():
    print(f"{'Variant':<13} {'Task':<5} {'#runs':>5} {'#samp':>6} {'mean±sd':>11} {'min':>6} {'max':>6} {'pooled':>7} {'95% CI':>17}  source")
    print("-" * 105)

    detail = []
    for variant, task, run_dirs in CELLS:
        per_run_acc = []
        all_scores: list[float] = []
        sources = set()
        for rd in run_dirs:
            full = OUTPUTS / rd
            scores = load_run_scores(full, task)
            if not scores:
                continue
            per_run_acc.append(sum(scores) / len(scores))
            all_scores.extend(scores)
            sources.add(
                "judge" if (full / "reeval_gpt-5_conversation_judge" / "results.json").exists()
                and (task == "code" or task == "doc")
                else "raw"
            )

        if not per_run_acc:
            print(f"{variant:<13} {task:<5} {'-':>5}")
            continue

        n_runs = len(per_run_acc)
        n_samp = len(all_scores)
        mu = mean(per_run_acc)
        sd = stdev(per_run_acc) if n_runs >= 2 else float("nan")
        mn = min(per_run_acc)
        mx = max(per_run_acc)
        pooled_sum = sum(all_scores)
        pooled_acc = pooled_sum / n_samp
        # Wilson CI is for binary outcomes; round to nearest integer count for fractional judge scores
        lo, hi = wilson_ci(round(pooled_sum), n_samp)
        src = ",".join(sorted(sources))
        sd_str = f"±{sd*100:4.1f}" if not math.isnan(sd) else "  -- "
        print(f"{variant:<13} {task:<5} {n_runs:>5} {n_samp:>6} {mu*100:>5.1f}{sd_str} {mn*100:>5.1f}% {mx*100:>5.1f}% {pooled_acc*100:>6.1f}% {f'[{lo*100:.1f}, {hi*100:.1f}]':>17}  {src}")
        detail.append((variant, task, per_run_acc))

    print("\n--- per-replicate accuracy ---")
    for variant, task, accs in detail:
        accs_str = ", ".join(f"{a*100:.1f}%" for a in accs)
        print(f"  {variant:<13} {task:<5}  [{accs_str}]")


if __name__ == "__main__":
    main()

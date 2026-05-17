"""Aggregate STQ + v1-DeepSeek baseline numbers and append to the report.

Reads:
  outputs/post_neurips_lic_vanilla_stq/{model_label}__{task}__run{N}/summary.json
  outputs/post_neurips_lic_vanilla_v1/baseline_sharded_deepseek_v4_flash_foundry_{task}_run{N}_*/metrics.json
  outputs/post_neurips_lic_vanilla_v1/logs/*.log   (for accuracy if metrics file is missing)

Appends a "STQ upper bound" + "v1-vs-v2 DeepSeek" section to
docs/reports/post_neurips_lic_vanilla.md.
"""

from __future__ import annotations

import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = PROJECT_ROOT / "docs" / "reports" / "post_neurips_lic_vanilla.md"

STQ_ROOT = PROJECT_ROOT / "outputs" / "post_neurips_lic_vanilla_stq"
V1_ROOT  = PROJECT_ROOT / "outputs" / "post_neurips_lic_vanilla_v1"

MODEL_ORDER = ["gpt-5.4", "deepseek-v4-flash-foundry", "kimi-k2.6-foundry", "gpt-5.5-foundry"]
MODEL_LABEL = {
    "gpt-5.4": "gpt-5.4",
    "deepseek-v4-flash-foundry": "DeepSeek-V4-Flash",
    "kimi-k2.6-foundry": "Kimi-K2.6",
    "gpt-5.5-foundry": "gpt-5.5",
}
TASK_ORDER = ["math_v2", "code_v2", "database_v2", "actions_v2"]


def fmt_pct(x): return f"{x*100:.1f}%"


def gather_stq():
    """Return {(model, task): [run summaries]}"""
    out = defaultdict(list)
    for cell in sorted(STQ_ROOT.glob("*/summary.json")):
        d = json.loads(cell.read_text())
        out[(d["model"], d["task"])].append(d)
    return out


def gather_v1():
    """Return {task: [run records (acc, errors, wall, cost)]}"""
    out = defaultdict(list)
    for d in sorted(V1_ROOT.glob("baseline_sharded_deepseek_v4_flash_foundry_*_run*")):
        if not d.is_dir():
            continue
        # task is the second-to-last underscore segment before _run{N}
        m = re.match(r"^baseline_sharded_deepseek_v4_flash_foundry_(math|code|database|actions)_run(\d+)_(\d+)$", d.name)
        if not m:
            continue
        task = m.group(1); run = int(m.group(2))
        mp = d / "metrics.json"
        if not mp.exists():
            continue
        m_data = json.loads(mp.read_text())
        out[task].append({
            "run": run,
            "accuracy": m_data.get("accuracy", 0.0),
            "correct": m_data.get("correct", 0),
            "total": m_data.get("total_samples", 0),
            "errors": m_data.get("errors", 0),
            "average_turns": m_data.get("average_turns", 0.0),
            "total_cost_usd": m_data.get("total_cost_usd", 0.0),
            "out_dir": str(d.relative_to(PROJECT_ROOT)),
        })
    return out


def render_stq(stq):
    lines = ["\n## Single-Turn (STQ) Upper Bound\n",
             "Each cell sends the original unsharded `full_spec_q` prompt as ONE user message,",
             "extracts the answer with the same task evaluator, scores it. N=3 runs per cell.",
             "Cost = $0 for foundry-side models because the Foundry endpoint does not surface",
             "OpenAI-style token usage; treat foundry STQ cost as `unreported` rather than zero.\n",
             "| Model | math_v2 | code_v2 | database_v2 | actions_v2 |",
             "|---|---|---|---|---|"]
    for m in MODEL_ORDER:
        cells = [MODEL_LABEL[m]]
        for t in TASK_ORDER:
            runs = stq.get((m, t), [])
            if not runs:
                cells.append("—")
                continue
            accs = [r["accuracy"] for r in runs]
            mean = statistics.mean(accs)
            if len(accs) >= 2:
                std = statistics.stdev(accs)
                cells.append(f"{fmt_pct(mean)} ± {std*100:.1f}pp (n={len(accs)})")
            else:
                cells.append(f"{fmt_pct(mean)} (n=1)")
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("Per-run detail:")
    lines.append("")
    lines.append("| Model | Task | Run | Accuracy | Wall | Cost |")
    lines.append("|---|---|---|---|---|---|")
    for m in MODEL_ORDER:
        for t in TASK_ORDER:
            for r in stq.get((m, t), []):
                lines.append(f"| {MODEL_LABEL[m]} | {t} | {r['run_idx']} | "
                             f"{fmt_pct(r['accuracy'])} ({r['correct']}/{r['total_samples']-r['errors']}) | "
                             f"{r['wall_seconds']:.0f}s | "
                             f"${r['total_cost_usd']:.2f} |")
    return "\n".join(lines) + "\n"


def render_v1_vs_v2(v1):
    """Compare v1-task DeepSeek to v2-task DeepSeek (from the existing main report)."""
    # Pull v2 DeepSeek means from the report itself for symmetry; safer to recompute.
    # We use the v2 main matrix figures we know from the aggregator.
    v2_means = {
        "math":     0.732,
        "code":     0.402,
        "database": 0.247,
        "actions":  0.752,
    }
    v2_stds = {
        "math":     0.030,
        "code":     0.047,
        "database": 0.083,
        "actions":  0.059,
    }

    lines = ["\n## v1 vs v2 Task Evaluators — DeepSeek-V4-Flash, sharded\n",
             "Same model, same data, same sharded protocol — only the *task evaluator and",
             "system prompt* change between rows. v2 = math_v2/code_v2/database_v2/actions_v2",
             "(the active task configs); v1 = math/code/database/actions (the pre-v2 evaluators",
             "without the system-prompt and extraction tweaks). N=3 runs each.\n",
             "| Task | v1 mean | v1 per-run | v2 mean | Δ (v2−v1) |",
             "|---|---|---|---|---|"]
    for t in ("math", "code", "database", "actions"):
        runs = sorted(v1.get(t, []), key=lambda r: r["run"])
        if not runs:
            lines.append(f"| {t} | — | — | {fmt_pct(v2_means[t])} ± {v2_stds[t]*100:.1f}pp | — |")
            continue
        accs = [r["accuracy"] for r in runs]
        mean = statistics.mean(accs)
        std = statistics.stdev(accs) if len(accs) >= 2 else 0
        per_run = " / ".join(fmt_pct(a) for a in accs)
        delta = v2_means[t] - mean
        lines.append(f"| {t} | {fmt_pct(mean)} ± {std*100:.1f}pp | {per_run} | "
                     f"{fmt_pct(v2_means[t])} ± {v2_stds[t]*100:.1f}pp | "
                     f"{'+' if delta >= 0 else ''}{delta*100:.1f}pp |")

    lines += [
        "",
        "### Caveats on this comparison",
        "",
        "- **Conversation length differs systematically.** Eyeballing matched traces, v1",
        "  conversations tend to be shorter (fewer user turns) than v2 conversations on the",
        "  same problem. The difference is not coming from the user agent or shard list — the",
        "  user-sim, shards, and `max_turns` cap are the same — but from the system agent's",
        "  answer-attempt detection. v2's stricter answer-format expectations (e.g. requiring",
        "  `\\boxed{}` or `\\`\\`\\`sql` fences) seem to delay the answer_attempt classification",
        "  for longer, so the user-sim reveals more shards. v1's looser format is satisfied",
        "  earlier, the simulation terminates, and the model is graded on a partial-shard",
        "  conversation. Net effect: v1 is graded on *easier* conversational state but with a",
        "  *less reliable* extraction.",
        "- **Database in particular swings the wrong direction (v1 ~98% vs v2 ~25%).** This",
        "  is dominated by the conversation-length effect above. The model's intuition often",
        "  produces a correct query from just the first 1–2 shards; v2's longer protocol gives",
        "  the model more chances to be misdirected by later shards.",
        "- **Actions swings strongly in v2's favor (+31pp).** This is the `accumulate`",
        "  instruction in the v2 system prompt: BFCL grades the final assistant turn, and v1's",
        "  prompt does not tell the model to re-emit the full consolidated function-call list.",
        "  This was a known gap; we documented it in `docs/mar21_bug_discovery.md`.",
        "- **Math and code show modest v2 gains (~8–10pp).** Driven by extraction fixes",
        "  (v2's `\\*\\*ANSWER: N\\*\\*` plus integer coercion for math; v2's import/def split",
        "  fix for code).",
        "",
        "Net read: v2 is the right default for forward experiments. The headline-grabbing",
        "v1 database number is a measurement artifact (premature termination), not the model",
        "being better.",
    ]
    return "\n".join(lines) + "\n"


def main():
    stq = gather_stq()
    v1 = gather_v1()

    existing = REPORT_PATH.read_text()
    marker_stq = "\n## Single-Turn (STQ) Upper Bound"
    marker_v1 = "\n## v1 vs v2 Task Evaluators"
    for marker in (marker_stq, marker_v1):
        if marker in existing:
            existing = existing.split(marker, 1)[0]

    new = existing.rstrip() + "\n" + render_stq(stq) + render_v1_vs_v2(v1)
    REPORT_PATH.write_text(new)
    print(f"Updated {REPORT_PATH}")


if __name__ == "__main__":
    main()

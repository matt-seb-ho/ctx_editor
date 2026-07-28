"""Paired significance analysis from existing phase1/phase2 per-run tables.

No new API calls: parses the per-run accuracy rows already recorded in
docs/reports/post_neurips_ac3_phase{1,2}.md. Because every strategy is
evaluated on the SAME (model, task, prefix) triples, the correct statistic is
the PAIRED delta vs the full-context Baseline, not independent per-cell stds.

Outputs, per strategy:
  - mean +/- std of the paired delta (pp)
  - win/loss/tie counts over paired comparisons
  - exact two-sided sign-test p-value (binomial, ties dropped)

Answers Vg97 Q2 ("paired tests") and iNYK Q2 ("does the mean clear baseline").
"""

import re
import math
import statistics as st
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
REPORTS = [
    (ROOT / "docs/reports/post_neurips_ac3_phase1.md", "DeepSeek-V4-Flash"),
    (ROOT / "docs/reports/post_neurips_ac3_phase2.md", None),  # model from output dir
]

ROW = re.compile(
    r"^\|\s*(?P<strategy>[A-Za-z0-9 \-+]+?)\s*\|\s*(?P<task>math_v2|code_v2|database_v2|actions_v2)\s*"
    r"\|\s*(?P<conv>\d+)\s*\|\s*(?P<acc>[\d.]+)%[^|]*\|[^|]*\|[^|]*\|[^|]*\|\s*`?(?P<dir>[^`|]*)`?\s*\|?"
)

def model_from_dir(d: str, default: str | None) -> str:
    if "gpt5_4" in d:
        return "gpt-5.4"
    if "kimi" in d:
        return "Kimi-K2.6"
    if "gpt5_5" in d:
        return "gpt-5.5"
    if "deepseek" in d:
        return "DeepSeek-V4-Flash"
    return default or "unknown"

# (model, task, conv) -> {strategy: acc}
cells: dict[tuple, dict] = defaultdict(dict)
for path, default_model in REPORTS:
    if not path.exists():
        continue
    for line in path.read_text().splitlines():
        m = ROW.match(line)
        if not m:
            continue
        strat = m.group("strategy").strip()
        if strat in {"Strategy", ""}:
            continue
        model = model_from_dir(m.group("dir"), default_model)
        key = (model, m.group("task"), int(m.group("conv")))
        cells[key][strat] = float(m.group("acc"))

def sign_test_p(wins: int, losses: int) -> float:
    """Exact two-sided binomial sign test (p=0.5), ties already dropped."""
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)

BASE = "Baseline"
strategies = ["AO", "Augment", "Reset", "Gated-Reset", "Rewrite"]

print(f"Paired comparisons vs {BASE} (each pair = same model x task x prefix)")
print(f"total (model,task,prefix) triples parsed: {len(cells)}\n")
print(f"{'strategy':12} {'n':>4} {'mean delta':>12} {'std':>7} {'W/L/T':>10} {'sign p':>9}")
for s in strategies:
    deltas, w, l, t = [], 0, 0, 0
    for key, d in cells.items():
        if s in d and BASE in d:
            delta = d[s] - d[BASE]
            deltas.append(delta)
            if delta > 0:
                w += 1
            elif delta < 0:
                l += 1
            else:
                t += 1
    if not deltas:
        continue
    mean = st.mean(deltas)
    sd = st.stdev(deltas) if len(deltas) > 1 else 0.0
    p = sign_test_p(w, l)
    print(f"{s:12} {len(deltas):4d} {mean:+11.1f}pp {sd:6.1f} {w:3d}/{l:2d}/{t:2d} {p:9.4f}")

# Per-model breakdown for the headline operators
print("\nPer-model paired delta (Reset / Augment vs Baseline):")
by_model = defaultdict(lambda: defaultdict(list))
for (model, task, conv), d in cells.items():
    for s in ("Reset", "Augment", "Gated-Reset"):
        if s in d and BASE in d:
            by_model[model][s].append(d[s] - d[BASE])
for model in sorted(by_model):
    parts = []
    for s in ("Augment", "Reset", "Gated-Reset"):
        v = by_model[model].get(s)
        if v:
            parts.append(f"{s} {st.mean(v):+.1f}pp (n={len(v)})")
    print(f"  {model:20} " + "  ".join(parts))

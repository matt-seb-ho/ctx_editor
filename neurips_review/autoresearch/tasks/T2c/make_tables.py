#!/usr/bin/env python
"""T2c step 4 — build the rebuttal-ready markdown tables."""
import json
import sys
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).parent))
import paired_split as PS  # noqa: E402

HERE = Path(__file__).parent
LABELS = HERE / (sys.argv[1] if len(sys.argv) > 1 else "leak_labels_v2.jsonl")
ARTIFACT = "outputs/post_neurips_ac3_phase1/ (recovered from blob_staging/snapshot.tar.gz)"

recs = [json.loads(l) for l in open(LABELS)]
for r in recs:
    if r.get("injected") is False:
        r["label"] = "NO_LEAK"
    r["binary"] = "NO_LEAK" if r["label"] == "NO_LEAK" else "LEAK(any)"

ARMS = {
    "AC3-Reset": ("context_edit_v2_no_gate", ["math", "code", "database"]),
    "AC3-Reset (actions)": ("context_edit_v2_no_gate_accumulate", ["actions"]),
    "AC3-Gated-Reset": ("context_edit_v2_gated", ["math", "code", "database"]),
    "AC3-Gated-Reset (actions)": ("context_edit_v2_gated_accumulate", ["actions"]),
}

# ---------- Table 1: leakage base rate ----------
print("### Table 1 — Leakage base rate in AC3-Reset analyzer outputs "
      f"(LiC / DeepSeek-V4-Flash, phase-1 matrix; artifact `{ARTIFACT}`)\n")
print("| task | n analyzer outputs | LEAKS | PARTIAL | NO_LEAK |")
print("|---|---|---|---|---|")
tot = Counter()
for t in ["math", "code", "database", "actions"]:
    sub = [r for r in recs if r["task"] == t and r["strategy"].startswith("context_edit_v2_no_gate")]
    c = Counter(r["label"] for r in sub)
    n = len(sub)
    if not n:
        continue
    tot.update(c)
    print(f"| {t} | {n} | {c['LEAKS']} ({c['LEAKS']/n:.0%}) | {c['PARTIAL']} "
          f"({c['PARTIAL']/n:.0%}) | {c['NO_LEAK']} ({c['NO_LEAK']/n:.0%}) |")
n = sum(tot.values())
print(f"| **all** | **{n}** | **{tot['LEAKS']} ({tot['LEAKS']/n:.0%})** | "
      f"**{tot['PARTIAL']} ({tot['PARTIAL']/n:.0%})** | "
      f"**{tot['NO_LEAK']} ({tot['NO_LEAK']/n:.0%})** |")

# ---------- Table 2: paired accuracy by leak stratum ----------
print("\n\n### Table 2 — AC3-Reset vs full-context Baseline, paired per sample, "
      "split by whether the analyzer leaked the answer\n")
print("| subset | n | Baseline | AC3-Reset | Δ (pp) | 95% CI | W/L | McNemar p |")
print("|---|---|---|---|---|---|---|---|")

base = PS.load_arm("baseline")


def emit(title, arm, tasks, labelkey, order):
    ac3 = PS.load_arm(arm)
    labels = {}
    for r in recs:
        if r["strategy"] != arm or r["task"] not in tasks:
            continue
        labels[(r["task"], r["conv"], r["sample_id"])] = r[labelkey]
    groups = defaultdict(list)
    for k, v in labels.items():
        groups[v].append(k)
    out = []
    for g in ["__ALL__"] + order:
        keys = list(labels) if g == "__ALL__" else groups.get(g, [])
        keys = [k for k in keys if k in ac3 and k in base]
        if not keys:
            continue
        nn = len(keys)
        a = sum(ac3[k] for k in keys)
        b = sum(base[k] for k in keys)
        win = sum(1 for k in keys if ac3[k] and not base[k])
        loss = sum(1 for k in keys if base[k] and not ac3[k])
        disc = win + loss
        p = PS.binom_two_sided(min(win, loss), disc)
        lo, hi = PS.wilson(win, disc) if disc else (float("nan"), float("nan"))
        dlo, dhi = (2 * lo - 1) * disc / nn, (2 * hi - 1) * disc / nn
        nm = title if g == "__ALL__" else f"&nbsp;&nbsp;{g}"
        ps = "<0.0001" if p < 1e-4 else f"{p:.3f}"
        print(f"| {nm} | {nn} | {b/nn:.1%} | {a/nn:.1%} | **{100*(a-b)/nn:+.1f}** | "
              f"[{100*dlo:+.1f}, {100*dhi:+.1f}] | {win}/{loss} | {ps} |")
        out.append((g, nn, b / nn, a / nn, (a - b) / nn, p))
    return out


emit("**math+code+database (all)**", "context_edit_v2_no_gate",
     ["math", "code", "database"], "binary", ["NO_LEAK", "LEAK(any)"])
for t in ["math", "code", "database"]:
    emit(f"**{t}**", "context_edit_v2_no_gate", [t], "binary", ["NO_LEAK", "LEAK(any)"])
emit("**actions** (AC3-Reset-accumulate)", "context_edit_v2_no_gate_accumulate",
     ["actions"], "binary", ["NO_LEAK", "LEAK(any)"])

print("\n\n### Table 3 — same split, 3-way label, math+code+database\n")
print("| subset | n | Baseline | AC3-Reset | Δ (pp) | 95% CI | W/L | McNemar p |")
print("|---|---|---|---|---|---|---|---|")
emit("**all**", "context_edit_v2_no_gate", ["math", "code", "database"], "label",
     ["NO_LEAK", "PARTIAL", "LEAKS"])

print("\n\n### Table 4 — AC3-Gated-Reset (the paper's production setting)\n")
print("| subset | n | Baseline | AC3-Gated | Δ (pp) | 95% CI | W/L | McNemar p |")
print("|---|---|---|---|---|---|---|---|")
emit("**math+code+database (all)**", "context_edit_v2_gated",
     ["math", "code", "database"], "binary", ["NO_LEAK", "LEAK(any)"])
for t in ["math", "code", "database"]:
    emit(f"**{t}**", "context_edit_v2_gated", [t], "binary", ["NO_LEAK", "LEAK(any)"])
emit("**actions** (Gated-accumulate)", "context_edit_v2_gated_accumulate",
     ["actions"], "binary", ["NO_LEAK", "LEAK(any)"])

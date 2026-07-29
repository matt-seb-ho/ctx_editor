#!/usr/bin/env python
"""T2c step 5 — final labels + rebuttal tables.

`leak_final` combines two independent detectors of "the correct answer is
present in the text that was inserted into the assistant's context":
  1. the answer-verification pass (`answer_check.jsonl`) returning
     CORRECT_ANSWER_STATED, and
  2. for math only, the model-free numeric probe: the GSM8K gold number appears
     in the injected text and appears in neither the user shards nor the
     assistant's own prior messages.
A record is LEAK if either fires. This is deliberately a union (high recall for
leakage), so the NO_LEAK stratum is a conservative, high-precision set.
"""
import json
import sys
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).parent))
import paired_split as PS  # noqa: E402

HERE = Path(__file__).parent
labs = [json.loads(l) for l in open(HERE / "leak_labels_v3.jsonl")]
ac = {(r["run"], r["sample_id"], r["analysis_idx"]): r
      for r in map(json.loads, open(HERE / "answer_check.jsonl"))}
probe = {(r["strategy"], r["sample_id"], r["conv"]): r
         for r in json.load(open(HERE / "math_numeric_probe.json"))}

for r in labs:
    k = (r["run"], r["sample_id"], r["analysis_idx"])
    verdict = ac.get(k, {}).get("verdict", "NOT_CHECKED")
    pderived = probe.get((r["strategy"], r["sample_id"], r["conv"]), {}).get("derived", False)
    if r.get("injected") is False:
        r["label"] = "NO_LEAK"
        verdict, pderived = "NOT_CHECKED", False
    r["answer_verdict"] = verdict
    r["leak_final"] = "LEAK" if (verdict == "CORRECT_ANSWER_STATED" or pderived) else "NO_LEAK"
    r["leak_judge"] = "NO_LEAK" if r["label"] == "NO_LEAK" else "LEAK"

with open(HERE / "leak_labels_final.jsonl", "w") as f:
    for r in labs:
        f.write(json.dumps(r) + "\n")

ARMS = [("AC3-Reset", "context_edit_v2_no_gate", ["math", "code", "database"]),
        ("AC3-Reset", "context_edit_v2_no_gate_accumulate", ["actions"]),
        ("AC3-Gated-Reset", "context_edit_v2_gated", ["math", "code", "database"]),
        ("AC3-Gated-Reset", "context_edit_v2_gated_accumulate", ["actions"])]
base = PS.load_arm("baseline")


def table_rates():
    print("### Table 1 — How often does the analyzer hand the assistant the answer?\n")
    print("Rates over every analyzer invocation in the AC3-Reset arm "
          "(one per conversation; LiC replay matrix, DeepSeek-V4-Flash).\n")
    print("| task | n | judge says LEAKS/PARTIAL<br>(upper bound) | answer verified correct<br>(**strict leak rate**) | model-free numeric probe<br>(math only) |")
    print("|---|---|---|---|---|")
    tot = [0, 0, 0]
    for t in ["math", "code", "database", "actions"]:
        sub = [r for r in labs if r["task"] == t and r["strategy"].startswith("context_edit_v2_no_gate")]
        n = len(sub)
        if not n:
            continue
        judge = sum(1 for r in sub if r["label"] != "NO_LEAK")
        strict = sum(1 for r in sub if r["answer_verdict"] == "CORRECT_ANSWER_STATED")
        pr = sum(1 for r in sub if probe.get((r["strategy"], r["sample_id"], r["conv"]), {}).get("derived"))
        prs = f"{pr} ({pr/n:.0%})" if t == "math" else "n/a"
        print(f"| {t} | {n} | {judge} ({judge/n:.0%}) | **{strict} ({strict/n:.0%})** | {prs} |")
        tot[0] += n; tot[1] += judge; tot[2] += strict
    print(f"| **all** | **{tot[0]}** | **{tot[1]} ({tot[1]/tot[0]:.0%})** | "
          f"**{tot[2]} ({tot[2]/tot[0]:.0%})** | — |")


def emit(title, arm, tasks, key):
    ac3 = PS.load_arm(arm)
    lab = {(r["task"], r["conv"], r["sample_id"]): r[key]
           for r in labs if r["strategy"] == arm and r["task"] in tasks}
    groups = defaultdict(list)
    for k, v in lab.items():
        groups[v].append(k)
    for g in ["__ALL__", "NO_LEAK", "LEAK"]:
        keys = list(lab) if g == "__ALL__" else groups.get(g, [])
        keys = [k for k in keys if k in ac3 and k in base]
        if not keys:
            continue
        n = len(keys)
        a = sum(ac3[k] for k in keys); b = sum(base[k] for k in keys)
        win = sum(1 for k in keys if ac3[k] and not base[k])
        loss = sum(1 for k in keys if base[k] and not ac3[k])
        disc = win + loss
        p = PS.binom_two_sided(min(win, loss), disc)
        lo, hi = PS.wilson(win, disc) if disc else (float("nan"),) * 2
        dlo, dhi = (2 * lo - 1) * disc / n, (2 * hi - 1) * disc / n
        nm = title if g == "__ALL__" else f"&nbsp;&nbsp;{g}"
        ps = "<0.0001" if p < 1e-4 else f"{p:.3f}"
        print(f"| {nm} | {n} | {b/n:.1%} | {a/n:.1%} | **{100*(a-b)/n:+.1f}** | "
              f"[{100*dlo:+.1f}, {100*dhi:+.1f}] | {win}/{loss} | {ps} |")


def table_paired(key, label):
    print(f"\n\n### Table 2 — AC3 vs full-context Baseline, paired per sample, "
          f"split by leakage ({label})\n")
    print("| subset | n | Baseline | AC3 | Δ (pp) | 95% CI | W/L | McNemar p |")
    print("|---|---|---|---|---|---|---|---|")
    emit("**AC3-Reset, math+code+database**", "context_edit_v2_no_gate",
         ["math", "code", "database"], key)
    for t in ["math", "code", "database"]:
        emit(f"**AC3-Reset, {t}**", "context_edit_v2_no_gate", [t], key)
    emit("**AC3-Reset, actions**", "context_edit_v2_no_gate_accumulate", ["actions"], key)
    print("| | | | | | | | |")
    emit("**AC3-Gated-Reset, math+code+database**", "context_edit_v2_gated",
         ["math", "code", "database"], key)
    emit("**AC3-Gated-Reset, actions**", "context_edit_v2_gated_accumulate", ["actions"], key)


table_rates()
table_paired("leak_final", "strict: analyzer output verified to contain the correct answer")
table_paired("leak_judge", "conservative: LLM judge's 3-way label, LEAKS+PARTIAL vs NO_LEAK")

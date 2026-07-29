"""T21 — per-problem paired view: assistant-omission (AO) vs AC3-Reset vs Baseline
on bigcodebench, all three arms x three replicates, all re-scored offline in the
single unified dependency environment. Zero API calls."""
import json
from ctx_editor.data.collabllm_loader import load_collabllm_dataset
from ctx_editor.evaluation.collabllm_metrics import judge_pass_rate

s = load_collabllm_dataset("bigcodebench", limit=20)
meta = {x["task_id"]: x["single_turn_metadata"] for x in s}
SNAP = "/home/t-matthewho/ac3/recovered/ctx_editor/outputs/post_neurips_r2_collabllm_user_deepseek"
cells = {
 "AO1":  f"{SNAP}/collabllm_assistant_omit_bigcodebench_rep1_1779092497",
 "AO2":  "outputs/T21/collabllm_assistant_omit_bigcodebench_rep2",
 "AO3":  "outputs/T21/collabllm_assistant_omit_bigcodebench_rep3",
 "RST1": f"{SNAP}/collabllm_ac3_reset_v8_bigcodebench_rep1_1779092497",
 "RST2": "outputs/T8/collabllm_ac3_reset_v8_bigcodebench_rep2",
 "RST3": "outputs/T8/collabllm_ac3_reset_v8_bigcodebench_rep3",
 "BAS1": f"{SNAP}/collabllm_baseline_bigcodebench_rep1_1779092497",
 "BAS2": "outputs/T8/collabllm_baseline_bigcodebench_rep2",
 "BAS3": "outputs/T8/collabllm_baseline_bigcodebench_rep3",
}
D = {}
for k, d in cells.items():
    r = json.load(open(f"{d}/results.json"))
    rs = r if isinstance(r, list) else r.get("results", r)
    D[k] = {x["sample_id"]: judge_pass_rate(x.get("extracted_answer") or "", meta[x["sample_id"]]) for x in rs}

ids = sorted(D["AO1"])
print(f"{'problem':34s}  AO1 AO2 AO3 | RST1 RST2 RST3 | BAS1 BAS2 BAS3")
tot = {"AO": 0, "RST": 0, "BAS": 0}
for i in ids:
    row = {a: [D[f"{a}{n}"].get(i, 0.0) for n in (1, 2, 3)] for a in ("AO", "RST", "BAS")}
    for a in tot:
        tot[a] += sum(row[a])
    print(f"{i:34s} " + " | ".join(" ".join(f"{int(x):3d}" for x in row[a]) for a in ("AO", "RST", "BAS")))
print(f"\ntotal across 3 reps:  AO {int(tot['AO'])}/60   AC3-Reset {int(tot['RST'])}/60   Baseline {int(tot['BAS'])}/60")
for a in ("AO", "RST", "BAS"):
    per = [sum(D[f"{a}{n}"].values()) for n in (1, 2, 3)]
    mu = sum(per) / 3
    sd = (sum((p - mu) ** 2 for p in per) / 2) ** 0.5
    print(f"{a:4s} per-rep {[int(p) for p in per]}/20  -> {[round(100*p/20,1) for p in per]}  mean {100*mu/20:.2f}  sd {100*sd/20:.2f}")

import json, os
from ctx_editor.data.collabllm_loader import load_collabllm_dataset
from ctx_editor.evaluation.collabllm_metrics import judge_pass_rate
s=load_collabllm_dataset("bigcodebench",limit=20)
meta={x["task_id"]:x["single_turn_metadata"] for x in s}
SNAP="/home/t-matthewho/ac3/recovered/ctx_editor/outputs/post_neurips_r2_collabllm_user_deepseek"
cells={
 "RST1":f"{SNAP}/collabllm_ac3_reset_v8_bigcodebench_rep1_1779092497",
 "RST2":"outputs/T8/collabllm_ac3_reset_v8_bigcodebench_rep2",
 "RST3":"outputs/T8/collabllm_ac3_reset_v8_bigcodebench_rep3",
 "BAS1":f"{SNAP}/collabllm_baseline_bigcodebench_rep1_1779092497",
 "BAS2":"outputs/T8/collabllm_baseline_bigcodebench_rep2",
 "BAS3":"outputs/T8/collabllm_baseline_bigcodebench_rep3",
}
D={}
for k,d in cells.items():
    r=json.load(open(f"{d}/results.json")); rs=r if isinstance(r,list) else r.get("results",r)
    D[k]={x["sample_id"]: judge_pass_rate(x.get("extracted_answer") or "", meta[x["sample_id"]]) for x in rs}
ids=sorted(D["RST1"])
print(f"{'problem':34s} RST1 RST2 RST3 | BAS1 BAS2 BAS3")
rt=bt=0
for i in ids:
    r=[D[f"RST{n}"].get(i) for n in (1,2,3)]; b=[D[f"BAS{n}"].get(i) for n in (1,2,3)]
    rt+=sum(r); bt+=sum(b)
    print(f"{i:34s} "+" ".join(f"{int(x):4d}" for x in r)+" | "+" ".join(f"{int(x):4d}" for x in b))
print(f"\ntotal across 3 reps: Reset {int(rt)}/60   Baseline {int(bt)}/60")

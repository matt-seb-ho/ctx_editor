import sys
from ctx_editor.data.collabllm_loader import load_collabllm_dataset
from ctx_editor.evaluation.collabllm_metrics import judge_pass_rate
seed=int(sys.argv[1])
s=load_collabllm_dataset("bigcodebench",limit=20,seed=seed)
ok=[];bad=[]
for x in s:
    sc=judge_pass_rate(x["single_turn_completion"], x["single_turn_metadata"])
    (ok if sc==1.0 else bad).append(x["task_id"].split("/")[-1])
print(f"seed={seed}: canonical solutions passing {len(ok)}/20")
print("  FAILING (env gap or unstable test):", bad)

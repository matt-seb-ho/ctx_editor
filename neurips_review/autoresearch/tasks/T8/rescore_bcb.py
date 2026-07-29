import json, sys
from ctx_editor.data.collabllm_loader import load_collabllm_dataset
from ctx_editor.evaluation.collabllm_metrics import judge_pass_rate

run = sys.argv[1]
samples = load_collabllm_dataset("bigcodebench", limit=20)
meta = {s["task_id"]: s["single_turn_metadata"] for s in samples}

r = json.load(open(f"{run}/results.json"))
rs = r if isinstance(r, list) else r.get("results", r)
tot = 0
for x in rs:
    sid = x["sample_id"]
    m = meta.get(sid)
    if m is None:
        print("MISSING META", sid); continue
    new = judge_pass_rate(x.get("extracted_answer") or "", m)
    old = x.get("score")
    tot += new
    flag = "" if new == old else "   <-- MISMATCH"
    print(f"{sid:34s} stored={old}  rescored={new}{flag}")
print(f"\nRESCORED TOTAL: {tot}/20   (stored total {sum(y.get('score') or 0 for y in rs)}/20)")

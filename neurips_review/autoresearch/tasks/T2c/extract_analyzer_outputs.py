#!/usr/bin/env python
"""T2c step 1 — extract analyzer outputs + pairing keys from AC3 traces.

Emits one JSONL record per analyzer invocation, carrying everything the
leakage classifier needs plus the pairing key back to results.json.
"""
import json
import glob
import os
import re
import sys
from pathlib import Path

PHASE1 = Path("/home/t-matthewho/ac3/recovered_t2c/ctx_editor/outputs/post_neurips_ac3_phase1")
OUT = Path("/home/t-matthewho/ac3/ctx_editor/neurips_review/autoresearch/tasks/T2c")


def load_results(run_dir):
    p = run_dir / "results.json"
    if not p.exists():
        return {}
    return {r["sample_id"]: r for r in json.load(open(p))}


def conv_of(name):
    m = re.search(r"_conv(\d)_", name)
    return int(m.group(1)) if m else -1


def strategy_of(name):
    for s in ("context_edit_v2_no_gate_accumulate", "context_edit_v2_gated_accumulate",
              "context_edit_v2_no_gate", "context_edit_v2_gated", "ac3_rewrite_lic",
              "append_analysis", "omit_assistant", "baseline"):
        if name.startswith(s):
            return s
    return name.split("_")[0]


def task_of(name):
    m = re.search(r"_(math|code|database|actions)_v2_", name)
    return m.group(1) if m else "?"


def extract_run(run_dir):
    name = run_dir.name
    res = load_results(run_dir)
    recs = []
    for tf in sorted(glob.glob(str(run_dir / "traces/*/*/*.json"))):
        d = json.load(open(tf))
        sid = d["sample_id"]
        r = res.get(sid, {})
        meta = r.get("metadata", {})
        logs = d["trace"]["logs"]
        msgs = d["trace"]["messages"]
        user_msgs = [m["content"] for m in msgs if m["role"] == "user"]

        def context_before(k):
            """(user_msgs, assistant_msgs) visible up to the k-th user message."""
            us, asts, seen = [], [], 0
            for m in msgs:
                if m["role"] == "user":
                    if seen >= k:
                        break
                    seen += 1
                    us.append(m["content"])
                elif m["role"] == "assistant":
                    asts.append(m["content"])
            return us, asts

        n_shards = 0
        analysis_idx = 0
        pending = None  # (record, index) awaiting the injected-context flag
        for l in logs:
            t = l["type"]
            if t == "shard_revealed":
                n_shards += 1
            elif t == "conversation_analysis":
                dd = l["data"]
                us_seen, ast_seen = context_before(n_shards)
                pending = {
                    "run": name,
                    "strategy": strategy_of(name),
                    "task": task_of(name),
                    "conv": conv_of(name),
                    "sample_id": sid,
                    "analysis_idx": analysis_idx,
                    "shards_revealed": n_shards,
                    "user_messages": us_seen,
                    "assistant_messages": ast_seen,
                    "user_intent": dd.get("user_intent", ""),
                    "aligned": dd.get("aligned", ""),
                    "issues": dd.get("issues", ""),
                    "needs_edit": dd.get("needs_edit"),
                    "analyzer_model": dd.get("analyzer_model"),
                    "injected": False,
                    "edited_context": None,
                    "sample_correct": r.get("is_correct"),
                    "ground_truth_a": meta.get("ground_truth_a"),
                    "full_spec_q": meta.get("full_spec_q"),
                    "trace_path": tf,
                }
                analysis_idx += 1
                recs.append(pending)
            elif t == "context_edit_output" and pending is not None:
                pending["injected"] = True
                pending["edited_context"] = l["data"].get("edited_context")
                pending = None
    return recs


def main():
    pats = sys.argv[1:] or ["context_edit_v2_no_gate_*", "context_edit_v2_gated_*"]
    all_recs = []
    for pat in pats:
        for rd in sorted(PHASE1.glob(pat)):
            if not rd.is_dir():
                continue
            all_recs.extend(extract_run(rd))
    outp = OUT / "analyzer_outputs.jsonl"
    with open(outp, "w") as f:
        for r in all_recs:
            f.write(json.dumps(r) + "\n")
    print(f"wrote {len(all_recs)} records -> {outp}")
    from collections import Counter
    print(Counter((r["strategy"], r["task"]) for r in all_recs))


if __name__ == "__main__":
    main()

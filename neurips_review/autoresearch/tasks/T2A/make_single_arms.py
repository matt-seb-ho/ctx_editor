#!/usr/bin/env python
"""T2A — derive single-span arms from the manifest.

`data/t2a_harm_only/`  : only the HARMFUL span injected.
`data/t2a_use_only/`   : only the USEFUL span injected.

With the existing `t2a_clean` and `t2a_injected` this completes a 2x2 factorial
(harmful present/absent x useful present/absent), which is what makes the
preservation number causally interpretable: running the *Baseline* (no editing
at all) across the four arms measures how much each injected span is actually
worth, independently of any detector.
"""
from __future__ import annotations
import json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))


def main():
    man = [json.loads(l) for l in open(os.path.join(HERE, "manifest.jsonl"))]
    for out in ("data/t2a_harm_only", "data/t2a_use_only"):
        p = os.path.join(REPO, out)
        if os.path.isdir(p):
            shutil.rmtree(p)
    n = 0
    for r in man:
        td, conv, sid = r["task_dir"], r["conv"], r["sample_id"]
        fn = sid.replace("/", "_") + ".json"
        src = os.path.join(REPO, "data/t2a_clean", td, conv, fn)
        if not os.path.exists(src):
            continue
        base = json.load(open(src))
        for tag, span in (("harm_only", r["harmful"]), ("use_only", r["useful"])):
            tr = json.loads(json.dumps(base))
            msgs = tr["trace"]["messages"]
            i = span["msg_index"]
            assert msgs[i]["role"] == "assistant", (sid, i)
            msgs[i]["content"] = msgs[i]["content"].rstrip() + "\n\n" + span["text"]
            d = os.path.join(REPO, f"data/t2a_{tag}", td, conv)
            os.makedirs(d, exist_ok=True)
            json.dump(tr, open(os.path.join(d, fn), "w"), indent=1)
        n += 1
    print(f"wrote {n} conversations x 2 single-span arms")
    return 0


if __name__ == "__main__":
    sys.exit(main())

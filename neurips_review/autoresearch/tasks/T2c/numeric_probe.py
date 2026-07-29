#!/usr/bin/env python
"""T2c step 1b — deterministic numeric leakage probe for LiC-math.

No LLM. For each math analyzer output, ask:
  - does the GSM8K gold final answer appear as a standalone number in the
    analyzer's output text?
  - does that same number already appear in the USER messages the analyzer saw?

The second question is the crux the task brief flags: a number the user already
supplied is not evidence the analyzer solved anything. Numbers are matched with
thousands separators and trailing ".0" normalised, on word boundaries.
"""
import json
import re
from pathlib import Path
from collections import Counter

HERE = Path(__file__).parent
RECS = [json.loads(l) for l in open(HERE / "analyzer_outputs.jsonl")]


def gold_number(gt):
    if not isinstance(gt, str):
        return None
    m = re.search(r"####\s*([\-0-9,\.]+)", gt)
    if not m:
        return None
    s = m.group(1).replace(",", "").rstrip(".")
    return s


def variants(numstr):
    """Surface forms the same value could be written in."""
    out = {numstr}
    try:
        v = float(numstr)
    except ValueError:
        return out
    if v == int(v):
        i = int(v)
        out.add(str(i))
        out.add(f"{i:,}")
        out.add(f"{i}.0")
        out.add(f"{i}.00")
    return out


def contains_number(text, numstr):
    if not text:
        return False
    for v in variants(numstr):
        if re.search(r"(?<![\d.,])" + re.escape(v) + r"(?![\d])", text):
            return True
    return False


rows = []
for r in RECS:
    if r["task"] != "math":
        continue
    g = gold_number(r.get("ground_truth_a"))
    if g is None:
        continue
    analyzer_text = "\n".join([r["user_intent"], r["aligned"], r["issues"]])
    user_text = "\n".join(r["user_messages"])
    asst_text = "\n".join(r.get("assistant_messages") or [])
    in_analyzer = contains_number(analyzer_text, g)
    in_user = contains_number(user_text, g)
    in_asst = contains_number(asst_text, g)
    in_injected = contains_number(r.get("edited_context") or "", g)
    rows.append(
        dict(
            run=r["run"], strategy=r["strategy"], conv=r["conv"],
            sample_id=r["sample_id"], gold=g,
            in_analyzer=in_analyzer, in_user=in_user, in_asst=in_asst,
            in_injected=in_injected,
            # analyzer stated the gold value that neither the user nor the
            # assistant had produced -> the analyzer derived it itself
            derived=in_analyzer and not in_user and not in_asst,
            derived_injected=in_injected and not in_user and not in_asst,
            # analyzer echoed a value the assistant had already produced
            echoed_assistant=in_analyzer and in_asst and not in_user,
            correct=r["sample_correct"],
        )
    )

json.dump(rows, open(HERE / "math_numeric_probe.json", "w"), indent=1)

for strat in sorted({r["strategy"] for r in rows}):
    sub = [r for r in rows if r["strategy"] == strat]
    n = len(sub)
    f = lambda k: sum(r[k] for r in sub)
    print(f"\n=== {strat}  (n={n} math analyzer outputs) ===")
    print(f"  gold number appears in analyzer output       : {f('in_analyzer'):4d}  ({f('in_analyzer')/n:.1%})")
    print(f"    ...already in the USER messages            : {sum(r['in_analyzer'] and r['in_user'] for r in sub):4d}")
    print(f"    ...already in the ASSISTANT messages       : {f('echoed_assistant'):4d}")
    print(f"  DERIVED by the analyzer (in neither)         : {f('derived'):4d}  ({f('derived')/n:.1%})")
    print(f"  DERIVED and INJECTED into context            : {f('derived_injected'):4d}  ({f('derived_injected')/n:.1%})")

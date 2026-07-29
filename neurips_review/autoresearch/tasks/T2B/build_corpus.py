#!/usr/bin/env python
"""T2B — build the counterfactual span-ablation corpora.

Design (see worklog.md §1):

* A **span** is a naturally occurring block (fenced code block or blank-line
  separated paragraph) inside an assistant message of the *replay prefix*.
  Nothing is authored or injected: these are the model's own words from the
  paper's phase-1 conversations.
* The **present** corpus is the prefix with every assistant message
  *canonicalised* (rebuilt as "\\n\\n".join(blocks)). The ablated corpora are
  byte-identical to it except that exactly one block is deleted. Canonicalising
  both arms is what guarantees the only textual difference is the ablated span.
* Ablation condition `abl{j}` holds, for every conversation, the variant with
  its j-th selected span removed. One variant per directory, because
  `load_baseline_traces()` keys traces by `sample_id`.
* Three **control** corpora inject a span of known causal sign at a fixed
  position (appended as a new final block of the last prefix assistant
  message). Their "removed" arm is the plain present corpus, so each control
  costs one extra condition:
    - `ctl_filler` : contentless, same surface frame -> expected effect ~0
    - `ctl_harm`   : the T2A H_PHANTOM_* span for this conversation (causally
                     validated harmful in T2A §4) -> expected effect > 0
    - `ctl_answer` : the fully specified question (+ reference SQL for
                     database) -> expected effect << 0

Usage:
    python build_corpus.py --select selection.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
POOL = os.path.join(REPO, "data/valid_prefixes_htn50_52/deepseek_v4_flash_foundry")

K_SPANS = 4  # spans kept per conversation
MIN_SPAN_CHARS = 40

FILLER = (
    "Quick note so we don't lose track of this: I'll keep the formatting consistent "
    "and use clear, descriptive names throughout. I'll carry that forward."
)


# --------------------------------------------------------------------------- #
# block splitting
# --------------------------------------------------------------------------- #
def split_blocks(text: str) -> list[tuple[str, str]]:
    """Partition an assistant message into (kind, text) blocks.

    kind is 'code' for a fenced code block, 'prose' for a blank-line separated
    paragraph. The partition is exhaustive up to whitespace.
    """
    parts: list[tuple[str, str]] = []
    pos = 0
    for m in re.finditer(r"```.*?```", text, re.S):
        if m.start() > pos:
            parts.append(("prose", text[pos : m.start()]))
        parts.append(("code", m.group(0)))
        pos = m.end()
    if pos < len(text):
        parts.append(("prose", text[pos:]))
    out: list[tuple[str, str]] = []
    for kind, seg in parts:
        if kind == "code":
            if seg.strip():
                out.append(("code", seg.strip()))
        else:
            for p in re.split(r"\n\s*\n", seg):
                if p.strip():
                    out.append(("prose", p.strip()))
    return out


def canonical(text: str) -> str:
    return "\n\n".join(b for _, b in split_blocks(text))


def prefix_assistant_indices(messages: list[dict]) -> list[int]:
    """Indices of assistant messages that survive `truncate_final_assistant`."""
    prefix = messages[:-1]  # replay drops the final assistant message
    return [i for i, m in enumerate(prefix) if m["role"] == "assistant"]


# --------------------------------------------------------------------------- #
# span enumeration + selection
# --------------------------------------------------------------------------- #
def enumerate_spans(messages: list[dict]) -> list[dict]:
    spans = []
    for i in prefix_assistant_indices(messages):
        blocks = split_blocks(messages[i]["content"])
        if len(blocks) < 2:
            # removing the only block would empty the message; not a valid
            # in-place ablation, so the message contributes no span.
            continue
        for b, (kind, txt) in enumerate(blocks):
            if len(txt) < MIN_SPAN_CHARS:
                continue
            spans.append(
                {
                    "msg_index": i,
                    "block_index": b,
                    "kind": kind,
                    "text": txt,
                    "n_chars": len(txt),
                    "n_blocks_in_msg": len(blocks),
                }
            )
    return spans


def spread(items: list, k: int) -> list:
    """Deterministic position-stratified pick of k items spread over `items`."""
    if len(items) <= k:
        return list(items)
    if k == 1:
        return [items[len(items) // 2]]
    idx = sorted({round(t * (len(items) - 1) / (k - 1)) for t in range(k)})
    return [items[i] for i in idx]


def select_spans(spans: list[dict], k: int = K_SPANS) -> list[dict]:
    """Stratify by block kind so the sample is not dominated by boilerplate prose.

    Up to 2 code blocks (spread over the conversation) + the rest prose (spread),
    then top up from whichever pool has leftovers. Selection uses position and
    block kind only -- never correctness, never content.
    """
    code = [s for s in spans if s["kind"] == "code"]
    prose = [s for s in spans if s["kind"] == "prose"]
    n_code = min(2, len(code), k)
    chosen = spread(code, n_code) + spread(prose, k - n_code)
    if len(chosen) < k:  # top up
        rest = [s for s in spans if s not in chosen]
        chosen += spread(rest, k - len(chosen))
    chosen = sorted(chosen, key=lambda s: (s["msg_index"], s["block_index"]))
    return chosen[:k]


# --------------------------------------------------------------------------- #
# corpus writers
# --------------------------------------------------------------------------- #
def canonicalise_trace(trace_file: dict) -> dict:
    tr = json.loads(json.dumps(trace_file))
    ms = tr["trace"]["messages"]
    for i in prefix_assistant_indices(ms):
        ms[i]["content"] = canonical(ms[i]["content"])
    return tr


def ablate(trace_file: dict, span: dict) -> dict:
    tr = json.loads(json.dumps(trace_file))
    ms = tr["trace"]["messages"]
    i = span["msg_index"]
    assert ms[i]["role"] == "assistant"
    blocks = split_blocks(ms[i]["content"])
    kept = [b for j, (_, b) in enumerate(blocks) if j != span["block_index"]]
    assert kept, "ablation would empty the message"
    ms[i]["content"] = "\n\n".join(kept)
    return tr


def inject(trace_file: dict, text: str) -> dict:
    """Append `text` as a new final block of the last prefix assistant message."""
    tr = json.loads(json.dumps(trace_file))
    ms = tr["trace"]["messages"]
    i = prefix_assistant_indices(ms)[-1]
    ms[i]["content"] = ms[i]["content"].rstrip() + "\n\n" + text
    return tr


def write(root: str, task: str, sample_id: str, trace: dict) -> None:
    d = os.path.join(REPO, root, task)
    os.makedirs(d, exist_ok=True)
    fn = sample_id.replace("/", "_") + ".json"
    json.dump(trace, open(os.path.join(d, fn), "w"), indent=1)


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--select", required=True, help="selection.json from pilot")
    ap.add_argument("--k", type=int, default=K_SPANS)
    args = ap.parse_args()

    sel = json.load(open(args.select))  # {task: [sample_id, ...]}

    # T2A manifest supplies the causally-validated harmful control spans.
    t2a = {}
    mpath = os.path.join(HERE, "..", "T2A", "manifest.jsonl")
    for line in open(os.path.abspath(mpath)):
        r = json.loads(line)
        if r["conv"] == "conv0":
            t2a[(r["task_dir"], r["sample_id"])] = r

    datasets = {
        "database_v2": json.load(open(os.path.join(REPO, "data/htn50_52_database_subset.json"))),
        "code_v2": json.load(open(os.path.join(REPO, "data/htn50_52_code_subset.json"))),
    }
    ds_index = {t: {s["task_id"]: s for s in rows} for t, rows in datasets.items()}

    for root in ["data/t2b_present", "data/t2b_ctl_filler", "data/t2b_ctl_harm",
                 "data/t2b_ctl_answer"] + [f"data/t2b_abl{j}" for j in range(1, args.k + 1)]:
        p = os.path.join(REPO, root)
        if os.path.isdir(p):
            shutil.rmtree(p)

    manifest = []
    stats = {"n_conv": 0, "n_spans": 0, "ctl_harm": 0, "ctl_answer": 0}
    for task, ids in sel.items():
        for sample_id in ids:
            src = os.path.join(POOL, task, "conv0", sample_id.replace("/", "_") + ".json")
            raw = json.load(open(src))
            base = canonicalise_trace(raw)
            write("data/t2b_present", task, sample_id, base)

            spans = select_spans(enumerate_spans(base["trace"]["messages"]), args.k)
            for j, sp in enumerate(spans, start=1):
                write(f"data/t2b_abl{j}", task, sample_id, ablate(base, sp))
                manifest.append(
                    {
                        "span_id": f"{task}|{sample_id}|{j}",
                        "task": task,
                        "sample_id": sample_id,
                        "cond": f"abl{j}",
                        **{k: sp[k] for k in
                           ("msg_index", "block_index", "kind", "text", "n_chars",
                            "n_blocks_in_msg")},
                        "n_spans_in_conv": len(spans),
                    }
                )
            stats["n_spans"] += len(spans)
            stats["n_conv"] += 1

            # --- controls -------------------------------------------------- #
            write("data/t2b_ctl_filler", task, sample_id, inject(base, FILLER))

            rec = t2a.get((task, sample_id))
            if rec and rec["harmful"]["kind"] in ("H_PHANTOM_COL", "H_PHANTOM_PARAM"):
                write("data/t2b_ctl_harm", task, sample_id, inject(base, rec["harmful"]["text"]))
                stats["ctl_harm"] += 1

            s = ds_index[task].get(sample_id)
            if s:
                spec = s.get("fully_specified_question") or s.get("full_spec_q")
                if spec:
                    txt = (
                        "Quick note so we don't lose track of this: the user's complete "
                        f"requirement is exactly this — {spec.strip()}"
                    )
                    if task == "database_v2" and s.get("reference_sql"):
                        txt += (
                            "\n\nThe query that satisfies it is:\n```sql\n"
                            + s["reference_sql"].strip()
                            + "\n```"
                        )
                    txt += "\n\nI'll carry that forward."
                    write("data/t2b_ctl_answer", task, sample_id, inject(base, txt))
                    stats["ctl_answer"] += 1

    with open(os.path.join(HERE, "spans.jsonl"), "w") as f:
        for r in manifest:
            f.write(json.dumps(r) + "\n")
    print(json.dumps(stats, indent=1))
    from collections import Counter

    print("spans per condition:", Counter(r["cond"] for r in manifest))
    print("spans by kind:", Counter(r["kind"] for r in manifest))
    return 0


if __name__ == "__main__":
    sys.exit(main())

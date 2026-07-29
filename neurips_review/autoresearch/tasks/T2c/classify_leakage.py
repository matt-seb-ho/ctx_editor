#!/usr/bin/env python
"""T2c step 2 — LLM leakage classifier over analyzer outputs.

Judge: gpt-5.4-mini_2026-03-17 on TRAPI redmond/interactive.
Concurrency capped at 5 (shared TRAPI budget with other agents).

The label is deliberately about NET NEW answer information: did the analyzer
put the correct final answer in front of the assistant that the assistant did
not already have? A number the USER supplied, or a result the ASSISTANT itself
already produced, is not the analyzer solving the task -- that distinction is
the crux of the whole analysis, so the judge is shown the user messages and
assistant messages the analyzer read, and is asked for the provenance
separately from the label.
"""
import asyncio
import json
import os
import re
import sys
from pathlib import Path

from openai import AsyncOpenAI
from azure.identity import DefaultAzureCredential

HERE = Path(__file__).parent
MODEL = "gpt-5.4-mini_2026-03-17"
BASE = "https://trapi.research.microsoft.com/redmond/interactive/openai/v1/"
CONCURRENCY = 5

TASK_BLURB = {
    "math": "a grade-school word problem; the ground truth is a single final numeric value",
    "database": "a text-to-SQL task; the ground truth is a gold SQL query (any query returning the same result set counts as the answer)",
    "code": "a competitive-programming task graded by hidden unit tests; there is no single gold string, so treat 'the answer' as a complete, correct algorithm/implementation sufficient to pass",
    "actions": "a function-calling task; the ground truth is the exact list of API calls with their arguments",
}

PROMPT_FILE = os.environ.get("T2C_PROMPT", "prompt_v3.txt")
_raw = (HERE / PROMPT_FILE).read_text().split("\n")
PROMPT = "\n".join(_raw[_raw.index("You are auditing an automated \"conversation analyzer\" that reviews a multi-turn conversation"):])


def gold_text(r):
    g = r.get("ground_truth_a")
    if r["task"] == "math" and isinstance(g, str):
        m = re.search(r"####\s*(.+)$", g.strip())
        return (f"Full worked solution:\n{g}\n\nFINAL ANSWER: {m.group(1).strip()}"
                if m else g)
    if r["task"] == "code":
        return ("No gold solution string is stored for this task. The problem statement is:\n"
                + (r.get("full_spec_q") or "")[:4000])
    if g is None:
        return "(not recorded)"
    return g if isinstance(g, str) else json.dumps(g, indent=1)


def truncate(s, n):
    s = s or ""
    return s if len(s) <= n else s[: n // 2] + "\n...[truncated]...\n" + s[-n // 2:]


def build_prompt(r):
    analyzer = r.get("edited_context") or (
        f"<task_spec>\n{r['user_intent']}\n</task_spec>\n\n"
        f"<aligned>\n{r['aligned']}\n</aligned>\n\n<issues>\n{r['issues']}\n</issues>"
    )
    return PROMPT.format(
        task=r["task"],
        blurb=TASK_BLURB.get(r["task"], ""),
        gold=truncate(gold_text(r), 4000),
        user_msgs="\n---\n".join(truncate(m, 1500) for m in r["user_messages"]) or "(none)",
        asst_msgs="\n---\n".join(truncate(m, 2000) for m in (r.get("assistant_messages") or [])) or "(none)",
        analyzer=truncate(analyzer, 8000),
    )


def parse(txt):
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    if d.get("label") not in {"LEAKS", "PARTIAL", "NO_LEAK"}:
        return None
    return d


async def classify(client, sem, r, idx):
    async with sem:
        for attempt in range(4):
            try:
                resp = await client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": build_prompt(r)}],
                )
                d = parse(resp.choices[0].message.content or "")
                if d:
                    out = dict(r)
                    for k in ("user_messages", "assistant_messages", "edited_context",
                              "full_spec_q", "ground_truth_a", "aligned", "issues",
                              "user_intent"):
                        out.pop(k, None)
                    out.update(label=d["label"], provenance=d.get("provenance", "?"),
                               justification=d.get("justification", ""))
                    return out
            except Exception as e:  # noqa: BLE001
                await asyncio.sleep(3 * (attempt + 1))
                if attempt == 3:
                    print(f"[{idx}] FAILED: {type(e).__name__}: {str(e)[:120]}", file=sys.stderr)
        return None


async def main():
    recs = [json.loads(l) for l in open(HERE / "analyzer_outputs.jsonl")]
    only = sys.argv[1].split(",") if len(sys.argv) > 1 else None
    outfile = HERE / (sys.argv[2] if len(sys.argv) > 2 else "leak_labels.jsonl")
    if only:
        recs = [r for r in recs if r["strategy"] in only]
    done = set()
    if outfile.exists():
        for l in open(outfile):
            d = json.loads(l)
            done.add((d["run"], d["sample_id"], d["analysis_idx"]))
    todo = [r for r in recs if (r["run"], r["sample_id"], r["analysis_idx"]) not in done]
    print(f"{len(recs)} records, {len(done)} already labelled, {len(todo)} to do")

    token = DefaultAzureCredential().get_token("api://trapi/.default").token
    client = AsyncOpenAI(base_url=BASE, api_key=token)
    sem = asyncio.Semaphore(CONCURRENCY)
    tasks = [classify(client, sem, r, i) for i, r in enumerate(todo)]
    n_ok = 0
    with open(outfile, "a") as f:
        for i, coro in enumerate(asyncio.as_completed(tasks)):
            res = await coro
            if res:
                f.write(json.dumps(res) + "\n")
                f.flush()
                n_ok += 1
            if (i + 1) % 25 == 0:
                print(f"  {i+1}/{len(todo)} ({n_ok} ok)", flush=True)
    print(f"done: {n_ok}/{len(todo)} -> {outfile}")


if __name__ == "__main__":
    asyncio.run(main())

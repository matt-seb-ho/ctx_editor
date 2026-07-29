#!/usr/bin/env python
"""T2c step 2b — correctness adjudication pass over v3 LEAKS/PARTIAL records.

v3 spot-checks showed the judge sometimes calls a span "LEAKS" when the analyzer
states a FINAL VALUE THAT IS WRONG (e.g. says "the answer should remain 16"
when gold is 14). That is not leakage -- an incorrect value cannot be the
analyzer handing over the answer. This pass re-examines only the records v3
flagged as LEAKS or PARTIAL and asks one narrow, checkable question.
"""
import asyncio
import json
import re
import sys
from pathlib import Path

from openai import AsyncOpenAI
from azure.identity import DefaultAzureCredential

sys.path.insert(0, str(Path(__file__).parent))
import classify_leakage as C  # noqa: E402

HERE = Path(__file__).parent

PROMPT = """An automated "conversation analyzer" produced the critique below, which was inserted \
into an AI assistant's context. We are checking one narrow thing: does that critique actually \
hand the assistant the CORRECT answer?

TASK TYPE: {task} -- {blurb}

=== GROUND TRUTH ===
{gold}

=== THE ANALYZER'S OUTPUT ===
{analyzer}

Question: does the analyzer's output state, or evaluate to, a final answer that MATCHES the \
ground truth?

  - "CORRECT_ANSWER_STATED" : the output contains the correct final answer (as a stated value, \
a fully evaluated expression, a complete correct query, or a complete correct implementation). \
Superficial differences (formatting, units, equivalent SQL, equivalent code) still count as a \
match.
  - "WRONG_ANSWER_STATED"   : the output asserts a final answer, but it does NOT match the \
ground truth.
  - "NOT_STATED"            : the output does not assert any final answer -- it may give a \
recipe, an intermediate value, or pure critique, but the final value/artifact is absent.

Be strict. Do the arithmetic or read the query carefully before deciding.

Respond with ONLY a JSON object: {{"verdict": ..., "stated_answer": "<what the analyzer asserts, \
or null>", "justification": "<one sentence>"}}"""


def parse(txt):
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    if d.get("verdict") not in {"CORRECT_ANSWER_STATED", "WRONG_ANSWER_STATED", "NOT_STATED"}:
        return None
    return d


async def one(client, sem, r, key):
    analyzer = r.get("edited_context") or (
        f"<task_spec>\n{r['user_intent']}\n</task_spec>\n\n"
        f"<aligned>\n{r['aligned']}\n</aligned>\n\n<issues>\n{r['issues']}\n</issues>"
    )
    p = PROMPT.format(
        task=r["task"], blurb=C.TASK_BLURB.get(r["task"], ""),
        gold=C.truncate(C.gold_text(r), 4000),
        analyzer=C.truncate(analyzer, 8000),
    )
    async with sem:
        for attempt in range(4):
            try:
                resp = await client.chat.completions.create(
                    model=C.MODEL, messages=[{"role": "user", "content": p}])
                d = parse(resp.choices[0].message.content or "")
                if d:
                    return dict(run=r["run"], sample_id=r["sample_id"],
                                analysis_idx=r["analysis_idx"], task=r["task"],
                                conv=r["conv"], strategy=r["strategy"],
                                verdict=d["verdict"],
                                stated_answer=d.get("stated_answer"),
                                justification=d.get("justification", ""))
            except Exception as e:  # noqa: BLE001
                await asyncio.sleep(3 * (attempt + 1))
                if attempt == 3:
                    print(f"FAILED {key}: {type(e).__name__}", file=sys.stderr)
        return None


async def main():
    labels = {(r["run"], r["sample_id"], r["analysis_idx"]): r
              for r in map(json.loads, open(HERE / "leak_labels_v3.jsonl"))}
    recs = [json.loads(l) for l in open(HERE / "analyzer_outputs.jsonl")]
    outfile = HERE / "answer_check.jsonl"
    done = set()
    if outfile.exists():
        for l in open(outfile):
            d = json.loads(l)
            done.add((d["run"], d["sample_id"], d["analysis_idx"]))
    todo = []
    for r in recs:
        k = (r["run"], r["sample_id"], r["analysis_idx"])
        if k in done:
            continue
        L = labels.get(k)
        if L and L["label"] in {"LEAKS", "PARTIAL"}:
            todo.append((r, k))
    print(f"{len(todo)} to adjudicate")
    token = DefaultAzureCredential().get_token("api://trapi/.default").token
    client = AsyncOpenAI(base_url=C.BASE, api_key=token)
    sem = asyncio.Semaphore(C.CONCURRENCY)
    n = 0
    with open(outfile, "a") as f:
        for i, coro in enumerate(asyncio.as_completed([one(client, sem, r, k) for r, k in todo])):
            res = await coro
            if res:
                f.write(json.dumps(res) + "\n")
                f.flush()
                n += 1
            if (i + 1) % 50 == 0:
                print(f"  {i+1}/{len(todo)}", flush=True)
    print(f"done {n}/{len(todo)}")


if __name__ == "__main__":
    asyncio.run(main())

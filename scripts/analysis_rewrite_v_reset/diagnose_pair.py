"""DeepSeek-V4-Flash worker that diagnoses why Rewrite failed and Reset
succeeded for a given paired sample.

For each pair, asks the worker to:

  1. Compare the two prepared contexts. Identify the *structural*
     difference (spec phrasing, what-looks-right format, etc.).
  2. Diagnose the failure chain: which part of the Rewrite context
     caused the assistant to err? (spec vs. work-so-far vs. neither)
  3. Attribute the bad Rewrite context to *which input of the
     rewrite operation* most likely caused it (analysis output
     contained the error, OR the rewriter LLM hallucinated from the
     conversation, OR the rewrite prompt itself).

Output: scripts/analysis_rewrite_v_reset/data/diagnoses.jsonl
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, "/home/v-homatthew/ctx_editor/src")

from omegaconf import OmegaConf  # noqa: E402

from ctx_editor.models.endpoint_config import LoadBalancerConfig  # noqa: E402
from ctx_editor.models.openai_model import OpenAIModelClient  # noqa: E402


DATA_DIR = Path(__file__).resolve().parent / "data"
LB_CFG_PATH = Path(
    "/home/v-homatthew/ctx_editor/src/ctx_editor/config/load_balancer/multi_endpoint_foundry.yaml"
)


SYSTEM_PROMPT = """\
You are a careful research-assistant LLM diagnosing why a context-editing
strategy called "Rewrite" produced a worse final answer than a baseline
strategy called "Reset" on the same multi-turn conversation problem.

Both strategies see the same analyzer output (task_spec, aligned, issues
sections) and the same underlying conversation. Then:

  - **Reset**: templates the analyzer output into a structured
    "compacted conversation" message. No additional LLM call.
  - **Rewrite**: runs a SECOND LLM call that takes
    (analyzer output, full conversation) and rewrites them into a
    compacted context. This second LLM call can rephrase the spec,
    inline prior code/results, or add interpretive notes.

Your job: read the two compacted contexts, the last user message, the
two final assistant answers, and diagnose precisely *what* in the
Rewrite context caused the assistant to produce the wrong final answer
where Reset succeeded.

Output STRICT JSON with this schema (no prose outside the JSON):

{
  "spec_divergence":  {
    "kind": "<one of: vaguer, more_specific, phantom_added, phantom_dropped, format_lost, equivalent>",
    "explanation": "<one-sentence specific description>"
  },
  "work_so_far_divergence": {
    "rewrite_inlines_verbatim_code": <bool>,
    "rewrite_inlines_numerical_speculation": <bool>,
    "rewrite_omits_important_caveat": <bool>,
    "explanation": "<one-sentence specific description>"
  },
  "failure_chain": {
    "primary_cause": "<one of: spec_divergence, work_so_far_divergence, both, other>",
    "explanation": "<one-sentence: how the bad Rewrite context produced the bad answer>"
  },
  "rewrite_input_attribution": {
    "<one of: analyzer_output, conversation, rewrite_prompt, rewriter_hallucination>": "<one-sentence justification>"
  },
  "confidence": <float 0..1>
}

Definitions:
- spec_divergence.kind values:
    vaguer            : rewrite's spec is less specific / drops a constraint
    more_specific     : rewrite's spec is more specific (adds detail not in user msgs) — phantom or restated
    phantom_added     : rewrite's spec adds requirements the user did not state
    phantom_dropped   : rewrite's spec is missing a requirement the user did state
    format_lost       : rewrite drops an output-format directive the user/system established
    equivalent        : two specs are functionally equivalent
- "rewrite_inlines_verbatim_code": rewrite's "What Looks Right" / "Verified Work" includes a verbatim code block (SQL, Python, function call) from the prior conversation. This is suspicious because it anchors the assistant on that exact code.
- "rewrite_inlines_numerical_speculation": rewrite includes a speculative numerical result ("X would be 8") that wasn't established by the assistant in the conversation.
- "rewrite_omits_important_caveat": rewrite drops a key qualifier (e.g., "waiting for X to compute final answer") that Reset preserved.
- rewrite_input_attribution: which input to the rewrite LLM is most responsible?
    analyzer_output         : the upstream analyzer's task_spec/issues was already wrong/imprecise
    conversation            : the conversation contained prior code/numbers the rewriter latched onto
    rewrite_prompt          : the rewrite operation's prompt instructed behavior that produced the error
    rewriter_hallucination  : neither — the rewrite LLM added something neither in the analyzer output nor the conversation
"""


USER_TEMPLATE = """\
# Pair to diagnose

## Task: {task}

## System prompt (truncated)
```
{system_prompt}
```

## Last user message
```
{last_user}
```

## Reset compacted context (the BASELINE — succeeded)
```
{reset_compacted}
```

## Rewrite compacted context (the FAILURE — wrong final answer)
```
{rewrite_compacted}
```

## Rewrite's analysis LLM call output (intermediate; raw fields)
```
task_spec_from_analysis: {analysis_task_spec}
aligned_from_analysis:   {analysis_aligned}
issues_from_analysis:    {analysis_issues}
```

## Reset's extracted final answer (correct)
```
{reset_extracted}
```

## Rewrite's extracted final answer (incorrect)
```
{rewrite_extracted}
```

Diagnose per the schema. Output JSON only.
"""


def build_lb() -> LoadBalancerConfig:
    cfg = OmegaConf.load(str(LB_CFG_PATH))
    return LoadBalancerConfig.from_dict(OmegaConf.to_container(cfg, resolve=True))


def truncate(s: str | None, n: int) -> str:
    s = s or ""
    return s[:n]


async def diagnose_one(client: OpenAIModelClient, row: dict, model: str) -> dict:
    al = row.get("rewrite_analysis_log") or {}
    user = USER_TEMPLATE.format(
        task=row["task"],
        system_prompt=truncate(row.get("system_prompt"), 1500),
        last_user=truncate(row.get("last_user_message"), 600),
        reset_compacted=truncate(row.get("reset_compacted"), 2500),
        rewrite_compacted=truncate(row.get("rewrite_compacted"), 2500),
        analysis_task_spec=truncate(al.get("task_spec"), 800),
        analysis_aligned=truncate(al.get("aligned"), 600),
        analysis_issues=truncate(al.get("issues"), 600),
        reset_extracted=truncate(row.get("reset_extracted_answer"), 1000),
        rewrite_extracted=truncate(row.get("rewrite_extracted_answer"), 1000),
    )
    resp = await client.generate(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
        model=model,
        temperature=0.0,
        max_tokens=800,
        timeout=180,
        is_json=True,
    )
    text = resp.content.strip()
    try:
        diag = json.loads(text)
    except json.JSONDecodeError:
        import re
        m = re.search(r"\{.*\}", text, re.DOTALL)
        diag = json.loads(m.group(0)) if m else {"_parse_error": text[:400]}
    diag["sample_id"] = row["sample_id"]
    diag["task"] = row["task"]
    diag["conv"] = row["conv"]
    return diag


async def main(args: argparse.Namespace) -> None:
    rows = [json.loads(l) for l in (DATA_DIR / "pairs.jsonl").open()]
    # Balanced sample per task
    by_task: dict[str, list[dict]] = {}
    for r in rows:
        by_task.setdefault(r["task"], []).append(r)
    rng = random.Random(args.seed)
    sampled: list[dict] = []
    for task, lst in by_task.items():
        rng.shuffle(lst)
        sampled.extend(lst[: args.n_per_task])

    print(f"Diagnosing {len(sampled)} pairs (DeepSeek-V4-Flash)...")

    lb = build_lb()
    client = OpenAIModelClient(load_balancer_config=lb)
    sem = asyncio.Semaphore(args.concurrency)
    out_path = DATA_DIR / "diagnoses.jsonl"
    done = [0]

    async def worker(row):
        async with sem:
            try:
                r = await diagnose_one(client, row, args.model)
            except Exception as e:
                r = {"sample_id": row["sample_id"], "task": row["task"], "_error": str(e)[:200]}
            done[0] += 1
            kind = ""
            try:
                kind = r.get("spec_divergence", {}).get("kind", "?")
            except Exception:
                pass
            print(f"  [{done[0]}/{len(sampled)}] {row['task']:9s} {row['sample_id'][:36]:36s} spec={kind}", flush=True)
            return r

    tasks = [worker(r) for r in sampled]
    results: list[dict] = []
    with out_path.open("w") as f:
        for coro in asyncio.as_completed(tasks):
            res = await coro
            f.write(json.dumps(res) + "\n")
            f.flush()
            results.append(res)
    print(f"Wrote {len(results)} diagnoses to {out_path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="DeepSeek-V4-Flash")
    p.add_argument("--n-per-task", type=int, default=12)
    p.add_argument("--concurrency", type=int, default=8)
    p.add_argument("--seed", type=int, default=1)
    asyncio.run(main(p.parse_args()))

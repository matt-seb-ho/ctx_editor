"""LLM-driven categorization of Rewrite failure cases.

Reads `data/rewrite_failures.jsonl`, samples a balanced subset across tasks,
and queries DeepSeek-V4-Flash to classify each case into one or more
failure modes. Output: `data/rewrite_failure_labels.jsonl`.

Categories were seeded from human inspection of 4 representative cases
(one per task) where Rewrite regressed vs Reset/AO/Baseline. The worker
LLM is invited to pick from these categories OR propose an additional
short label if none fit.

Run with:
  python scripts/analysis_rewrite/categorize_failures.py --n-per-task 15

Requires env vars for Foundry auth (AzureCliCredential).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
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


CATEGORY_DEFINITIONS = """\
F1_LOST_META_STRUCTURE
  The compacted context lost a meta-level structural requirement that the
  raw conversation had — e.g., "compute both pairs", "return parallel
  function calls", "include all sub-results", "sum across sub-problems",
  or "specific column ordering". The assistant then produced a result
  that omits or restructures something it should have preserved.

F2_ANCHORED_ON_PARTIAL_WRONG_WORK
  The compacted context's "What Looks Right So Far" section preserved
  partial (but incorrect or premature) work from earlier turns, and the
  final assistant turn extended that partial work without re-deriving.
  Often the partial work is mathematically/logically wrong, but the
  compaction made it look authoritative.

F3_COMPACTION_INTERPRETIVE_BIAS
  The compaction itself did interpretive work (e.g., "the answer would
  probably be X" or "the next step is Y") that wasn't actually validated
  in the original conversation. The final assistant turn parroted the
  compaction's speculation as if it were established.

F4_OVERFIT_REQUIREMENTS
  Rewrite re-narrated the user's task spec in a way that added phantom
  requirements (extra columns, extra constraints, extra steps) the user
  never asked for, or dropped requirements the user did state. The
  assistant then produced an answer matching the rewritten (wrong) spec.

F5_SCHEMA_DETAIL_LOST
  The compacted context dropped task-critical reference material from
  the system prompt or earlier turns — e.g., specific table/column
  names, function signatures, test-case inputs, formatting requirements
  — that the assistant then had to guess at and got wrong.

F6_TONE_OR_FORMAT_MISMATCH
  The compaction reformatted the conversation in a way that changed
  the expected output format (e.g., switched from one answer style to
  another, dropped code-fence convention, lost \\boxed{} for math).

F7_OTHER
  The failure does not match any of the above; describe in <other_label>.
"""

SYSTEM_PROMPT = """\
You are a careful research-assistant LLM analyzing failure cases of a
"Context Rewrite" intervention for multi-turn conversations. The Rewrite
strategy:

  1. Reads a multi-turn conversation between a user and an assistant.
  2. Produces a "compacted context" with two sections: a Task Spec and
     a "What Looks Right So Far" summary.
  3. Replaces the full conversation with that compacted context + the
     latest user message, and lets the assistant continue.

We compared Rewrite against (a) Baseline (no intervention), (b) Reset
(template-based extraction from the same analyzer output, no extra LLM
call), and (c) AO (Assistant-Omitted: keep only user turns). Rewrite
underperforms all three on average. Your job: classify the failure mode
for individual cases.

Output STRICT JSON with the schema:
{
  "primary_category": "<one of F1..F7>",
  "secondary_categories": ["<F1..F7>", ...],
  "confidence": <0..1 float>,
  "rationale": "<one short sentence>",
  "other_label": "<only if primary == F7, a 2-4 word custom label>"
}

Do not include any text outside the JSON object.
"""


USER_TEMPLATE = """\
# Failure case

## Categories (pick the best primary; you may list additional secondary)
{categories}

## Task: {task}

## System prompt (truncated)
```
{system_prompt}
```

## Final user message (the one Rewrite's compaction was supposed to set up for)
```
{last_user}
```

## Rewrite's compacted context (what the assistant actually saw)
```
{compacted}
```

## Rewrite's final extracted answer
```
{rw_answer}
```

## Reset's final extracted answer (control — Reset got this right)
```
{rs_answer}
```

## Outcomes
- Rewrite: {rw_correct} (score={rw_score})
- Reset: {rs_correct} (score={rs_score})
- Baseline: {bl_correct} (score={bl_score})
- AO: {ao_correct} (score={ao_score})

## Instructions
Compare Rewrite's compacted context against the final user message and
the correct (Reset) answer. Diagnose: what aspect of the compaction
caused Rewrite to fail where Reset succeeded? Output JSON.
"""


def sample_balanced(rows: list[dict], n_per_task: int, seed: int = 1) -> list[dict]:
    rng = random.Random(seed)
    by_task: dict[str, list[dict]] = {}
    for r in rows:
        if not r["regression_vs_reset"]:
            continue
        by_task.setdefault(r["task"], []).append(r)
    out: list[dict] = []
    for task, lst in by_task.items():
        rng.shuffle(lst)
        out.extend(lst[:n_per_task])
    return out


def build_load_balancer() -> LoadBalancerConfig:
    cfg = OmegaConf.load(str(LB_CFG_PATH))
    return LoadBalancerConfig.from_dict(OmegaConf.to_container(cfg, resolve=True))


async def classify_one(client: OpenAIModelClient, row: dict, model: str) -> dict:
    user = USER_TEMPLATE.format(
        categories=CATEGORY_DEFINITIONS,
        task=row["task"],
        system_prompt=(row.get("system_prompt") or "")[:2500],
        last_user=(row.get("last_user_message") or "")[:800],
        compacted=(row.get("compacted_context") or "")[:3000],
        rw_answer=(row.get("rewrite_extracted_answer") or "")[:1500],
        rs_answer=(row.get("reset_extracted_answer") or "")[:1500],
        rw_correct=bool(row.get("rewrite_score")),
        rs_correct=bool(row.get("reset_score")),
        bl_correct=bool(row.get("baseline_score")),
        ao_correct=bool(row.get("ao_score")),
        rw_score=row.get("rewrite_score"),
        rs_score=row.get("reset_score"),
        bl_score=row.get("baseline_score"),
        ao_score=row.get("ao_score"),
    )
    resp = await client.generate(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
        model=model,
        temperature=0.0,
        max_tokens=600,
        timeout=180,
        is_json=True,
    )
    text = resp.content.strip()
    try:
        label = json.loads(text)
    except json.JSONDecodeError:
        # Try to extract a JSON object via regex fallback
        import re

        m = re.search(r"\{.*\}", text, re.DOTALL)
        label = json.loads(m.group(0)) if m else {"primary_category": "F7", "rationale": "JSON parse error", "_raw": text}
    label["sample_id"] = row["sample_id"]
    label["task"] = row["task"]
    label["conv"] = row["conv"]
    label["regression_vs_baseline"] = row["regression_vs_baseline"]
    label["regression_vs_reset"] = row["regression_vs_reset"]
    label["regression_vs_ao"] = row["regression_vs_ao"]
    return label


async def main(args: argparse.Namespace) -> None:
    rows = [json.loads(l) for l in (DATA_DIR / "rewrite_failures.jsonl").open()]
    sampled = sample_balanced(rows, args.n_per_task, args.seed)
    print(f"Sampled {len(sampled)} failures: " + str({t: sum(1 for r in sampled if r['task']==t) for t in {r['task'] for r in sampled}}), flush=True)

    lb = build_load_balancer()
    client = OpenAIModelClient(load_balancer_config=lb)

    sem = asyncio.Semaphore(args.concurrency)
    out_path = DATA_DIR / "rewrite_failure_labels.jsonl"
    # Stream results as they complete so we can monitor progress
    done = [0]

    async def worker(row, idx):
        async with sem:
            try:
                r = await classify_one(client, row, args.model)
            except Exception as e:
                r = {"sample_id": row["sample_id"], "task": row["task"], "conv": row["conv"], "primary_category": "ERROR", "rationale": str(e)[:200]}
            done[0] += 1
            print(f"  [{done[0]}/{len(sampled)}] {row['task']:9s} {row['sample_id'][:40]:40s} -> {r.get('primary_category')}", flush=True)
            return r

    tasks = [worker(r, i) for i, r in enumerate(sampled)]
    labels: list[dict] = []
    with out_path.open("w") as f:
        for coro in asyncio.as_completed(tasks):
            label = await coro
            f.write(json.dumps(label) + "\n")
            f.flush()
            labels.append(label)
    print(f"Wrote {len(labels)} labels to {out_path}")

    # Quick aggregation
    from collections import Counter

    by_task_cat: dict[str, Counter] = {}
    for l in labels:
        by_task_cat.setdefault(l["task"], Counter())[l.get("primary_category", "?")] += 1
    print("\nPrimary category counts by task:")
    for t, c in sorted(by_task_cat.items()):
        print(f"  {t}: {dict(c)}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="DeepSeek-V4-Flash")
    p.add_argument("--n-per-task", type=int, default=15)
    p.add_argument("--concurrency", type=int, default=20)
    p.add_argument("--seed", type=int, default=1)
    asyncio.run(main(p.parse_args()))

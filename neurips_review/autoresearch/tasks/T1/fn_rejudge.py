#!/usr/bin/env python
"""T1 §8.3 — arm-symmetric false-negative re-judge.

Problem this fixes. ``identify_false_negatives.analyze_sample`` builds the
user-sufficiency judge's prompt from ``get_active_messages(trace)``, i.e.
**visible** messages only. After a context reset the visible user messages are
the condensed text plus the latest shard, so the judge sees a truncated user
history, decides the user never specified the task, and the sample is dropped
from the ``adjusted_accuracy`` denominator. The exclusion rate then scales with
how aggressively an arm discards user text (9% for Baseline, 78% for the
summarisation arm) — post-treatment conditioning, invalid for cross-arm
comparison.

Fix. Re-run the *same* judge, with the *same* prompt, on the complete user
message history recovered from ``trace.messages`` (hidden messages are retained
there), de-duplicated in order. That input is identical across arms by
construction, because every arm receives the same shards from the same user
agent.

Deliberately reuses ``identify_false_negatives.analyze_sample`` verbatim rather
than reimplementing the prompt, so the only thing that changes between the
repo's number and this one is message visibility.

Usage:
    .venv/bin/python neurips_review/autoresearch/tasks/T1/fn_rejudge.py [cell ...]
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, "/home/t-matthewho/ac3/ctx_editor/src")

from ctx_editor.identify_false_negatives import analyze_sample  # noqa: E402
from ctx_editor.models import LoadBalancerConfig, OpenAIModelClient  # noqa: E402

ROOT = Path("/home/t-matthewho/ac3/ctx_editor")
MAIN = ROOT / "outputs" / "T1" / "main"
HERE = Path(__file__).parent
JUDGE = "gpt-5.4-mini_2026-03-17"
CONCURRENCY = 4


def load_trace(cell: Path, sample_id: str):
    hits = list(cell.glob(f"traces/*/*/{sample_id}.json"))
    if not hits:
        return None
    return json.load(open(hits[0]))


def all_visible(trace: dict) -> dict:
    """Return a copy of the trace with every message visible, deduplicated.

    Context resets re-add a copy of the latest user message, so a naive
    "make everything visible" would show the judge duplicates.
    """
    msgs = trace.get("messages") or trace.get("trace", {}).get("messages") or []
    out, seen = [], set()
    for m in msgs:
        key = (m.get("role"), m.get("content"))
        if key in seen:
            continue
        seen.add(key)
        m = dict(m)
        m["visible"] = True
        out.append(m)
    return {"messages": out}


async def rejudge_cell(cell: Path, client) -> dict:
    results = json.load(open(cell / "results.json"))
    incorrect = [r for r in results if not r["is_correct"] and not r.get("metadata", {}).get("error")]
    sem = asyncio.Semaphore(CONCURRENCY)

    async def one(r):
        tr = load_trace(cell, r["sample_id"])
        if tr is None:
            return None
        sample = dict(r)
        sample["trace"] = all_visible(tr)
        async with sem:
            try:
                return await analyze_sample(sample, client, JUDGE)
            except Exception as e:
                print(f"  ERROR {r['sample_id']}: {e}")
                return None

    out = await asyncio.gather(*[one(r) for r in incorrect])
    out = [o for o in out if o is not None]

    correct = sum(1 for r in results if r["is_correct"])
    total = len(results)
    induced = [o.sample_id for o in out if not o.user_sim_sufficient]
    adj_total = total - len(induced)
    return {
        "cell": cell.name,
        "raw_correct": correct,
        "raw_total": total,
        "raw_accuracy": correct / total if total else 0.0,
        "n_incorrect_judged": len(out),
        "user_sim_induced_symmetric": len(induced),
        "user_sim_induced_ids": sorted(induced),
        "adjusted_total_symmetric": adj_total,
        "adjusted_accuracy_symmetric": correct / adj_total if adj_total else 0.0,
    }


async def main(cells):
    import yaml
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    lb_yaml = yaml.safe_load(
        (ROOT / "src/ctx_editor/config/load_balancer/trapi.yaml").read_text()
    )
    lb = LoadBalancerConfig.from_dict(lb_yaml)
    client = OpenAIModelClient(load_balancer_config=lb)
    rows = []
    for name in cells:
        cell = MAIN / name
        if not (cell / "results.json").exists():
            print(f"[skip] {name}: no results.json")
            continue
        print(f"[rejudge] {name} ...", flush=True)
        row = await rejudge_cell(cell, client)
        rows.append(row)
        print(
            f"  raw {row['raw_correct']}/{row['raw_total']} = {row['raw_accuracy']:.1%}"
            f"  | symmetric-adjusted {row['raw_correct']}/{row['adjusted_total_symmetric']}"
            f" = {row['adjusted_accuracy_symmetric']:.1%}"
            f"  ({row['user_sim_induced_symmetric']} excluded of {row['n_incorrect_judged']} judged)",
            flush=True,
        )
    out = HERE / "fn_rejudge.json"
    json.dump(rows, open(out, "w"), indent=2)
    print(f"[written] {out}")


if __name__ == "__main__":
    cells = sys.argv[1:] or sorted(
        d.name for d in MAIN.iterdir() if d.is_dir() and not d.name.startswith("BUGGY")
    )
    asyncio.run(main(cells))

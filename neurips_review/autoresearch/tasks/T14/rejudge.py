#!/usr/bin/env python
"""T14 — arm-symmetric false-negative re-judge across the archived LiC matrix.

Direct extension of ``neurips_review/autoresearch/tasks/T1/fn_rejudge.py``; the
judging logic is ``identify_false_negatives.analyze_sample`` verbatim, so the only
thing that differs between the shipped number and this one is which messages the
judge is shown.

Two modes, selected per-run:

``symmetric``  every message in ``trace.messages`` is marked visible (deduplicated
               in order). Identical user-message union in every arm by construction,
               because every arm receives the same shards from the same user agent.
``visible``    reproduce the shipped path exactly (honour the stored ``visible``
               flags). Used as a control: running this with *our* judge model and
               comparing against the shipped ``false_negatives.json`` (which used
               ``gpt-5-mini``) isolates judge-model drift from the visibility effect.

Usage:
    .venv/bin/python neurips_review/autoresearch/tasks/T14/rejudge.py \
        --group post_neurips_ac3_phase1 --mode symmetric [--limit N] [--out FILE]
"""
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, "/home/t-matthewho/ac3/ctx_editor/src")

from ctx_editor.identify_false_negatives import analyze_sample  # noqa: E402
from ctx_editor.models import LoadBalancerConfig, OpenAIModelClient  # noqa: E402

ROOT = Path("/home/t-matthewho/ac3/ctx_editor")
HERE = Path(__file__).parent
JUDGE = "gpt-5.4-mini_2026-03-17"


def load_trace_messages(run: Path, sample_id: str):
    """Trace filenames sanitise '/' to '_' (e.g. 'sharded-HumanEval/105')."""
    for name in (sample_id, sample_id.replace("/", "_")):
        hits = list(run.glob(f"traces/*/*/{name}.json"))
        if hits:
            d = json.load(open(hits[0]))
            tr = d.get("trace") if isinstance(d.get("trace"), dict) else d
            return tr.get("messages") or []
    return None


def build_trace(messages: list[dict], mode: str) -> dict:
    if mode == "visible":
        return {"messages": messages}
    out, seen = [], set()
    for m in messages:
        key = (m.get("role"), m.get("content"))
        if key in seen:
            continue
        seen.add(key)
        m = dict(m)
        m["visible"] = True
        out.append(m)
    return {"messages": out}


async def rejudge_run(run: Path, client, mode: str, sem, limit=None) -> dict:
    results = json.load(open(run / "results.json"))
    incorrect = [
        r for r in results
        if not r["is_correct"] and not (r.get("metadata") or {}).get("error")
    ]
    if limit:
        incorrect = incorrect[:limit]

    async def one(r):
        msgs = load_trace_messages(run, r["sample_id"])
        if msgs is None:
            return ("missing", r["sample_id"], None)
        sample = dict(r)
        sample["trace"] = build_trace(msgs, mode)
        # how many user turns the judge will actually see, for the audit trail
        n_user_seen = sum(
            1 for m in sample["trace"]["messages"]
            if m.get("role") == "user" and m.get("visible", True)
        )
        n_user_total = sum(1 for m in msgs if m.get("role") == "user")
        async with sem:
            for attempt in range(3):
                try:
                    res = await analyze_sample(sample, client, JUDGE)
                    return ("ok", r["sample_id"], (res.user_sim_sufficient, n_user_seen, n_user_total))
                except Exception as e:
                    if attempt == 2:
                        return ("error", r["sample_id"], str(e)[:200])
                    await asyncio.sleep(2 * (attempt + 1))

    out = await asyncio.gather(*[one(r) for r in incorrect])
    ok = [o for o in out if o[0] == "ok"]
    errs = [o for o in out if o[0] == "error"]
    missing = [o for o in out if o[0] == "missing"]

    correct = sum(1 for r in results if r["is_correct"])
    total = len([r for r in results if not (r.get("metadata") or {}).get("error")])
    induced = [o[1] for o in ok if not o[2][0]]

    summ = json.load(open(run / "run_summary.json"))
    shipped = summ.get("metrics", {})
    fn = json.load(open(run / "false_negatives.json"))

    return {
        "run": str(run),
        "cell": run.name,
        "mode": mode,
        "judge": JUDGE,
        "raw_correct": correct,
        "raw_total": total,
        "raw_accuracy": correct / total if total else 0.0,
        "shipped_excluded": fn.get("summary", {}).get("user_sim_induced"),
        "shipped_analysed": fn.get("total_analyzed"),
        "shipped_adjusted_accuracy": shipped.get("adjusted_accuracy"),
        "n_judged": len(ok),
        "n_errors": len(errs),
        "n_missing_trace": len(missing),
        "excluded": len(induced),
        "excluded_ids": sorted(induced),
        "adjusted_total": total - len(induced),
        "adjusted_accuracy": correct / (total - len(induced)) if total - len(induced) > 0 else 0.0,
        # audit trail: how truncated the judge's view was
        "mean_user_turns_seen": (
            sum(o[2][1] for o in ok) / len(ok) if ok else None
        ),
        "mean_user_turns_total": (
            sum(o[2][2] for o in ok) / len(ok) if ok else None
        ),
        "errors": [(o[1], o[2]) for o in errs][:5],
    }


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", default="post_neurips_ac3_phase1")
    ap.add_argument("--snapshot", default="/home/t-matthewho/ac3/t14_snapshot/ctx_editor/outputs")
    ap.add_argument("--mode", default="symmetric", choices=["symmetric", "visible"])
    ap.add_argument("--concurrency", type=int, default=5)
    ap.add_argument("--limit", type=int, default=None, help="max incorrect samples per run")
    ap.add_argument("--runs", type=int, default=None, help="max runs")
    ap.add_argument("--filter", default="", help="substring filter on run dir name")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    import yaml
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    lb = LoadBalancerConfig.from_dict(
        yaml.safe_load((ROOT / "src/ctx_editor/config/load_balancer/trapi.yaml").read_text())
    )
    client = OpenAIModelClient(load_balancer_config=lb)

    base = Path(args.snapshot) / args.group
    runs = sorted(p.parent for p in base.rglob("false_negatives.json"))
    if args.filter:
        runs = [r for r in runs if args.filter in r.name]
    if args.runs:
        runs = runs[: args.runs]

    out_path = Path(args.out) if args.out else HERE / f"rejudge_{args.group}_{args.mode}.json"
    rows = []
    if out_path.exists():
        rows = json.load(open(out_path))
    done = {r["run"] for r in rows}

    sem = asyncio.Semaphore(args.concurrency)
    t0 = time.time()
    for i, run in enumerate(runs, 1):
        if str(run) in done:
            continue
        row = await rejudge_run(run, client, args.mode, sem, args.limit)
        rows.append(row)
        json.dump(rows, open(out_path, "w"), indent=2)
        print(
            f"[{i}/{len(runs)}] {run.name}  raw {row['raw_correct']}/{row['raw_total']}"
            f"={row['raw_accuracy']:.1%}  shipped-adj={row['shipped_adjusted_accuracy']}"
            f"  shipped-excl={row['shipped_excluded']}/{row['shipped_analysed']}"
            f"  {args.mode}-excl={row['excluded']}/{row['n_judged']}"
            f"  adj={row['adjusted_accuracy']:.1%}"
            f"  userturns seen/total={row['mean_user_turns_seen']}/{row['mean_user_turns_total']}"
            f"  err={row['n_errors']} miss={row['n_missing_trace']}"
            f"  [{time.time()-t0:.0f}s]",
            flush=True,
        )
    print(f"[written] {out_path}")


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""T11 — WildChat judge position-bias + judge-agreement re-judging harness.

Reads recovered Phase-3b WildChat turn results (AO vs AC3-Reset / AC3-Augment)
and re-runs the *judging* step only, under controlled presentation order.

Modes
-----
  --mode order      : judge every selected pair in BOTH orders (AO-first, VAR-first)
  --mode repeat     : judge every selected pair again in a FIXED order (self-consistency)
  --mode control    : positive control -- good response vs. a degraded copy of itself

Output: one JSONL per run with one record per (pair, order) judgement.

Nothing in src/ is modified; the judge prompt is read from the live harness file
so the prompt is byte-identical to the one that produced the headline numbers.
"""

import argparse
import asyncio
import json
import os
import random
import sys
import time
from pathlib import Path

REPO = Path("/home/t-matthewho/ac3/ctx_editor")
sys.path.insert(0, str(REPO / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO / ".env")

from ctx_editor.models import get_model_client  # noqa: E402
from ctx_editor.models.endpoint_config import LoadBalancerConfig  # noqa: E402

JUDGE_PROMPT = (REPO / "src/ctx_editor/huang_eval/prompts/pairwise_judge.txt").read_text()

RECOVERED = Path("/home/t-matthewho/ac3/recovered/ctx_editor/outputs")
PHASE1 = RECOVERED / "huang_eval/phase1/2026-03-24/02-22-57"
PHASE3 = RECOVERED / "post_neurips_ac3_phase3_huang"


# ----------------------------------------------------------------------------- data
def load_conversations() -> dict:
    convs = {}
    for f in sorted((PHASE1 / "conversations").glob("*.json")):
        c = json.loads(f.read_text())
        convs[c["conversation_id"]] = c
    return convs


def load_pairs() -> list[dict]:
    """Every (AO, variant) response pair from the 6 Phase-3b cells."""
    pairs = []
    for cell in sorted(PHASE3.glob("*_seed*")):
        name = cell.name
        variant = "s15" if name.startswith("s15") else "augment"
        seed = int(name.split("_seed")[1].split("_")[0])
        f = cell / "turn_results.jsonl"
        if not f.exists():
            continue
        for i, line in enumerate(f.read_text().splitlines()):
            if not line.strip():
                continue
            r = json.loads(line)
            key = f"{variant}_vs_ao"
            orig = r["judgments"].get(f"ao_vs_{variant}", {})
            pairs.append(
                {
                    "pair_id": f"{variant}|{seed}|{r['conversation_id']}|{r['turn_index']}",
                    "cell": name,
                    "variant": variant,
                    "seed": seed,
                    "conversation_id": r["conversation_id"],
                    "turn_index": r["turn_index"],
                    "turn_type": r.get("turn_type"),
                    "ao_response": r["ao_response"],
                    "var_response": r[f"{variant}_response"],
                    "orig_quality_winner": orig.get("quality_winner"),
                    "orig_ontopic_winner": orig.get("ontopic_winner"),
                    "orig_confidence": orig.get("confidence"),
                    "_pk": key,
                }
            )
    return pairs


def _format_context(turns):
    parts = [f"[{m['role']}]\n{m['content']}" for m in turns]
    return "\n\n".join(parts) if parts else "(No prior context)"


def _parse_json(text: str):
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
    s = text.strip()
    if s.startswith("```"):
        lines = s.split("\n")
        lines = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        try:
            return json.loads("\n".join(lines))
        except Exception:
            pass
    start = text.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : i + 1])
                    except Exception:
                        break
    return None


def build_prompt(turns, turn_index, first_resp, second_resp):
    user_turns = [i for i, t in enumerate(turns) if t["role"] == "user"]
    round_num = user_turns.index(turn_index) + 1 if turn_index in user_turns else 1
    total_rounds = len(user_turns)
    ctx = _format_context(turns[:turn_index])
    return (
        JUDGE_PROMPT.replace("{round_num}", str(round_num))
        .replace("{total_rounds}", str(total_rounds))
        .replace("{context_for_a}", ctx)
        .replace("{first_resp}", first_resp)
        .replace("{context_for_b}", ctx)
        .replace("{second_resp}", second_resp)
    )


# ----------------------------------------------------------------------------- judging
async def judge_once(client, model, turns, turn_index, first_resp, second_resp,
                     assignment, temperature, sem, retries=3):
    prompt = build_prompt(turns, turn_index, first_resp, second_resp)
    async with sem:
        last_err = None
        for attempt in range(retries):
            try:
                resp = await client.generate(
                    messages=[{"role": "user", "content": prompt}],
                    model=model,
                    temperature=temperature,
                    timeout=180,
                )
                parsed = _parse_json(resp.content)
                if parsed and "quality_winner" in parsed:
                    def m(raw):
                        raw = str(raw).strip().upper()
                        if raw in ("A", "B"):
                            return assignment[raw]
                        return "tie"
                    return {
                        "ok": True,
                        "quality_winner": m(parsed.get("quality_winner", "tie")),
                        "ontopic_winner": m(parsed.get("ontopic_winner", "tie")),
                        "quality_winner_pos": str(parsed.get("quality_winner", "tie")).strip().upper(),
                        "confidence": float(parsed.get("confidence", 0.5) or 0.5),
                        "raw_len": len(resp.content or ""),
                    }
                last_err = f"parse_fail: {(resp.content or '')[:200]}"
            except Exception as e:  # noqa: BLE001
                last_err = f"{type(e).__name__}: {e}"[:300]
            await asyncio.sleep(2 + 3 * attempt)
        # HARD failure -- recorded explicitly, never silently coerced to "tie"
        return {"ok": False, "error": last_err}


def degrade(text: str) -> str:
    """Obviously-degraded copy of a response: truncated mid-sentence, first 25%,
    with a generic filler tail. Used as the positive control."""
    n = max(60, int(len(text) * 0.25))
    head = text[:n]
    return head + "\n\nAnyway, that's basically it. Let me know if you want more."


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["order", "repeat", "control"], required=True)
    ap.add_argument("--judge-model", required=True)
    ap.add_argument("--load-balancer", default="t9_foundry_trapi")
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0, help="subsample N pairs (stratified by cell)")
    ap.add_argument("--max-concurrent", type=int, default=5)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--fixed-order", default="ao_first", choices=["ao_first", "var_first"])
    ap.add_argument("--subset-file", default="", help="json list of pair_ids to restrict to")
    args = ap.parse_args()

    import yaml
    lb_path = REPO / f"src/ctx_editor/config/load_balancer/{args.load_balancer}.yaml"
    lb = LoadBalancerConfig.from_dict(yaml.safe_load(lb_path.read_text()))
    client = get_model_client(args.judge_model, lb)

    convs = load_conversations()
    pairs = load_pairs()

    if args.subset_file:
        keep = set(json.loads(Path(args.subset_file).read_text()))
        pairs = [p for p in pairs if p["pair_id"] in keep]
    elif args.limit:
        # stratified: round-robin across cells, deterministic
        rng = random.Random(1234)
        bycell = {}
        for p in pairs:
            bycell.setdefault(p["cell"], []).append(p)
        for v in bycell.values():
            rng.shuffle(v)
        out, i = [], 0
        cells = sorted(bycell)
        while len(out) < args.limit and any(len(bycell[c]) > i for c in cells):
            for c in cells:
                if len(bycell[c]) > i and len(out) < args.limit:
                    out.append(bycell[c][i])
            i += 1
        pairs = out

    print(f"[T11] mode={args.mode} judge={args.judge_model} pairs={len(pairs)}", flush=True)
    sem = asyncio.Semaphore(args.max_concurrent)
    outf = Path(args.out)
    outf.parent.mkdir(parents=True, exist_ok=True)
    lock = asyncio.Lock()
    fh = outf.open("w")
    done = [0]
    t0 = time.time()

    async def one(p, order):
        turns = convs[p["conversation_id"]]["turns"]
        ao, var = p["ao_response"], p["var_response"]
        if args.mode == "control":
            good, bad = var, degrade(var)
            if order == "good_first":
                first, second, asg = good, bad, {"A": "good", "B": "degraded"}
            else:
                first, second, asg = bad, good, {"A": "degraded", "B": "good"}
        else:
            if order == "ao_first":
                first, second, asg = ao, var, {"A": "ao", "B": "var"}
            else:
                first, second, asg = var, ao, {"A": "var", "B": "ao"}
        res = await judge_once(client, args.judge_model, turns, p["turn_index"],
                               first, second, asg, args.temperature, sem)
        rec = {k: p[k] for k in ("pair_id", "cell", "variant", "seed", "conversation_id",
                                 "turn_index", "turn_type", "orig_quality_winner")}
        rec["order"] = order
        rec["judge_model"] = args.judge_model
        rec["mode"] = args.mode
        rec.update(res)
        async with lock:
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            done[0] += 1
            if done[0] % 25 == 0:
                print(f"  {done[0]} judgements  ({time.time()-t0:.0f}s)", flush=True)

    if args.mode == "order":
        orders = ["ao_first", "var_first"]
    elif args.mode == "repeat":
        orders = [args.fixed_order]
    else:
        orders = ["good_first", "degraded_first"]

    tasks = [one(p, o) for p in pairs for o in orders]
    await asyncio.gather(*tasks)
    fh.close()
    print(f"[T11] wrote {done[0]} records -> {outf}  ({time.time()-t0:.0f}s)", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

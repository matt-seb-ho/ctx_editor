"""Recoverability instrument for the entanglement knob (validation of the eval construction).

For every entangled user turn in a saved trace, we measure two quantities by asking a *recoverer*
LLM to reconstruct the turn's stand-alone intent, then a *matcher* LLM to score that reconstruction
against the gold shard the turn was supposed to convey:

  informed_recoverability  = recover(prior USER turns + prior ASSISTANT turns + this user turn)
  blinded_recoverability   = recover(prior USER turns ONLY               + this user turn)

Interpretation (Choi 2021 / concept_exploration.md §1.1, §2):
  * faithfulness   = informed_recoverability   -> should be HIGH at every level (intent preserved,
                     recoverable once you can read the assistant turn it depends on).
  * entanglement   = informed - blinded        -> should GROW with the requested level (the turn
                     becomes uninterpretable without the assistant turns).
  * leakage/independence = blinded_recoverability -> should FALL with level.

The recoverer/matcher model is deliberately a DIFFERENT family (gpt-5.4-mini) from the entangling
generator (gpt-4o) to avoid validating the generator against itself.

Usage:
  python -m research.entanglement.src.recoverability \
      --results-dir research/entanglement/artifacts/<run> \
      --data data/dev_math_subset.json \
      --out research/entanglement/artifacts/recoverability/<name>.json
"""

import argparse
import asyncio
import json
import os
import re
from pathlib import Path
from typing import Any, Optional

from azure.identity import (
    AzureCliCredential,
    ChainedTokenCredential,
    ManagedIdentityCredential,
)
from openai import AsyncOpenAI

SCOPE = "api://trapi/.default"
ENDPOINT = "https://trapi.research.microsoft.com/redmond/interactive/openai/v1/"
# Judge (recoverer + matcher). Override with RECOV_JUDGE_MODEL to check judge-family invariance.
JUDGE_MODEL = os.environ.get("RECOV_JUDGE_MODEL", "gpt-5.4-mini_2026-03-17")

_credential = ChainedTokenCredential(AzureCliCredential(), ManagedIdentityCredential())


def _fresh_client() -> AsyncOpenAI:
    token = _credential.get_token(SCOPE).token
    return AsyncOpenAI(base_url=ENDPOINT, api_key=token)


_client = _fresh_client()

_sem = asyncio.Semaphore(12)


async def _chat(messages: list[dict], max_tokens: int = 400) -> str:
    async with _sem:
        for attempt in range(4):
            try:
                resp = await _client.chat.completions.create(
                    model=JUDGE_MODEL, messages=messages, max_completion_tokens=max_tokens
                )
                return resp.choices[0].message.content or ""
            except Exception as e:  # noqa: BLE001
                if attempt == 3:
                    return f"__ERROR__ {e}"
                await asyncio.sleep(2 * (attempt + 1))
    return "__ERROR__"


RECOVER_PROMPT = """You are reconstructing what a user MEANT by their latest message in a chat with an AI assistant.
You are given the conversation available to you (some of it may be hidden). Rewrite ONLY the user's
LAST message into a single self-contained, stand-alone sentence that states the concrete information
or request the user is conveying, as if it were said with no prior context. If the last message is
too dependent on hidden context to reconstruct, write exactly: UNRECOVERABLE.

Conversation available to you:
{context}

The user's LAST message to reconstruct:
{last_user}

Stand-alone reconstruction (one sentence, or UNRECOVERABLE):"""

MATCH_PROMPT = """You are grading whether a reconstructed user intent matches a gold piece of information.

Gold information the user was trying to convey:
{gold}

Reconstructed intent:
{recon}

Does the reconstruction convey the SAME concrete information as the gold (same quantities, same
relation)? Answer with a single number:
1.0 = fully conveys the gold information
0.5 = partially (right topic, missing or wrong specifics)
0.0 = does not convey it, or is UNRECOVERABLE
Answer with just the number."""


def _extract_score(text: str) -> float:
    m = re.search(r"(1\.0|0\.5|0\.0|1|0)", text)
    if not m:
        return 0.0
    v = float(m.group(1))
    return max(0.0, min(1.0, v))


def _load_gold_shards(data_path: Path) -> dict[str, dict[int, str]]:
    """normalized_task_id -> {shard_id -> shard_text}. Keys normalized (/,- -> _)."""
    data = json.loads(data_path.read_text())
    out: dict[str, dict[int, str]] = {}
    for s in data:
        tid = str(s.get("task_id")).replace("/", "_")
        out[tid] = {int(sh["shard_id"]): sh["shard"] for sh in s.get("shards", [])}
    return out


def _iter_traces(results_dir: Path):
    tdir = results_dir / "traces"
    for f in tdir.rglob("*.json"):
        try:
            yield f, json.loads(f.read_text())
        except Exception:  # noqa: BLE001
            continue


def _messages_of(trace: dict) -> list[dict]:
    return trace.get("messages") or trace.get("trace", {}).get("messages") or []


async def _score_turn(
    prior_user: list[str], prior_assistant: list[str], last_user: str, gold: str
) -> dict:
    # blinded: user-only context
    blinded_ctx = (
        "\n".join(f"[user] {u}" for u in prior_user) if prior_user else "(no prior messages)"
    )
    # informed: interleave user + assistant (assistant turns visible)
    informed_lines = []
    for i, u in enumerate(prior_user):
        informed_lines.append(f"[user] {u}")
        if i < len(prior_assistant):
            informed_lines.append(f"[assistant] {prior_assistant[i]}")
    informed_ctx = "\n".join(informed_lines) if informed_lines else "(no prior messages)"

    blinded_recon, informed_recon = await asyncio.gather(
        _chat([{"role": "user", "content": RECOVER_PROMPT.format(context=blinded_ctx, last_user=last_user)}]),
        _chat([{"role": "user", "content": RECOVER_PROMPT.format(context=informed_ctx, last_user=last_user)}]),
    )
    blinded_score_txt, informed_score_txt = await asyncio.gather(
        _chat([{"role": "user", "content": MATCH_PROMPT.format(gold=gold, recon=blinded_recon)}], max_tokens=10),
        _chat([{"role": "user", "content": MATCH_PROMPT.format(gold=gold, recon=informed_recon)}], max_tokens=10),
    )
    return {
        "gold": gold,
        "last_user": last_user,
        "blinded_recon": blinded_recon,
        "informed_recon": informed_recon,
        "blinded": _extract_score(blinded_score_txt),
        "informed": _extract_score(informed_score_txt),
    }


async def analyze(results_dir: Path, data_path: Path) -> dict:
    gold_map = _load_gold_shards(data_path)
    tasks = []
    meta = []
    for f, trace in _iter_traces(results_dir):
        msgs = _messages_of(trace)
        stem = f.stem  # e.g. sharded-GSM8K_1166
        shard_lookup = gold_map.get(stem)
        if shard_lookup is None:
            for k, v in gold_map.items():
                if stem.endswith(k) or k.endswith(stem) or k in stem:
                    shard_lookup = v
                    break
        if shard_lookup is None:
            continue

        prior_user: list[str] = []
        prior_assistant: list[str] = []
        for m in msgs:
            role = m.get("role")
            content = m.get("content", "")
            if role == "user":
                md = m.get("metadata") or {}
                lvl = md.get("entanglement_level")
                sid = md.get("revealed_shard_id")
                gold = None
                if sid is not None:
                    try:
                        gold = shard_lookup.get(int(sid))
                    except (TypeError, ValueError):
                        gold = None
                # Only score entangled turns that reveal a resolvable gold shard.
                if lvl is not None and gold and content.strip():
                    tasks.append(
                        _score_turn(list(prior_user), list(prior_assistant), content, gold)
                    )
                    meta.append(
                        {
                            "file": f.name,
                            "level": lvl,
                            "shard_id": sid,
                            "self_report": md.get("decontextualized"),
                        }
                    )
                prior_user.append(content)
            elif role == "assistant":
                prior_assistant.append(content)
    results = await asyncio.gather(*tasks) if tasks else []
    for r, mrow in zip(results, meta):
        r.update(mrow)

    # aggregate by level
    by_level: dict[Any, list[dict]] = {}
    for r in results:
        by_level.setdefault(r.get("level"), []).append(r)
    agg = {}
    for lvl, rows in sorted(by_level.items(), key=lambda kv: (kv[0] is None, kv[0])):
        n = len(rows)
        inf = sum(x["informed"] for x in rows) / n if n else 0.0
        bl = sum(x["blinded"] for x in rows) / n if n else 0.0
        agg[str(lvl)] = {
            "n_turns": n,
            "informed_recoverability_faithfulness": round(inf, 3),
            "blinded_recoverability_independence": round(bl, 3),
            "entanglement_gap": round(inf - bl, 3),
        }
    return {"aggregate_by_level": agg, "per_turn": results}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = asyncio.run(analyze(Path(args.results_dir), Path(args.data)))
    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(out, indent=2))
    print(json.dumps(out["aggregate_by_level"], indent=2))
    print(f"\nWrote {outp}")


if __name__ == "__main__":
    main()

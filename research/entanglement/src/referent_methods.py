"""Philippe's method-comparison figure, measured on the referent construction.

The referent construction (see referent_demo.py) is the regime where entanglement is REAL: the
user's intent is carried by a pointer into an assistant-introduced referent, so dropping the
assistant turn destroys the intent. That is precisely the regime where context-management methods
differ. We measure, per entanglement level, whether the user's intent still survives under each
method, using the recoverability instrument as the survival proxy:

  accumulate (S0)          = INFORMED recoverability
                             (assistant turns kept -> referent resolvable). Should stay HIGH.
  omit-assistant (Huang)   = BLINDED recoverability
                             (assistant turns dropped -> referent gone). Should COLLAPSE with level.
  decontextualize-then-edit (ours)
                           = first REWRITE the user turn to be self-contained *using* the assistant
                             context (the inverse of entangling; Choi 2021), THEN drop the assistant
                             and measure blinded recoverability of the rewritten turn. Should stay
                             HIGH -- the content is relocated back into the user turn before the
                             assistant is dropped, so dropping it is now lossless.

This is exactly Philippe's predicted matrix: drop-assistant only survives at low entanglement;
accumulate is fine on recoverability (it pays elsewhere, in pollution); decontextualize-then-edit
holds across all levels. x-axis = entanglement level, one line per method.

Usage:
  python research/entanglement/src/referent_methods.py \
      --out research/entanglement/artifacts/referent_methods
"""

import argparse
import asyncio
import importlib.util
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

_here = Path(__file__)
_spec = importlib.util.spec_from_file_location("recoverability", str(_here.with_name("recoverability.py")))
_rec = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_rec)
_demo_spec = importlib.util.spec_from_file_location("referent_demo", str(_here.with_name("referent_demo.py")))
_demo = importlib.util.module_from_spec(_demo_spec)
_demo_spec.loader.exec_module(_demo)

SEEDS = _demo.SEEDS


DECON_PROMPT = """You are rewriting a user's latest message so it stands on its own.
You can see the full conversation, including the assistant's turns. Rewrite ONLY the user's LAST
message into a single self-contained instruction that a fresh assistant could act on WITHOUT seeing
any of the prior conversation -- resolve every reference ("option B", "that function", "the last
one", "the second step") into the concrete thing it points to, using the conversation to look it up.
Preserve the user's intent exactly; do not add or drop requirements.

Full conversation:
{context}

The user's LAST message to rewrite as self-contained:
{last_user}

Self-contained rewrite (one message):"""


async def _decontextualize(prior_user: list[str], prior_assistant: list[str], last_user: str) -> str:
    lines = []
    for i, u in enumerate(prior_user):
        lines.append(f"[user] {u}")
        if i < len(prior_assistant):
            lines.append(f"[assistant] {prior_assistant[i]}")
    context = "\n".join(lines) if lines else "(no prior messages)"
    out = await _rec._chat(
        [{"role": "user", "content": DECON_PROMPT.format(context=context, last_user=last_user)}],
        max_tokens=300,
    )
    return out.strip()


async def _score_methods(seed: dict, lvl: int) -> dict:
    prior_user = [seed["base"]]
    prior_assistant = [seed["assistant"]]
    last_user = seed["turns"][lvl]
    gold = seed["gold"]

    # accumulate & omit come straight from the recoverability instrument (informed / blinded).
    base = await _rec._score_turn(list(prior_user), list(prior_assistant), last_user, gold)

    # decontextualize-then-edit: rewrite using assistant context, then measure with NO assistant.
    rewritten = await _decontextualize(prior_user, prior_assistant, last_user)
    # blinded recovery of the rewritten turn (user context only, assistant dropped)
    blinded_ctx = "\n".join(f"[user] {u}" for u in prior_user) if prior_user else "(no prior messages)"
    recon = await _rec._chat(
        [{"role": "user", "content": _rec.RECOVER_PROMPT.format(context=blinded_ctx, last_user=rewritten)}]
    )
    score_txt = await _rec._chat(
        [{"role": "user", "content": _rec.MATCH_PROMPT.format(gold=gold, recon=recon)}], max_tokens=10
    )
    decon_score = _rec._extract_score(score_txt)

    return {
        "level": lvl,
        "accumulate": base["informed"],
        "omit_assistant": base["blinded"],
        "decon_then_edit": decon_score,
        "rewritten": rewritten,
        "gold": gold,
    }


async def _run():
    tasks = [_score_methods(seed, lvl) for seed in SEEDS for lvl in (0, 1, 2, 3)]
    rows = await asyncio.gather(*tasks)
    by_level = {}
    for r in rows:
        by_level.setdefault(r["level"], []).append(r)
    agg = {}
    for lvl in sorted(by_level):
        rs = by_level[lvl]
        n = len(rs)
        agg[str(lvl)] = {
            "n": n,
            "accumulate": round(sum(x["accumulate"] for x in rs) / n, 3),
            "omit_assistant": round(sum(x["omit_assistant"] for x in rs) / n, 3),
            "decon_then_edit": round(sum(x["decon_then_edit"] for x in rs) / n, 3),
        }
    return {"aggregate_by_level": agg, "per_turn": rows}


def _figure(agg: dict, out: Path):
    levels = sorted(int(k) for k in agg)
    methods = [
        ("accumulate", "Accumulate (S0) — keep assistant", "#888888", "s", "-"),
        ("omit_assistant", "Drop-assistant (Huang/ERGO)", "#d1495b", "^", "--"),
        ("decon_then_edit", "Decontextualize-then-edit (ours)", "#2e8540", "o", "-"),
    ]
    plt.figure(figsize=(7.2, 5))
    for key, label, color, marker, ls in methods:
        ys = [agg[str(l)][key] for l in levels]
        plt.plot(levels, ys, marker=marker, color=color, linewidth=2.4, markersize=8,
                 linestyle=ls, label=label)
    plt.xlabel("Entanglement level  (0 = independent  →  3 = intent carried purely by reference)")
    plt.ylabel("Intent survival  (recoverability vs gold)")
    plt.title("Context management under real entanglement (referent construction)\n"
              "Drop-assistant collapses as entanglement rises; decontextualize-then-edit holds.")
    plt.xticks(levels, [f"e{l}" for l in levels])
    plt.ylim(-0.02, 1.05)
    plt.grid(True, alpha=0.3)
    plt.legend(loc="lower left", fontsize=9)
    plt.tight_layout()
    plt.savefig(out, dpi=150)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    res = asyncio.run(_run())
    (outdir / "result.json").write_text(json.dumps(res, indent=2))
    _figure(res["aggregate_by_level"], outdir / "figure.png")
    print(json.dumps(res["aggregate_by_level"], indent=2))
    print(f"\nWrote {outdir/'result.json'}, {outdir/'figure.png'}")


if __name__ == "__main__":
    main()

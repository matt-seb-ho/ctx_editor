"""Referent-construction existence proof for faithful entanglement.

The math/code validation showed that retrofitting an entanglement knob onto LiC-style
INDEPENDENT shards produces the *difficulty-confound* signature (informed and blinded
recoverability fall together, gap ~= 0): each shard is a piece of the problem SPECIFICATION,
independent of anything the assistant contributes, so "phrasing it relative to the assistant"
can only make it vaguer (destroy information), never relocate information into the assistant turn.

This script demonstrates the *positive* case: a construction where the user's turn conveys its
intent THROUGH an assistant-introduced referent (a selection among assistant-enumerated options,
a callback to an assistant-named entity, or a correction of assistant-produced content). Here the
content genuinely lives in the assistant turn, so dropping it from the user surface turn
*relocates* rather than destroys information. Prediction (the desired signature):

    informed_recoverability (faithfulness)  -> HIGH and ~flat across levels
    blinded_recoverability  (independence)  -> FALLS as the level rises
    entanglement_gap = informed - blinded   -> GROWS with level

Turns are TEMPLATED (mechanical), not model-generated, on purpose: the claim is about the
*construction*, so we remove any generator from the loop and let only the recoverer/matcher LLM
run. If templated pure-reference turns yield the gap, the construction is sound independent of any
particular generator (this also sidesteps the generator/recoverer self-validation threat).

Usage:
  python research/entanglement/src/referent_demo.py \
      --out research/entanglement/artifacts/referent_demo/result.json
"""

import argparse
import asyncio
import json
from pathlib import Path

# reuse the exact recoverability scoring machinery
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "recoverability", str(Path(__file__).with_name("recoverability.py"))
)
_rec = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_rec)


# Each seed: a base user request, an assistant turn that INTRODUCES a labeled referent whose
# content == the gold intent, the standalone gold intent, and four surface turns (levels 0..3)
# conveying that same intent with increasing reliance on the assistant-introduced referent.
SEEDS = [
    {
        "base": "Help me pick a sorting algorithm for my function.",
        "assistant": "Here are three options:\n(A) bubble sort — simple but O(n^2).\n(B) quicksort — fast average case, O(n log n).\n(C) merge sort — stable, O(n log n) but uses extra memory.",
        "gold": "Use quicksort for the sorting.",
        "turns": {
            0: "Use quicksort for the sorting.",
            1: "Let's go with quicksort, like you suggested.",
            2: "Use the fast O(n log n) option you listed.",
            3: "Go with option B.",
        },
    },
    {
        "base": "I need to handle the edge cases in my parser.",
        "assistant": "I see three edge cases to handle:\n1. empty input string\n2. input with only whitespace\n3. input containing non-ASCII characters",
        "gold": "Handle the case where the input is only whitespace.",
        "turns": {
            0: "Handle the case where the input is only whitespace.",
            1: "Make sure we handle the whitespace-only input case you mentioned.",
            2: "Handle that second edge case about whitespace.",
            3: "Let's handle the second one.",
        },
    },
    {
        "base": "Design the API endpoints for the app.",
        "assistant": "I'd propose:\n- GET /users (list users)\n- POST /users (create a user)\n- DELETE /users/{id} (remove a user)",
        "gold": "Add the endpoint that deletes a user by id.",
        "turns": {
            0: "Add the endpoint that deletes a user by id.",
            1: "Yes, include that delete-by-id endpoint you proposed.",
            2: "Include the delete endpoint you listed.",
            3: "Keep the last one.",
        },
    },
    {
        "base": "Here's my function that computes a total.",
        "assistant": "def total(xs):\n    s = 0\n    for x in xs:\n        s += x\n    return s",
        "gold": "Change it so it returns the average instead of the sum.",
        "turns": {
            0: "Change it so it returns the average of the numbers instead of the sum.",
            1: "Change your function so it returns the average instead of the sum.",
            2: "Have it divide that running total by the count before returning.",
            3: "Divide what you return by the length first.",
        },
    },
    {
        "base": "You wrote a regex for me to match dates.",
        "assistant": "Here's the regex: `\\d{4}-\\d{2}-\\d{2}` which matches YYYY-MM-DD.",
        "gold": "Make the regex also accept a slash as the separator, not just a dash.",
        "turns": {
            0: "Make the regex also accept a slash '/' as the separator, not just a dash.",
            1: "Update your regex to also accept a slash separator, not only the dash.",
            2: "Let that separator you used also match a slash.",
            3: "Also let that character between the groups be a slash.",
        },
    },
    {
        "base": "Pick a data structure for the cache.",
        "assistant": "Two candidates:\n(A) a plain dict — O(1) lookup, no eviction.\n(B) an OrderedDict-based LRU — O(1) lookup with least-recently-used eviction.",
        "gold": "Use the LRU structure with eviction.",
        "turns": {
            0: "Use the LRU structure that supports eviction.",
            1: "Go with the LRU option that has eviction, like you described.",
            2: "Use the one with least-recently-used eviction.",
            3: "Take option B.",
        },
    },
    {
        "base": "You listed steps for the deployment.",
        "assistant": "Deployment steps:\n1. run the test suite\n2. build the docker image\n3. push to the registry\n4. roll out to production",
        "gold": "Insert a database backup step before rolling out to production.",
        "turns": {
            0: "Insert a database backup step right before rolling out to production.",
            1: "Add a DB backup step before that production rollout step you listed.",
            2: "Add a backup step right before the last step.",
            3: "Put a backup right before step 4.",
        },
    },
    {
        "base": "Choose a loss function for the classifier.",
        "assistant": "Options:\n(A) mean squared error\n(B) cross-entropy loss\n(C) hinge loss",
        "gold": "Use cross-entropy loss.",
        "turns": {
            0: "Use cross-entropy loss.",
            1: "Let's use cross-entropy, the one you mentioned.",
            2: "Use the second option you listed.",
            3: "Go with B.",
        },
    },
    {
        "base": "You proposed column names for the table.",
        "assistant": "I'd use columns: id, created_at, updated_at, status, owner_email.",
        "gold": "Rename the owner_email column to just owner.",
        "turns": {
            0: "Rename the owner_email column to just 'owner'.",
            1: "Rename that owner_email column you proposed to just 'owner'.",
            2: "Shorten that last column name to just 'owner'.",
            3: "Drop the '_email' from the last one.",
        },
    },
    {
        "base": "You gave me a plan with a few phases.",
        "assistant": "Plan:\nPhase 1 — data collection\nPhase 2 — model training\nPhase 3 — evaluation\nPhase 4 — deployment",
        "gold": "Merge the evaluation phase into the training phase.",
        "turns": {
            0: "Merge the evaluation phase into the training phase.",
            1: "Merge that evaluation phase into the training phase you outlined.",
            2: "Fold the third phase into the second.",
            3: "Combine the third one into the one before it.",
        },
    },
    {
        "base": "You suggested two ways to parallelize.",
        "assistant": "(A) thread pool — good for I/O-bound work.\n(B) process pool — good for CPU-bound work.",
        "gold": "Use a process pool since the work is CPU-bound.",
        "turns": {
            0: "Use a process pool since the work is CPU-bound.",
            1: "Go with the process-pool option you gave for the CPU-bound work.",
            2: "Use the CPU-bound one you suggested.",
            3: "Take the second approach.",
        },
    },
    {
        "base": "You wrote a function with two helper calls.",
        "assistant": "def run(x):\n    y = normalize(x)\n    z = validate(y)\n    return z",
        "gold": "Remove the validate call and return the normalized value directly.",
        "turns": {
            0: "Remove the validate() call and return the normalized value directly.",
            1: "Drop that validate call in your function and return the normalized value.",
            2: "Cut the second helper call and return the earlier result.",
            3: "Skip the second step and return what came before it.",
        },
    },
]


async def _run():
    rows = []
    tasks = []
    meta = []
    for seed in SEEDS:
        for lvl in (0, 1, 2, 3):
            tasks.append(
                _rec._score_turn(
                    [seed["base"]],  # prior user turns
                    [seed["assistant"]],  # prior assistant turns (holds the referent)
                    seed["turns"][lvl],  # the surface user turn at this level
                    seed["gold"],  # standalone gold intent
                )
            )
            meta.append({"level": lvl, "gold": seed["gold"]})
    results = await asyncio.gather(*tasks)
    for r, m in zip(results, meta):
        r["level"] = m["level"]
        rows.append(r)

    by_level = {}
    for r in rows:
        by_level.setdefault(r["level"], []).append(r)
    agg = {}
    for lvl in sorted(by_level):
        rs = by_level[lvl]
        n = len(rs)
        inf = sum(x["informed"] for x in rs) / n
        bl = sum(x["blinded"] for x in rs) / n
        agg[str(lvl)] = {
            "n_turns": n,
            "informed_recoverability_faithfulness": round(inf, 3),
            "blinded_recoverability_independence": round(bl, 3),
            "entanglement_gap": round(inf - bl, 3),
        }
    return {"aggregate_by_level": agg, "per_turn": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = asyncio.run(_run())
    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(out, indent=2))
    print(json.dumps(out["aggregate_by_level"], indent=2))
    print(f"\nWrote {outp}")


if __name__ == "__main__":
    main()

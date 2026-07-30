#!/usr/bin/env python3
"""Judge-invariance figure on the faithfulness axis (informed recoverability).

The entanglement GAP (informed - blinded) turns out to be judge-sensitive: a lenient judge scores
vague blinded reconstructions differently, so even the math retrofit can show a small positive gap
under one judge. The clean, judge-ROBUST discriminator is *informed recoverability itself*
(faithfulness): does the intent survive at all once you are allowed to read the assistant turn?

  * Retrofit onto independent LiC shards -> informed DECAYS (0.9 -> 0.4): the knob destroys
    information, so the intent is unrecoverable even WITH the assistant. Not a faithful knob.
  * Referent construction              -> informed stays HIGH (~0.85): the knob relocates
    information into the assistant turn, so the intent is always recoverable with it. Faithful.

Both patterns hold under two independent judge families (gpt-5.4-mini and gpt-4o), which is the
point of this figure.

Usage: python research/entanglement/src/judge_invariance_figure.py
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ART = Path("research/entanglement/artifacts")


def _read(path, level):
    d = json.loads((ART / path).read_text())["aggregate_by_level"]
    return d[str(level)]["informed_recoverability_faithfulness"]


# math retrofit informed recoverability, per judge
math_g54 = {l: _read(f"recoverability/val_lvl{l}.json", l) for l in (1, 2, 3)}
math_g4o = {l: _read(f"recoverability/math_gpt4ojudge_lvl{l}.json", l) for l in (1, 2, 3)}
# referent construction informed recoverability, per judge (N=28)
ref_g54_all = json.loads((ART / "referent_demo_n28/result.json").read_text())["aggregate_by_level"]
ref_g4o_all = json.loads((ART / "referent_demo_gpt4o_judge/result.json").read_text())["aggregate_by_level"]
ref_g54 = {int(k): v["informed_recoverability_faithfulness"] for k, v in ref_g54_all.items()}
ref_g4o = {int(k): v["informed_recoverability_faithfulness"] for k, v in ref_g4o_all.items()}


def main():
    plt.figure(figsize=(7.6, 5))
    # math (red), referent (green); judge gpt-5.4-mini solid, gpt-4o dotted
    plt.plot(list(math_g54), list(math_g54.values()), "s-", color="#d1495b", lw=2.4, ms=8,
             label="Math retrofit — judge gpt-5.4-mini")
    plt.plot(list(math_g4o), list(math_g4o.values()), "s:", color="#d1495b", lw=2.0, ms=7,
             alpha=0.8, label="Math retrofit — judge gpt-4o")
    plt.plot(list(ref_g54), list(ref_g54.values()), "o-", color="#2e8540", lw=2.4, ms=8,
             label="Referent construction — judge gpt-5.4-mini")
    plt.plot(list(ref_g4o), list(ref_g4o.values()), "o:", color="#2e8540", lw=2.0, ms=7,
             alpha=0.8, label="Referent construction — judge gpt-4o")
    plt.xlabel("Entanglement level")
    plt.ylabel("Informed recoverability  (faithfulness)")
    plt.title("Faithfulness is the judge-robust discriminator\n"
              "Retrofit destroys intent (informed decays); referent construction preserves it "
              "(informed flat-high) — under both judges.")
    plt.xticks([0, 1, 2, 3], ["e0", "e1", "e2", "e3"])
    plt.ylim(-0.02, 1.05)
    plt.grid(True, alpha=0.3)
    plt.legend(loc="lower left", fontsize=8.5)
    plt.tight_layout()
    out = ART / "recoverability" / "judge_invariance_figure.png"
    plt.savefig(out, dpi=150)
    print(f"Wrote {out}")
    print("math informed  g5.4mini:", math_g54, " g4o:", math_g4o)
    print("ref  informed  g5.4mini:", ref_g54, " g4o:", ref_g4o)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Recoverability figure: informed vs blinded recoverability across entanglement levels, for the
three constructions we measured.

  (1) Math retrofit  — LiC math, independent shards            -> difficulty confound (gap ~ 0)
  (2) Code retrofit  — LiC code, independent shards            -> difficulty confound (gap ~ 0)
  (3) Referent build — intent routed via assistant referents   -> faithful entanglement (gap grows)

The signature to look for: informed (faithfulness) HIGH & flat; blinded (independence) FALLING.
Only construction (3) shows it. This is the core evidence that entanglement is a knob on TASK
STRUCTURE, and that the recoverability instrument certifies faithfulness.

Usage:
  python research/entanglement/src/recoverability_figure.py
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ART = Path("research/entanglement/artifacts")


def _load_levelfiles(prefix: str) -> dict[int, dict]:
    """Load per-level files like recoverability/{prefix}_lvl{N}.json -> {level: agg}."""
    out = {}
    for lvl in (1, 2, 3):
        f = ART / "recoverability" / f"{prefix}_lvl{lvl}.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text())["aggregate_by_level"]
        # each file holds a single key == str(lvl)
        for k, v in d.items():
            out[int(k)] = v
    return out


def _load_referent() -> dict[int, dict]:
    f = ART / "referent_demo" / "result.json"
    d = json.loads(f.read_text())["aggregate_by_level"]
    return {int(k): v for k, v in d.items()}


def _series(agg: dict[int, dict]):
    levels = sorted(agg)
    inf = [agg[l]["informed_recoverability_faithfulness"] for l in levels]
    bl = [agg[l]["blinded_recoverability_independence"] for l in levels]
    return levels, inf, bl


PANELS = [
    ("Math retrofit\n(LiC, independent shards)", _load_levelfiles("val"), "#d1495b"),
    ("Code retrofit\n(LiC, independent shards)", _load_levelfiles("code"), "#edae49"),
    ("Referent construction\n(intent via assistant referents)", _load_referent(), "#2e8540"),
]


def main():
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.4), sharey=True)
    for ax, (title, agg, color) in zip(axes, PANELS):
        levels, inf, bl = _series(agg)
        ax.plot(levels, inf, marker="o", color=color, linewidth=2.4, markersize=8,
                label="informed  (faithfulness)")
        ax.plot(levels, bl, marker="s", color=color, linewidth=2.0, markersize=7,
                linestyle="--", alpha=0.75, label="blinded  (independence)")
        # shade the entanglement gap
        ax.fill_between(levels, bl, inf, where=[i >= b for i, b in zip(inf, bl)],
                        color=color, alpha=0.12)
        for l, i, b in zip(levels, inf, bl):
            ax.annotate(f"{i - b:+.2f}", (l, (i + b) / 2), fontsize=8, ha="center",
                        va="center", color="#333")
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("entanglement level")
        ax.set_xticks(levels)
        ax.set_ylim(-0.02, 1.05)
        ax.grid(True, alpha=0.3)
        ax.legend(loc="lower left", fontsize=8)
    axes[0].set_ylabel("recoverability")
    fig.suptitle(
        "Entanglement is a knob on task STRUCTURE, not phrasing.\n"
        "Desired signature (informed flat-high, blinded falling, gap growing) appears ONLY when "
        "user intent routes through an assistant-introduced referent.",
        fontsize=11,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    out = ART / "recoverability" / "recoverability_figure.png"
    fig.savefig(out, dpi=150)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Aggregate a sweep directory (method__lvlN/metrics.json) into a matrix + figure.

Usage:
  python research/entanglement/src/aggregate.py --sweep research/entanglement/artifacts/sweep_main \
      --out research/entanglement/artifacts/sweep_main
Produces: matrix.json, matrix.csv, figure.png in --out.
"""
import argparse
import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

METHOD_LABELS = {
    "baseline": "Accumulate (S0)",
    "omit_assistant": "Drop-assistant (Huang/ERGO)",
    "summarize_v1": "Naive summarize",
    "context_edit_v2": "Decontextualize-then-edit (ours)",
}
METHOD_ORDER = ["baseline", "omit_assistant", "summarize_v1", "context_edit_v2"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--metric", default="accuracy", choices=["accuracy", "average_score"])
    args = ap.parse_args()

    sweep = Path(args.sweep)
    cells = {}  # method -> {level -> value}
    ns = {}
    for d in sorted(sweep.glob("*__lvl*")):
        m = re.match(r"(.+)__lvl(\d+)", d.name)
        if not m:
            continue
        method, lvl = m.group(1), int(m.group(2))
        mf = d / "metrics.json"
        if not mf.exists():
            continue
        data = json.loads(mf.read_text())
        cells.setdefault(method, {})[lvl] = data.get(args.metric)
        ns.setdefault(method, {})[lvl] = data.get("total_attempted")

    levels = sorted({lvl for mv in cells.values() for lvl in mv})
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # matrix.json / csv
    (out / "matrix.json").write_text(json.dumps({"metric": args.metric, "cells": cells, "n": ns}, indent=2))
    lines = ["method," + ",".join(f"e{l}" for l in levels)]
    for method in METHOD_ORDER + [m for m in cells if m not in METHOD_ORDER]:
        if method not in cells:
            continue
        row = [METHOD_LABELS.get(method, method)]
        for l in levels:
            v = cells[method].get(l)
            row.append(f"{v:.3f}" if v is not None else "")
        lines.append(",".join(row))
    (out / "matrix.csv").write_text("\n".join(lines) + "\n")

    # figure
    plt.figure(figsize=(7, 5))
    markers = {"baseline": "s", "omit_assistant": "^", "summarize_v1": "D", "context_edit_v2": "o"}
    colors = {"baseline": "#888888", "omit_assistant": "#d1495b", "summarize_v1": "#edae49", "context_edit_v2": "#2e8540"}
    for method in METHOD_ORDER + [m for m in cells if m not in METHOD_ORDER]:
        if method not in cells:
            continue
        xs = [l for l in levels if cells[method].get(l) is not None]
        ys = [cells[method][l] for l in xs]
        if not xs:
            continue
        plt.plot(xs, ys, marker=markers.get(method, "o"), color=colors.get(method),
                 linewidth=2, markersize=8, label=METHOD_LABELS.get(method, method))
    plt.xlabel("Entanglement level  (0 = independent / LiC  →  3 = relative-elliptical / corrections)")
    plt.ylabel(args.metric.replace("_", " ").title())
    plt.title("Context-management methods vs. user–assistant entanglement\n(single benchmark, task held fixed)")
    plt.xticks(levels, [f"e{l}" for l in levels])
    plt.ylim(-0.02, 1.02)
    plt.grid(True, alpha=0.3)
    plt.legend(loc="best", fontsize=9)
    plt.tight_layout()
    fig_path = out / "figure.png"
    plt.savefig(fig_path, dpi=150)
    print("Matrix:\n" + "\n".join(lines))
    print(f"\nWrote {out/'matrix.json'}, {out/'matrix.csv'}, {fig_path}")


if __name__ == "__main__":
    main()

"""Sample-by-sample comparison of Rewrite v1 vs v2.

Walks Phase 1 Rewrite (v1) outputs and the R2 Rewrite-v2 outputs and
joins on sample_id. For each task/conv, produces:

  - per-sample win/loss matrix (v1_correct, v2_correct)
  - aggregate accuracy comparison
  - count of cases v2 fixed (v1=0, v2=1) and cases v2 newly broke (v1=1, v2=0)

Output: stdout summary + `data/rewrite_v1_vs_v2.md`.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

V1_DIR = Path("/home/v-homatthew/ctx_editor/outputs/post_neurips_ac3_phase1")
V2_DIR = Path("/home/v-homatthew/ctx_editor/outputs/post_neurips_r2_rewrite_v2")
OUT_DIR = Path(__file__).resolve().parent / "data"

V1_PAT = re.compile(r"^ac3_rewrite_lic_(?P<task>[a-z_]+)_v2_conv(?P<conv>\d+)_\d+$")
V2_PAT = re.compile(r"^ac3_rewrite_v2_lic_(?P<task>[a-z_]+)_v2_conv(?P<conv>\d+)_\d+$")


def collect(d: Path, pat: re.Pattern) -> dict[tuple[str, str], dict[str, dict]]:
    out: dict[tuple[str, str], dict[str, dict]] = {}
    for sub in sorted(d.iterdir()):
        if not sub.is_dir():
            continue
        m = pat.match(sub.name)
        if not m:
            continue
        rfile = sub / "results.json"
        if not rfile.exists():
            continue
        rows = json.load(open(rfile))
        out[(m.group("task"), m.group("conv"))] = {r["sample_id"]: r for r in rows}
    return out


def main() -> None:
    v1 = collect(V1_DIR, V1_PAT)
    v2 = collect(V2_DIR, V2_PAT)

    print(f"v1 cells: {len(v1)}, v2 cells: {len(v2)}")

    # Aggregate per (task, conv)
    md_lines = ["# Rewrite v1 vs v2 — sample-by-sample comparison\n"]
    md_lines.append("| Task | Conv | n | v1 acc | v2 acc | v1→v2 fixed | v1→v2 broke | net |")
    md_lines.append("|---|---|---|---|---|---|---|---|")

    overall = defaultdict(lambda: {"n": 0, "v1c": 0, "v2c": 0, "fixed": 0, "broke": 0})
    pertask = defaultdict(lambda: {"n": 0, "v1c": 0, "v2c": 0, "fixed": 0, "broke": 0})

    for key in sorted(v1):
        if key not in v2:
            continue
        task, conv = key
        v1_rows = v1[key]
        v2_rows = v2[key]
        common = set(v1_rows) & set(v2_rows)
        v1c = sum(1 for s in common if v1_rows[s].get("is_correct"))
        v2c = sum(1 for s in common if v2_rows[s].get("is_correct"))
        fixed = sum(1 for s in common if not v1_rows[s].get("is_correct") and v2_rows[s].get("is_correct"))
        broke = sum(1 for s in common if v1_rows[s].get("is_correct") and not v2_rows[s].get("is_correct"))
        n = len(common)
        if n == 0:
            continue
        md_lines.append(
            f"| {task} | {conv} | {n} | {v1c/n*100:.1f}% | {v2c/n*100:.1f}% | "
            f"+{fixed} | -{broke} | {v2c-v1c:+d} |"
        )
        overall["all"]["n"] += n
        overall["all"]["v1c"] += v1c
        overall["all"]["v2c"] += v2c
        overall["all"]["fixed"] += fixed
        overall["all"]["broke"] += broke
        pt = pertask[task]
        pt["n"] += n; pt["v1c"] += v1c; pt["v2c"] += v2c; pt["fixed"] += fixed; pt["broke"] += broke

    md_lines.append("")
    md_lines.append("## Per-task (across conv0/1/2)\n")
    md_lines.append("| Task | n | v1 acc | v2 acc | fixed | broke | net |")
    md_lines.append("|---|---|---|---|---|---|---|")
    for task, d in sorted(pertask.items()):
        if d["n"] == 0: continue
        md_lines.append(
            f"| {task} | {d['n']} | {d['v1c']/d['n']*100:.1f}% | {d['v2c']/d['n']*100:.1f}% | "
            f"+{d['fixed']} | -{d['broke']} | {d['v2c']-d['v1c']:+d} |"
        )
    a = overall["all"]
    if a["n"]:
        md_lines.append(
            f"| **All** | {a['n']} | {a['v1c']/a['n']*100:.1f}% | {a['v2c']/a['n']*100:.1f}% | "
            f"+{a['fixed']} | -{a['broke']} | {a['v2c']-a['v1c']:+d} |"
        )

    text = "\n".join(md_lines)
    print(text)
    out_path = OUT_DIR / "rewrite_v1_vs_v2.md"
    out_path.write_text(text)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()

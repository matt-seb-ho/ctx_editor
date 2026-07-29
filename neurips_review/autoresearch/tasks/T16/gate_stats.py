#!/usr/bin/env python3
"""T16 — Re-derive the analyzer gate-open rate from trace artifacts.

Zero API calls. Walks `<run_dir>/traces/<task>/<strategy>/<sample>.json` and tallies
`trace.logs[]` entries of type `conversation_analysis`, whose `data.needs_edit` is the
gate signal (True = gate opens = analyzer asks for an edit).

Two denominators are reported, and the distinction is load-bearing:

  * INVOCATION-level (primary, correct): denominator = number of `conversation_analysis`
    log records. Samples where the analyzer never ran (conversation ended before
    `min_turns`) are EXCLUDED.
  * SAMPLE-level "legacy" (reproduces the 2026-06 reconstruction): denominator = number
    of trace files, so samples on which the analyzer never ran are silently counted as
    gate-CLOSED. This understates the gate-open rate.

Populations (both are last-turn replay, so exactly one analyzer call per sample):

  LiC       post_neurips_ac3_phase1/ — arms context_edit_v2_no_gate* (Reset; the arm the
            original 554-sample Gated-Reset reconstruction was built from),
            context_edit_v2_gated*, ac3_rewrite_lic_*, append_analysis_*
  CollabLLM post_neurips_ac3_phase3_collabllm/ — arms collabllm_ac3_reset_v8_*,
            collabllm_ac3_augment_v8_*

Usage:
    python gate_stats.py                      # full report to stdout
    python gate_stats.py --json out.json      # also dump machine-readable tallies
    python gate_stats.py --control            # run the parser positive controls
    python gate_stats.py --dump-samples 10    # print raw records for hand inspection
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# --------------------------------------------------------------------------------------
# Artifact roots. These are the recovered snapshot trees; both are outside the repo.
# --------------------------------------------------------------------------------------
LIC_ROOT = Path.home() / "ac3/recovered_t2c/ctx_editor/outputs/post_neurips_ac3_phase1"
COLLAB_ROOT = Path.home() / "ac3/t14_snapshot/ctx_editor/outputs/post_neurips_ac3_phase3_collabllm"

# run-dir name -> (benchmark, strategy label, task, cell)
LIC_PAT = re.compile(
    r"^(?P<strategy>context_edit_v2_no_gate|context_edit_v2_gated|ac3_rewrite_lic|append_analysis)"
    r"(?:_accumulate)?_(?P<task>[a-z_]+)_v2_conv(?P<cell>\d+)_\d+$"
)
COLLAB_PAT = re.compile(
    r"^collabllm_(?P<strategy>ac3_reset_v8|ac3_augment_v8)_"
    r"(?P<task>bigcodebench|math-hard)_rep(?P<cell>\d+)_\d+$"
)

# Strategy arms that the original 97.3% / 98.3% reconstruction was computed over.
LEGACY_ARMS = {"LiC": "context_edit_v2_no_gate", "CollabLLM": "ac3_reset_v8"}


def truthy(v) -> bool:
    """needs_edit is serialised as a real bool in these traces, but be defensive:
    some older dumps stringify log data."""
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in {"true", "1", "yes"}
    return bool(v)


def scan_trace(path: Path) -> dict:
    """Return per-sample record: how many analyzer calls, how many opened."""
    with open(path) as f:
        trace = json.load(f)
    logs = (trace.get("trace") or {}).get("logs") or []
    calls, opens = [], 0
    edit_decisions = 0
    n_edit_decisions = 0
    for log in logs:
        if log.get("type") == "conversation_analysis":
            data = log.get("data") or {}
            if "needs_edit" not in data:
                # analyzer record with no gate field -> cannot be scored either way
                calls.append(None)
                continue
            ne = truthy(data["needs_edit"])
            calls.append(ne)
            opens += int(ne)
        elif log.get("type") == "edit_decision":
            n_edit_decisions += 1
            if truthy((log.get("data") or {}).get("should_edit")):
                edit_decisions += 1
    scored = [c for c in calls if c is not None]
    return {
        "sample_id": trace.get("sample_id") or path.stem,
        "path": str(path),
        "n_calls": len(scored),
        "n_calls_raw": len(calls),
        "n_open": opens,
        "n_edit_decisions_true": edit_decisions,
        "n_edit_decisions": n_edit_decisions,
        "analyzer_ran": len(scored) > 0,
        # Sample-level gate verdicts. The 2026-06 reconstruction applied a per-sample rule
        # ("Reset if needs_edit=True"); on single-turn replay last == any, on multi-turn
        # CollabLLM they differ, so both are carried.
        "sample_open_last": bool(scored[-1]) if scored else False,
        "sample_open_any": any(scored),
    }


def collect(root: Path, pat: re.Pattern, benchmark: str) -> list[dict]:
    rows = []
    if not root.exists():
        print(f"WARNING: missing root {root}", file=sys.stderr)
        return rows
    for run_dir in sorted(root.iterdir()):
        if not run_dir.is_dir():
            continue
        m = pat.match(run_dir.name)
        if not m:
            continue
        traces = sorted((run_dir / "traces").glob("*/*/*.json"))
        for tp in traces:
            rec = scan_trace(tp)
            rec.update(
                benchmark=benchmark,
                strategy=m.group("strategy"),
                task=m.group("task"),
                cell=m.group("cell"),
                run_dir=run_dir.name,
            )
            rows.append(rec)
    return rows


def tally(rows: list[dict]) -> dict:
    n_samples = len(rows)
    n_ran = sum(r["analyzer_ran"] for r in rows)
    n_calls = sum(r["n_calls"] for r in rows)
    n_open = sum(r["n_open"] for r in rows)
    s_last = sum(r["sample_open_last"] for r in rows)
    s_any = sum(r["sample_open_any"] for r in rows)
    return {
        "n_samples": n_samples,
        "n_samples_analyzer_ran": n_ran,
        "n_samples_analyzer_never_ran": n_samples - n_ran,
        "n_invocations": n_calls,
        "n_open": n_open,
        # PRIMARY: turn/invocation level, analyzer-never-ran excluded
        "rate_invocation": n_open / n_calls if n_calls else None,
        # LEGACY (reproduces the 2026-06 reconstruction): per-sample verdict from the last
        # analyzer call, denominator = every trace file incl. analyzer-never-ran
        "n_samples_open_last": s_last,
        "rate_legacy_sample": s_last / n_samples if n_samples else None,
        # same per-sample verdict, but with the never-ran samples correctly excluded
        "rate_sample_corrected": s_last / n_ran if n_ran else None,
        "n_samples_open_any": s_any,
    }


def pct(x) -> str:
    return "—" if x is None else f"{100 * x:.1f}%"


def table(rows: list[dict], keys: tuple[str, ...], title: str) -> str:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        groups[tuple(r[k] for k in keys)].append(r)
    head = " | ".join(keys)
    out = [
        f"\n### {title}",
        "",
        f"| {head} | n samples | analyzer never ran | n invocations | n gate-open "
        "| **open rate (invocation)** | samples open (last call) | open rate (LEGACY sample denom) |",
        "|" + "---|" * (len(keys) + 7),
    ]
    for k in sorted(groups):
        t = tally(groups[k])
        out.append(
            "| "
            + " | ".join(k)
            + f" | {t['n_samples']} | {t['n_samples_analyzer_never_ran']} | "
            f"{t['n_invocations']} | {t['n_open']} | **{pct(t['rate_invocation'])}** | "
            f"{t['n_samples_open_last']} | {pct(t['rate_legacy_sample'])} |"
        )
    return "\n".join(out)


# --------------------------------------------------------------------------------------
# Diagnostic: is `needs_edit` actually coupled to the analyzer finding issues?
# --------------------------------------------------------------------------------------
# The analyzer sometimes prefixes its `issues` field with the prompt's own section header
# before the real content; strip it before classifying, otherwise every such record looks
# like a template echo. (Verified by hand — the numbered findings follow the header.)
ISSUES_HDR = re.compile(r'^What in the assistant.*?(?:write "None"\.|so far\.)\s*', re.S)


def classify_issues(raw: str) -> str:
    s = (raw or "").strip()
    m = ISSUES_HDR.match(s)
    if m:
        s = s[m.end():].strip()
    if not s:
        return "empty"
    if re.match(r"^(none\b|no issues|n/?a\b)", s, re.I):
        return "issues_none"
    return "issues_stated"


def issues_diagnostic(rows: list[dict], label: str) -> str:
    counts: dict[tuple[str, bool], int] = defaultdict(int)
    for r in rows:
        trace = json.load(open(r["path"]))
        for log in (trace.get("trace") or {}).get("logs", []):
            if log.get("type") != "conversation_analysis":
                continue
            d = log.get("data") or {}
            if "needs_edit" not in d:
                continue
            counts[(classify_issues(d.get("issues")), truthy(d["needs_edit"]))] += 1
    n_open = sum(v for k, v in counts.items() if k[1])
    out = [
        f"\n### Diagnostic — `needs_edit` vs the analyzer's own `issues` field ({label})",
        "",
        "| `issues` content | gate open | gate closed |",
        "|---|---|---|",
    ]
    for lab in ("issues_stated", "issues_none", "empty"):
        out.append(f"| {lab} | {counts[(lab, True)]} | {counts[(lab, False)]} |")
    if n_open:
        frac = counts[("issues_none", True)] / n_open
        out.append(
            f"\n**{counts[('issues_none', True)]} / {n_open} ({pct(frac)}) of gate-OPEN "
            "records have the analyzer explicitly writing \"None\" under `issues`.** "
            "`needs_edit` is therefore only loosely coupled to the analyzer having found a "
            "problem — read the gate-open rate as a firing rate, not as a detection rate."
        )
    return "\n".join(out)


# --------------------------------------------------------------------------------------
# Positive controls
# --------------------------------------------------------------------------------------
def positive_controls(rows: list[dict]) -> str:
    out = ["\n## Positive controls\n"]

    # C1 — independent string-level parser. Count `"needs_edit": true/false` textually,
    # bypassing the JSON walk entirely, and compare totals.
    tot_true = tot_false = 0
    pat_t = re.compile(r'"needs_edit"\s*:\s*(true|false)', re.I)
    for r in rows:
        txt = Path(r["path"]).read_text()
        for m in pat_t.finditer(txt):
            if m.group(1).lower() == "true":
                tot_true += 1
            else:
                tot_false += 1
    walked_open = sum(r["n_open"] for r in rows)
    walked_calls = sum(r["n_calls"] for r in rows)
    ok1 = (tot_true == walked_open) and (tot_true + tot_false == walked_calls)
    out.append(
        f"- **C1 independent regex parser**: raw-text scan finds {tot_true} true / "
        f"{tot_false} false = {tot_true + tot_false} `needs_edit` fields; the JSON walk "
        f"finds {walked_open} open / {walked_calls} invocations. "
        f"{'MATCH' if ok1 else 'MISMATCH'}"
    )

    # C2 — one analyzer call per sample (last-turn replay assumption).
    from collections import Counter
    out.append("- **C2 invocations per sample, by arm** (0 calls => excluded from the "
               "invocation denominator, NOT counted as gate-closed):")
    arms = sorted({(r["benchmark"], r["strategy"]) for r in rows})
    for b, s_ in arms:
        sub = [r for r in rows if r["benchmark"] == b and r["strategy"] == s_]
        c = Counter(r["n_calls"] for r in sub)
        out.append(
            f"    - {b}/{s_}: n={len(sub)}, calls-per-sample histogram "
            f"{dict(sorted(c.items()))}"
        )

    # C3 — needs_edit vs edit_decision.should_edit consistency (independent log type).
    # only arms that emit edit_decision at all (append_analysis / reset_v8 do not gate)
    gated_rows = [r for r in rows if r["n_edit_decisions"] > 0]
    disagree = [
        r for r in gated_rows if r["n_open"] != r["n_edit_decisions_true"]
    ]
    out.append(
        f"- **C3 cross-check against `edit_decision.should_edit`** (a different log record "
        f"written by a different code path), restricted to the "
        f"{len(gated_rows)} samples that emit any `edit_decision`: {len(disagree)} disagree "
        f"with `needs_edit`."
    )
    if disagree[:5]:
        for r in disagree[:5]:
            out.append(
                f"    - {r['benchmark']}/{r['strategy']}/{r['task']}/{r['sample_id']}: "
                f"needs_edit_true={r['n_open']} should_edit_true={r['n_edit_decisions_true']}"
            )
    return "\n".join(out)


def dump_samples(rows: list[dict], n: int) -> str:
    """Print the raw analyzer record for n samples, evenly spaced, for hand inspection."""
    step = max(1, len(rows) // n)
    picked = rows[::step][:n]
    out = ["\n## Hand-inspection dump\n"]
    for r in picked:
        trace = json.load(open(r["path"]))
        recs = [
            log
            for log in (trace.get("trace") or {}).get("logs", [])
            if log.get("type") in ("conversation_analysis", "edit_decision")
        ]
        out.append(
            f"\n--- {r['benchmark']} | {r['strategy']} | {r['task']} cell{r['cell']} | "
            f"{r['sample_id']}  (parser: {r['n_open']}/{r['n_calls']} open)"
        )
        for rec in recs:
            d = rec.get("data") or {}
            if rec["type"] == "conversation_analysis":
                out.append(
                    f"    conversation_analysis needs_edit={d.get('needs_edit')!r} "
                    f"aligned={str(d.get('aligned'))[:70]!r} issues={str(d.get('issues'))[:70]!r}"
                )
            else:
                out.append(f"    edit_decision should_edit={d.get('should_edit')!r}")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, help="write machine-readable tallies here")
    ap.add_argument("--control", action="store_true", help="run parser positive controls")
    ap.add_argument("--dump-samples", type=int, default=0, help="print N raw records")
    args = ap.parse_args()

    lic = collect(LIC_ROOT, LIC_PAT, "LiC")
    collab = collect(COLLAB_ROOT, COLLAB_PAT, "CollabLLM")
    allrows = lic + collab

    print("# T16 — analyzer gate-open rate, re-derived from traces\n")
    print(f"LiC root:       {LIC_ROOT}")
    print(f"CollabLLM root: {COLLAB_ROOT}")

    report = {}
    for bench, rows in (("LiC", lic), ("CollabLLM", collab)):
        legacy = [r for r in rows if r["strategy"] == LEGACY_ARMS[bench]]
        print(f"\n## {bench}")
        print(
            f"\n**Headline arm** (`{LEGACY_ARMS[bench]}`, the arm the original "
            f"reconstruction was built from):"
        )
        t = tally(legacy)
        print(
            f"\n- gate-open, **invocation (turn) denominator**: {t['n_open']}/{t['n_invocations']}"
            f" = **{pct(t['rate_invocation'])}**"
        )
        print(
            f"- gate-open, **per-sample verdict, corrected denominator**: "
            f"{t['n_samples_open_last']}/{t['n_samples_analyzer_ran']}"
            f" = **{pct(t['rate_sample_corrected'])}**"
        )
        print(
            f"- gate-open, LEGACY per-sample verdict / all-traces denominator: "
            f"{t['n_samples_open_last']}/{t['n_samples']}"
            f" = {pct(t['rate_legacy_sample'])}"
            f"  ({t['n_samples_analyzer_never_ran']} samples the analyzer never ran on, "
            "silently scored as gate-closed)"
        )
        print(table(legacy, ("task",), f"{bench} — {LEGACY_ARMS[bench]} by task"))
        print(table(legacy, ("task", "cell"), f"{bench} — {LEGACY_ARMS[bench]} by task x cell"))
        print(table(rows, ("strategy",), f"{bench} — all analyzer-bearing strategies"))
        print(table(rows, ("strategy", "task"), f"{bench} — strategy x task"))
        report[bench] = {
            "headline_arm": LEGACY_ARMS[bench],
            "headline": t,
            "by_strategy": {
                s: tally([r for r in rows if r["strategy"] == s])
                for s in sorted({r["strategy"] for r in rows})
            },
            "by_strategy_task": {
                f"{s}/{tk}": tally(
                    [r for r in rows if r["strategy"] == s and r["task"] == tk]
                )
                for s in sorted({r["strategy"] for r in rows})
                for tk in sorted({r["task"] for r in rows if r["strategy"] == s})
            },
        }

    if args.control:
        print(positive_controls(allrows))
    if args.dump_samples:
        print(dump_samples(allrows, args.dump_samples))
    if args.json:
        args.json.write_text(json.dumps(report, indent=2))
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()

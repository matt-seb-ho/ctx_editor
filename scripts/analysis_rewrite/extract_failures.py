"""Extract Rewrite failure cases for hierarchical LLM analysis.

For Phase 1 DeepSeek-V4-Flash outputs, walk all conv prefixes per task and
identify samples where:

  - Rewrite scored 0 but Baseline (or Reset) scored 1 (regression cases), OR
  - Rewrite scored 0 across all 3 conv prefixes (consistent failure)

Emit a JSONL with one row per (sample_id, task, prefix) and the actual
compacted-context content + final assistant answer + ground-truth answer
(when available), so a downstream LLM categorizer can read each case
in isolation.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

PHASE_DIR = Path("/home/v-homatthew/ctx_editor/outputs/post_neurips_ac3_phase1")
OUT_DIR = Path(__file__).resolve().parent / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

STRATEGY_PATTERNS = {
    "baseline": re.compile(r"^baseline_(?P<task>[a-z_]+)_v2_conv(?P<conv>\d+)_\d+$"),
    "rewrite": re.compile(r"^ac3_rewrite_lic_(?P<task>[a-z_]+)_v2_conv(?P<conv>\d+)_\d+$"),
    "reset": re.compile(r"^context_edit_v2_no_gate(?:_accumulate)?_(?P<task>[a-z_]+)_v2_conv(?P<conv>\d+)_\d+$"),
    "ao": re.compile(r"^omit_assistant_(?P<task>[a-z_]+)_v2_conv(?P<conv>\d+)_\d+$"),
    "augment": re.compile(r"^append_analysis_(?P<task>[a-z_]+)_v2_conv(?P<conv>\d+)_\d+$"),
}


def collect_cells() -> dict:
    cells: dict[tuple[str, str, str], Path] = {}
    for d in sorted(PHASE_DIR.iterdir()):
        if not d.is_dir():
            continue
        for strat, pat in STRATEGY_PATTERNS.items():
            m = pat.match(d.name)
            if m:
                key = (strat, m.group("task"), m.group("conv"))
                cells[key] = d
                break
    return cells


def load_results(cell_dir: Path) -> dict[str, dict]:
    rfile = cell_dir / "results.json"
    if not rfile.exists():
        return {}
    rows = json.load(open(rfile))
    return {r["sample_id"]: r for r in rows}


def load_trace(cell_dir: Path, task: str, strategy_subdir: str, sample_id: str) -> dict | None:
    # Trace filenames use '_' in place of '/' or other separators that appear in sample_ids.
    for candidate in (sample_id, sample_id.replace("/", "_")):
        p = cell_dir / "traces" / task / strategy_subdir / f"{candidate}.json"
        if p.exists():
            return json.load(open(p))
    return None


def extract_compacted(trace: dict) -> dict[str, Any]:
    """Pull out the compacted context text + analysis logs, if any."""
    out: dict[str, Any] = {"compacted_messages": [], "analysis_logs": [], "num_resets": trace.get("trace", {}).get("num_resets", 0)}
    if "trace" not in trace:
        return out
    t = trace["trace"]
    for m in t.get("messages", []) or []:
        if m.get("role") == "compacted conversation":
            out["compacted_messages"].append(m.get("content", ""))
    for log in t.get("logs", []) or []:
        if log.get("type") in ("compaction_analysis", "context_compaction"):
            out["analysis_logs"].append(log)
    return out


def get_assistant_final(trace: dict) -> str:
    if "trace" not in trace:
        return ""
    msgs = trace["trace"].get("messages", []) or []
    for m in reversed(msgs):
        if m.get("role") == "assistant":
            return m.get("content", "")
    return ""


def get_gold_answer(trace: dict) -> str:
    # LiC traces sometimes have gold under metadata in the trace; fall back to nothing
    md = trace.get("metadata") or {}
    if isinstance(md, dict):
        for k in ("gold", "gold_answer", "reference", "expected_answer"):
            if k in md:
                return str(md[k])
    return ""


def main() -> None:
    cells = collect_cells()
    by_strat: dict[str, list[tuple[str, str, Path]]] = defaultdict(list)
    for (strat, task, conv), d in cells.items():
        by_strat[strat].append((task, conv, d))

    # Index results per (strat, task, conv, sample_id) -> row
    results: dict[tuple[str, str, str], dict[str, dict]] = {}
    for (strat, task, conv), d in cells.items():
        results[(strat, task, conv)] = load_results(d)

    failures: list[dict] = []
    for (strat, task, conv) in cells:
        if strat != "rewrite":
            continue
        rw_rows = results.get(("rewrite", task, conv), {})
        bl_rows = results.get(("baseline", task, conv), {})
        rs_rows = results.get(("reset", task, conv), {})
        ao_rows = results.get(("ao", task, conv), {})

        for sid, rw_row in rw_rows.items():
            if rw_row.get("is_correct"):
                continue
            bl = bl_rows.get(sid, {})
            rs = rs_rows.get(sid, {})
            ao = ao_rows.get(sid, {})
            regression_vs_baseline = bool(bl.get("is_correct")) and not rw_row.get("is_correct")
            regression_vs_reset = bool(rs.get("is_correct")) and not rw_row.get("is_correct")
            regression_vs_ao = bool(ao.get("is_correct")) and not rw_row.get("is_correct")
            if not (regression_vs_baseline or regression_vs_reset or regression_vs_ao):
                continue
            trace = load_trace(cells[("rewrite", task, conv)], task, "ac3_rewrite_lic", sid)
            if trace is None:
                continue
            comp = extract_compacted(trace)
            final = get_assistant_final(trace)
            # Pull a snippet of the system message + last user message for context
            sys_msg = ""
            last_user = ""
            for m in (trace.get("trace") or {}).get("messages", []) or []:
                if m.get("role") == "system" and not sys_msg:
                    sys_msg = m.get("content", "")
                if m.get("role") == "user":
                    last_user = m.get("content", "")

            failures.append({
                "sample_id": sid,
                "task": task,
                "conv": conv,
                "rewrite_score": rw_row.get("score"),
                "rewrite_extracted_answer": rw_row.get("extracted_answer"),
                "baseline_score": bl.get("score"),
                "baseline_extracted_answer": bl.get("extracted_answer"),
                "reset_score": rs.get("score"),
                "reset_extracted_answer": rs.get("extracted_answer"),
                "ao_score": ao.get("score"),
                "regression_vs_baseline": regression_vs_baseline,
                "regression_vs_reset": regression_vs_reset,
                "regression_vs_ao": regression_vs_ao,
                "system_prompt": sys_msg[:4000],  # truncate to keep file manageable
                "last_user_message": last_user[:1500],
                "compacted_context": "\n\n---\n\n".join(comp["compacted_messages"]),
                "analysis_logs": comp["analysis_logs"],
                "assistant_final_response": final[:4000],
            })

    out = OUT_DIR / "rewrite_failures.jsonl"
    with out.open("w") as f:
        for row in failures:
            f.write(json.dumps(row) + "\n")
    print(f"Wrote {len(failures)} failure rows to {out}")

    # Quick summary by task + regression type
    by_task: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in failures:
        t = row["task"]
        by_task[t]["total"] += 1
        if row["regression_vs_baseline"]:
            by_task[t]["regression_vs_baseline"] += 1
        if row["regression_vs_reset"]:
            by_task[t]["regression_vs_reset"] += 1
        if row["regression_vs_ao"]:
            by_task[t]["regression_vs_ao"] += 1

    print("\nFailure breakdown by task:")
    for t, counts in sorted(by_task.items()):
        print(f"  {t}: {dict(counts)}")


if __name__ == "__main__":
    main()

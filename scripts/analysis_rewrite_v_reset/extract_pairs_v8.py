"""R6-era variant of extract_pairs.py: pair v8 Rewrite (R6 A2) failures
against Reset successes on the same (task, conv, sample).

Reads:
  outputs/post_may18_r6_a_stage/ac3_rewrite_v8_lic_*_v2_conv*_*/ — v8 Rewrite
  outputs/post_neurips_ac3_phase1/context_edit_v2_no_gate*_v2_conv*_*/ — Reset

Output: scripts/analysis_rewrite_v_reset/data/pairs_v8.jsonl

The v8 prompt is open-ended (no <task_spec>/<work_so_far> tags); the rewriter
emits <new_context>...</new_context> and only that body reaches the assistant.
The downstream diagnose worker only reads the compacted-context blob, so the
format change is transparent to it.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path("/home/v-homatthew/ctx_editor")
REWRITE_ROOT = PROJECT_ROOT / "outputs" / "post_may18_r6_a_stage"
RESET_ROOT = PROJECT_ROOT / "outputs" / "post_neurips_ac3_phase1"
OUT_DIR = Path(__file__).resolve().parent / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

REWRITE_PAT = re.compile(r"^ac3_rewrite_v8_lic_(?P<task>[a-z_]+)_v2_conv(?P<conv>\d+)_\d+$")
RESET_PAT = re.compile(r"^context_edit_v2_no_gate(?:_accumulate)?_(?P<task>[a-z_]+)_v2_conv(?P<conv>\d+)_\d+$")


def collect(root: Path, pat: re.Pattern) -> dict[tuple[str, str], Path]:
    out: dict[tuple[str, str], Path] = {}
    if not root.exists():
        return out
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        m = pat.match(d.name)
        if m:
            out[(m.group("task"), m.group("conv"))] = d
    return out


def load_trace(cell_dir: Path, task: str, strategy_subdir: str, sample_id: str) -> dict | None:
    for candidate in (sample_id, sample_id.replace("/", "_")):
        p = cell_dir / "traces" / task / strategy_subdir / f"{candidate}.json"
        if p.exists():
            return json.load(open(p))
    return None


def extract_view(trace: dict) -> dict:
    """Pull the relevant slices from a trace; format-agnostic to v1/v8 rewriter."""
    msgs = (trace.get("trace") or {}).get("messages", []) or []
    logs = (trace.get("trace") or {}).get("logs", []) or []
    system = ""
    compacted = ""
    last_user = ""
    final_assistant = ""
    pre_compaction_user_turns: list[str] = []
    pre_compaction_assistant_turns: list[str] = []
    saw_compacted = False
    for m in msgs:
        role = m.get("role", "")
        c = m.get("content", "") or ""
        if role == "system" and not system:
            system = c
        elif role == "compacted conversation":
            compacted = c
            saw_compacted = True
        elif role == "user":
            last_user = c
            if not saw_compacted:
                pre_compaction_user_turns.append(c)
        elif role == "assistant":
            if not saw_compacted:
                pre_compaction_assistant_turns.append(c)
    for m in reversed(msgs):
        if m.get("role") == "assistant":
            final_assistant = m.get("content", "") or ""
            break

    # Analyzer outputs (v8 path uses ConversationAnalyzer; legacy "compaction_analysis"
    # log type may also be present in older traces).
    analysis_log = None
    compaction_log = None
    for log in logs:
        t = log.get("type", "")
        if t == "context_compaction":
            compaction_log = log.get("data", {})
        elif t in ("analyzer_output", "compaction_analysis") and analysis_log is None:
            analysis_log = log.get("data", {})
    return {
        "system": system,
        "compacted": compacted,
        "last_user": last_user,
        "final_assistant": final_assistant,
        "pre_user_turns": pre_compaction_user_turns,
        "pre_assistant_turns": pre_compaction_assistant_turns,
        "analysis_log": analysis_log,
        "compaction_log": compaction_log,
    }


def main() -> None:
    rw_cells = collect(REWRITE_ROOT, REWRITE_PAT)
    rs_cells = collect(RESET_ROOT, RESET_PAT)
    print(f"v8 Rewrite cells: {len(rw_cells)}; Reset cells: {len(rs_cells)}")

    pairs: list[dict] = []
    for key in sorted(rw_cells):
        if key not in rs_cells:
            continue
        rw_dir = rw_cells[key]
        rs_dir = rs_cells[key]
        task, conv = key

        try:
            rw_results = {r["sample_id"]: r for r in json.load(open(rw_dir / "results.json"))}
        except FileNotFoundError:
            continue
        try:
            rs_results = {r["sample_id"]: r for r in json.load(open(rs_dir / "results.json"))}
        except FileNotFoundError:
            continue

        rw_strat = "ac3_rewrite_v8_lic"
        # Reset cell name might be context_edit_v2_no_gate or no_gate_accumulate
        rs_strat = rs_dir.name.split(f"_{task}_v2_")[0]
        rs_strat_dir = rs_dir / "traces" / task
        if rs_strat_dir.exists():
            subs = [p.name for p in rs_strat_dir.iterdir() if p.is_dir()]
            if subs:
                rs_strat = subs[0]

        for sid in sorted(set(rw_results) & set(rs_results)):
            rw_r = rw_results[sid]
            rs_r = rs_results[sid]
            if not (rs_r.get("is_correct") and not rw_r.get("is_correct")):
                continue
            # Skip cells where Rewrite ran into an error (no completion at all)
            if rw_r.get("num_turns", 0) == 0:
                continue
            rw_trace = load_trace(rw_dir, task, rw_strat, sid)
            rs_trace = load_trace(rs_dir, task, rs_strat, sid)
            if rw_trace is None or rs_trace is None:
                continue

            rw_v = extract_view(rw_trace)
            rs_v = extract_view(rs_trace)

            pairs.append({
                "sample_id": sid,
                "task": task,
                "conv": conv,
                "system_prompt": rw_v["system"][:2500],
                "last_user_message": rw_v["last_user"][:1500],
                "pre_user_turns": [t[:600] for t in rw_v["pre_user_turns"][:6]],
                "pre_assistant_turns": [t[:1200] for t in rw_v["pre_assistant_turns"][:6]],
                "rewrite_compacted": rw_v["compacted"][:4000],
                "reset_compacted": rs_v["compacted"][:4000],
                "rewrite_final_answer": rw_v["final_assistant"][:3000],
                "reset_final_answer": rs_v["final_assistant"][:3000],
                "rewrite_extracted_answer": rw_r.get("extracted_answer"),
                "reset_extracted_answer": rs_r.get("extracted_answer"),
                "rewrite_analysis_log": rw_v["analysis_log"],
                "rewrite_compaction_log": rw_v["compaction_log"],
            })

    out_path = OUT_DIR / "pairs_v8.jsonl"
    with out_path.open("w") as f:
        for p in pairs:
            f.write(json.dumps(p) + "\n")

    by_task = defaultdict(int)
    for p in pairs:
        by_task[p["task"]] += 1
    print(f"Wrote {len(pairs)} v8 pairs to {out_path}")
    print(f"Breakdown by task: {dict(by_task)}")


if __name__ == "__main__":
    main()

"""Extract paired (Reset, Rewrite) contexts + final answers for
samples where Reset succeeded and Rewrite failed.

Walks Phase 1 outputs (post_neurips_ac3_phase1) and pulls trace
files for both strategies on the same sample. Emits one JSON per
pair containing everything a downstream DeepSeek-V4-Flash worker
needs to diagnose the rewrite failure.

Output: scripts/analysis_rewrite_v_reset/data/pairs.jsonl
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

PHASE_DIR = Path("/home/v-homatthew/ctx_editor/outputs/post_neurips_ac3_phase1")
OUT_DIR = Path(__file__).resolve().parent / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

REWRITE_PAT = re.compile(r"^ac3_rewrite_lic_(?P<task>[a-z_]+)_v2_conv(?P<conv>\d+)_\d+$")
RESET_PAT = re.compile(r"^context_edit_v2_no_gate(?:_accumulate)?_(?P<task>[a-z_]+)_v2_conv(?P<conv>\d+)_\d+$")


def collect(pat: re.Pattern) -> dict[tuple[str, str], Path]:
    out: dict[tuple[str, str], Path] = {}
    for d in sorted(PHASE_DIR.iterdir()):
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
    """Pull the relevant slices from a trace."""
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

    # Analyzer outputs (for rewrite, this captures the FIRST query: analysis)
    analysis_log = None
    compaction_log = None
    for log in logs:
        t = log.get("type", "")
        if t == "compaction_analysis":
            analysis_log = log.get("data", {})
        elif t == "context_compaction":
            compaction_log = log.get("data", {})
        elif t == "analyzer_output" and analysis_log is None:
            # Reset / Augment use ConversationAnalyzer instead. Different log type.
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
    rw_cells = collect(REWRITE_PAT)
    rs_cells = collect(RESET_PAT)

    pairs: list[dict] = []
    for key in sorted(rw_cells):
        if key not in rs_cells:
            continue
        rw_dir = rw_cells[key]
        rs_dir = rs_cells[key]
        task, conv = key

        rw_results = {r["sample_id"]: r for r in json.load(open(rw_dir / "results.json"))}
        rs_results = {r["sample_id"]: r for r in json.load(open(rs_dir / "results.json"))}

        # Strategy subdir under traces/{task}/
        rw_strat = "ac3_rewrite_lic"
        # Reset cell name might be context_edit_v2_no_gate or no_gate_accumulate
        rs_strat = rs_dir.name.split(f"_{task}_v2_")[0]
        # Actions stored under "context_edit_v2_no_gate_accumulate" — check filesystem
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

    out_path = OUT_DIR / "pairs.jsonl"
    with out_path.open("w") as f:
        for p in pairs:
            f.write(json.dumps(p) + "\n")

    by_task = defaultdict(int)
    for p in pairs:
        by_task[p["task"]] += 1
    print(f"Wrote {len(pairs)} pairs to {out_path}")
    print(f"Breakdown by task: {dict(by_task)}")


if __name__ == "__main__":
    main()

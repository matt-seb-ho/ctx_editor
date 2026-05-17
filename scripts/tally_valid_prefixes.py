"""Tally valid prefixes per (model, task, problem) from the vanilla matrix.

For each ctx-editor run dir we have:
  - run_summary.json            (which model + task + experiment_name)
  - traces/{sample_id}.json     (the saved sharded conversation)
  - false_negatives.json        (only contains entries for INCORRECT samples)

For replay-as-prefix purposes a "valid prefix" is a saved conversation that is
either:
  (a) correct (assistant got it right; nothing to intervene on), OR
  (b) incorrect AND user_sim_sufficient (a legit true-negative — the user
      revealed enough info, so testing AC3 on it is fair).

A run is *invalid as a prefix* if it is incorrect AND user_sim_sufficient is
false (user-sim never gave enough info). Those would propagate the
user-simulator's failure into the intervention experiments.

This script walks every (model, task, run) cell we have, joins traces with the
false_negatives.json verdict, and emits:

  - per-(model, task) counts: how many problems have 0 / 1 / 2 / ≥3 valid
    prefixes available right now;
  - the precise list of (model, task, problem) cells that need more prefixes.

Output goes to docs/reports/post_neurips_lic_vanilla.md as an appendix table,
and to a JSON sidecar that the next-run launcher can consume.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MAIN_OUT_DIRS = [
    PROJECT_ROOT / "outputs" / "2026-05-16",                # main matrix
    PROJECT_ROOT / "outputs" / "post_neurips_lic_vanilla_redo",
    PROJECT_ROOT / "outputs" / "post_neurips_lic_vanilla_fillin",
]

MODEL_LABELS = {
    "gpt-5.4": "gpt5_4",
    "deepseek-v4-flash-foundry": "deepseek_v4_flash_foundry",
    "kimi-k2.6-foundry": "kimi_k2_6_foundry",
    "gpt-5.5-foundry": "gpt5_5_foundry",
}


def is_collision_overwritten(rs_path: Path, expected_model_in_name: str) -> bool:
    """Detect the math-run-1 collision: run_summary's experiment_name names a
    different model than the directory we think we're in."""
    if not rs_path.exists():
        return False
    try:
        rs = json.loads(rs_path.read_text())
    except Exception:
        return True
    exp = rs.get("experiment_name", "")
    return expected_model_in_name not in exp


def discover_cells():
    """Yield dicts describing each (model, task, run) cell with paths."""
    for root in MAIN_OUT_DIRS:
        if not root.exists():
            continue
        for run_dir in sorted(root.rglob("run_summary.json")):
            d = run_dir.parent
            try:
                rs = json.loads(run_dir.read_text())
            except Exception:
                continue
            exp = rs.get("experiment_name", "")
            # Pull (model_key, task_key, run_label) from experiment_name like
            # baseline_sharded_<model>_<task>_run<i>  or  ..._redo<i>
            m = re.match(
                r"^baseline_sharded_(?P<model>.+?)_(?P<task>math|code|database|actions)_v2_(?P<kind>run|redo|fillin)(?P<idx>\d+)(?:_(?P<ts>\d+))?$",
                exp,
            )
            if not m:
                continue
            # Include the timestamp suffix in the label so multiple invocations
            # with the same kind+idx (e.g. two "fillin1" passes at different times)
            # don't collide in the (model, task, label) dedup map.
            ts = m.group("ts")
            label_parts = [m.group("kind") + m.group("idx")]
            if ts:
                label_parts.append(ts)
            yield {
                "out_dir": d,
                "rs": rs,
                "model_key": m.group("model"),
                "task_key": m.group("task") + "_v2",
                "label": "_".join(label_parts),
            }


def load_fn(out_dir: Path) -> dict:
    p = out_dir / "false_negatives.json"
    if not p.exists():
        return {"results": []}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {"results": []}


def list_trace_ids(out_dir: Path) -> set[str]:
    traces_dir = out_dir / "traces"
    if not traces_dir.exists():
        return set()
    # safe_id mapping: '/' replaced with '_'. We invert with split below.
    return {p.stem for p in traces_dir.glob("*.json")}


def per_problem_status(cell: dict, results_by_id: dict[str, dict]):
    """For each problem in this cell, classify the prefix as valid/invalid."""
    out_dir = cell["out_dir"]
    fn = load_fn(out_dir)
    # FN map: sample_id -> {"user_sim_sufficient": bool, "is_answer_attempt": bool}
    fn_map = {r["sample_id"]: r for r in fn.get("results", [])}

    # All sample_ids in this cell. Use run_summary if present; otherwise list traces.
    # results.json (per-sample) is the most reliable source.
    results_path = out_dir / "results.json"
    samples = []
    if results_path.exists():
        try:
            samples = json.loads(results_path.read_text())
        except Exception:
            samples = []
    if not samples:
        for tid in list_trace_ids(out_dir):
            sid = tid.replace("_", "/", 1)
            samples.append({"sample_id": sid, "is_correct": None, "score": None})

    for s in samples:
        sid = s.get("sample_id", "?")
        verdict = "unknown"
        if s.get("is_correct"):
            verdict = "correct_valid"
        else:
            fn_entry = fn_map.get(sid)
            if fn_entry is None:
                # Either no FN analysis ran for this sample, or it was correct.
                # Treat as valid-as-prefix only if explicitly correct above.
                # If is_correct is None we don't know; mark as 'unknown'.
                verdict = "unknown"
            else:
                if fn_entry.get("user_sim_sufficient", True):
                    verdict = "incorrect_valid"
                else:
                    verdict = "incorrect_invalid_usersim"
        results_by_id.setdefault((cell["model_key"], cell["task_key"], sid), []).append({
            "label": cell["label"],
            "verdict": verdict,
            "out_dir": str(out_dir.relative_to(PROJECT_ROOT)),
        })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", default=str(PROJECT_ROOT / "outputs/post_neurips_lic_vanilla/valid_prefix_tally.json"))
    args = parser.parse_args()

    cells = list(discover_cells())
    print(f"Discovered {len(cells)} cells.")

    # Filter to last-write-wins per (model, task, label)
    # (the collision case): for math run1 we may have several "run1" cells; only
    # keep the one whose run_summary actually names that model.
    keep = {}
    for c in cells:
        # The "model" field in run_summary may differ from filename if
        # there was a write race. Trust the experiment_name in run_summary,
        # which is set by the launcher with the intended model.
        # discover_cells already pulls model_key from experiment_name, so it's fine.
        key = (c["model_key"], c["task_key"], c["label"])
        # If duplicate, prefer the one whose run_summary.model matches model_key
        if key in keep:
            existing = keep[key]
            existing_match = MODEL_LABELS.get(existing["rs"].get("model", ""), "") == c["model_key"]
            cand_match = MODEL_LABELS.get(c["rs"].get("model", ""), "") == c["model_key"]
            if cand_match and not existing_match:
                keep[key] = c
        else:
            keep[key] = c

    cells = list(keep.values())
    print(f"After dedup by (model, task, label): {len(cells)} cells.")

    by_problem: dict = {}
    for c in cells:
        per_problem_status(c, by_problem)

    # Aggregate per (model, task)
    per_mt = defaultdict(lambda: {
        "problems_total": 0,
        "valid_count_distribution": Counter(),
        "needs_more": [],
    })

    for (model, task, sid), runs in by_problem.items():
        n_valid = sum(1 for r in runs if r["verdict"] in ("correct_valid", "incorrect_valid"))
        mt = per_mt[(model, task)]
        mt["problems_total"] += 1
        mt["valid_count_distribution"][n_valid] += 1
        if n_valid < 3:
            mt["needs_more"].append({"sample_id": sid, "valid_now": n_valid,
                                       "runs": runs})

    # Print summary
    print("\n=== Per (model, task) prefix-validity summary ===")
    header = f"{'model':30s} {'task':12s} {'problems':10s} {'≥3 valid':10s} {'2 valid':10s} {'1':6s} {'0':6s} {'needs_more':12s}"
    print(header)
    print("-" * len(header))
    for (m, t), v in sorted(per_mt.items()):
        d = v["valid_count_distribution"]
        ge3 = sum(c for k, c in d.items() if k >= 3)
        print(f"{m:30s} {t:12s} {v['problems_total']:<10d} {ge3:<10d} {d.get(2,0):<10d} {d.get(1,0):<6d} {d.get(0,0):<6d} {len(v['needs_more']):<12d}")

    # Write JSON sidecar (paths-only — readable but compact)
    sidecar = {
        "generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "cells_scanned": len(cells),
        "per_model_task": {
            f"{m}__{t}": {
                "problems_total": v["problems_total"],
                "ge3_valid": sum(c for k, c in v["valid_count_distribution"].items() if k >= 3),
                "valid_count_distribution": {str(k): c for k, c in sorted(v["valid_count_distribution"].items())},
                "needs_more": v["needs_more"],
            }
            for (m, t), v in per_mt.items()
        },
    }
    out_path = Path(args.json_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(sidecar, indent=2))
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()

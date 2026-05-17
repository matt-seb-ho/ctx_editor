"""Curate the final valid-prefix pool from the vanilla matrix + fill-in runs.

For each (model, task, problem) we have up to N runs across the main matrix,
the redo round, and the fill-in passes. Each run's trace file lives under
its run dir's traces/ tree. This script:

  1. Walks every run dir, joins traces with the per-run false_negatives.json.
  2. For each (model, task, problem), collects up to 3 VALID prefix trace
     paths (a prefix is valid iff the run was correct, OR was incorrect but
     the FN analyzer judged the user-sim sufficient).
  3. Copies the chosen trace files into a canonical replay layout:

        data/valid_prefixes_htn50_52/
            {model}/
                {task}/
                    conv0/{sample_id}.json
                    conv1/{sample_id}.json
                    conv2/{sample_id}.json
                    false_negatives.json   # empty-summary stub
                    conv_manifest.json     # which run dir each prefix came from

  4. Writes a coverage report at
        outputs/post_neurips_lic_vanilla/prefix_pool_coverage.json
     listing per-cell which problems have <3 valid prefixes and why.

Selection policy (when more than 3 valid prefixes exist):
  - prefer 'correct' prefixes over 'incorrect-but-valid', so that AC3 has
    something to improve from. Specifically take the first 3 from the union
    in this order: incorrect-but-valid first (these are the cases AC3 is
    targeting), then correct. Rationale: if all 3 are correct prefixes,
    AC3 has nothing to fix and the cell contributes 0pp signal. We want
    the prefix pool weighted toward failures the interventions can help.

Run order policy:
  - Within each preference bucket, take the earliest run (by run dir
    timestamp) first, for reproducibility.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEARCH_ROOTS = [
    PROJECT_ROOT / "outputs" / "2026-05-16",
    PROJECT_ROOT / "outputs" / "post_neurips_lic_vanilla_redo",
    PROJECT_ROOT / "outputs" / "post_neurips_lic_vanilla_fillin",
]
POOL_ROOT = PROJECT_ROOT / "data" / "valid_prefixes_htn50_52"
COVERAGE_OUT = PROJECT_ROOT / "outputs" / "post_neurips_lic_vanilla" / "prefix_pool_coverage.json"

MODEL_NAME_TO_KEY = {
    "gpt-5.4": "gpt5_4",
    "deepseek-v4-flash-foundry": "deepseek_v4_flash_foundry",
    "kimi-k2.6-foundry": "kimi_k2_6_foundry",
    "gpt-5.5-foundry": "gpt5_5_foundry",
}

EXP_RE = re.compile(
    r"^baseline_sharded_(?P<model>.+?)_(?P<task>math|code|database|actions)_v2"
    r"_(?P<kind>run|redo|fillin)(?P<idx>\d+)(?:_(?P<ts>\d+))?$"
)


def discover_runs():
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for rs_path in root.rglob("run_summary.json"):
            d = rs_path.parent
            try:
                rs = json.loads(rs_path.read_text())
            except Exception:
                continue
            exp = rs.get("experiment_name", "")
            m = EXP_RE.match(exp)
            if not m:
                continue
            yield {
                "out_dir": d,
                "rs": rs,
                "model_key": m.group("model"),
                "task_cfg": m.group("task") + "_v2",
                "kind": m.group("kind"),
                "idx": int(m.group("idx")),
                "ts": int(m.group("ts")) if m.group("ts") else 0,
            }


def load_results(out_dir: Path) -> list[dict]:
    p = out_dir / "results.json"
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text())
    except Exception:
        return []


def load_fn(out_dir: Path) -> dict[str, dict]:
    p = out_dir / "false_negatives.json"
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text())
    except Exception:
        return {}
    return {r["sample_id"]: r for r in data.get("results", [])}


def find_trace(out_dir: Path, sample_id: str) -> Path | None:
    """Locate the trace JSON for a sample inside out_dir/traces/."""
    safe_id = sample_id.replace("/", "_").replace("\\", "_")
    traces_dir = out_dir / "traces"
    if not traces_dir.exists():
        return None
    # The exact filename is {safe_id}.json, but inside an experiment-name subdir.
    hits = list(traces_dir.rglob(f"{safe_id}.json"))
    if not hits:
        return None
    return hits[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Plan only; do not write files.")
    args = parser.parse_args()

    runs = list(discover_runs())
    # Group by (model, task) and within each (problem) keep candidates ordered
    # by (preference bucket, timestamp).
    candidates: dict = defaultdict(lambda: defaultdict(list))  # (model, task) -> sample_id -> [cand]
    for run in runs:
        if run["kind"] == "redo" and run["model_key"] not in {"gpt5_4", "deepseek_v4_flash_foundry", "gpt5_5_foundry"}:
            # redo runs only target code_v2 for 3 specific models; defensive
            pass
        results = load_results(run["out_dir"])
        fn = load_fn(run["out_dir"])
        for r in results:
            sid = r.get("sample_id", "?")
            is_correct = bool(r.get("is_correct"))
            verdict_bucket = None
            if is_correct:
                verdict_bucket = "correct"
            else:
                fn_entry = fn.get(sid)
                if fn_entry is None:
                    # No FN analysis or this sample errored: skip — we can't
                    # guarantee a clean prefix from this run.
                    continue
                if fn_entry.get("user_sim_sufficient", True):
                    verdict_bucket = "incorrect_valid"
                else:
                    continue  # invalid as prefix
            tp = find_trace(run["out_dir"], sid)
            if tp is None:
                continue
            candidates[(run["model_key"], run["task_cfg"])][sid].append({
                "bucket": verdict_bucket,
                "ts": run["ts"] or int(run["out_dir"].stat().st_mtime),
                "out_dir": str(run["out_dir"].relative_to(PROJECT_ROOT)),
                "trace_path": str(tp),
                "is_correct": is_correct,
            })

    coverage = {}
    for (model_key, task_cfg), sample_candidates in candidates.items():
        cell_dir_root = POOL_ROOT / model_key / task_cfg
        per_problem = {}
        for sid, cands in sample_candidates.items():
            # Sort: incorrect_valid first (these are the AC3 targets), then correct.
            # Within bucket, oldest first.
            cands.sort(key=lambda c: (0 if c["bucket"] == "incorrect_valid" else 1,
                                       c["ts"]))
            chosen = cands[:3]
            per_problem[sid] = chosen

        coverage[f"{model_key}__{task_cfg}"] = {
            "total_problems": len(per_problem),
            "with_3_valid": sum(1 for v in per_problem.values() if len(v) >= 3),
            "with_2_valid": sum(1 for v in per_problem.values() if len(v) == 2),
            "with_1_valid": sum(1 for v in per_problem.values() if len(v) == 1),
            "with_0_valid": sum(1 for v in per_problem.values() if len(v) == 0),
            "incorrect_valid_chosen": sum(1 for cs in per_problem.values()
                                            for c in cs if c["bucket"] == "incorrect_valid"),
            "correct_chosen": sum(1 for cs in per_problem.values()
                                    for c in cs if c["bucket"] == "correct"),
            "problems_short": sorted(
                [{"sample_id": s, "valid_now": len(v),
                  "buckets": [c["bucket"] for c in v]}
                 for s, v in per_problem.items() if len(v) < 3],
                key=lambda x: (x["valid_now"], x["sample_id"]),
            ),
        }

        if args.dry_run:
            continue

        # Materialize
        for conv_idx in range(3):
            conv_dir = cell_dir_root / f"conv{conv_idx}"
            conv_dir.mkdir(parents=True, exist_ok=True)
        manifest = {}
        for sid, cands in per_problem.items():
            for i, cand in enumerate(cands):
                target = cell_dir_root / f"conv{i}" / f"{sid.replace('/', '_')}.json"
                shutil.copy(cand["trace_path"], target)
                manifest.setdefault(sid, []).append({
                    "conv_idx": i,
                    "bucket": cand["bucket"],
                    "src_out_dir": cand["out_dir"],
                })
        # Empty fn-summary stub (we already excluded user-sim-induced)
        for conv_idx in range(3):
            (cell_dir_root / f"conv{conv_idx}" / "false_negatives.json").write_text(
                json.dumps({"summary": {"user_sim_induced_ids": []}}, indent=2)
            )
        (cell_dir_root / "conv_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True)
        )

    COVERAGE_OUT.parent.mkdir(parents=True, exist_ok=True)
    COVERAGE_OUT.write_text(json.dumps(coverage, indent=2, sort_keys=True))

    # Print a tidy summary
    print(f"{'cell':45s}  {'#prob':>5}  {'≥3':>4}  {'2':>3}  {'1':>3}  {'0':>3}  {'icv_chosen':>10}")
    print("-" * 95)
    for key, c in sorted(coverage.items()):
        print(f"{key:45s}  {c['total_problems']:>5}  {c['with_3_valid']:>4}  "
              f"{c['with_2_valid']:>3}  {c['with_1_valid']:>3}  {c['with_0_valid']:>3}  "
              f"{c['incorrect_valid_chosen']:>10}")
    print()
    print(f"Wrote {COVERAGE_OUT}")
    if not args.dry_run:
        print(f"Pool root: {POOL_ROOT}")


if __name__ == "__main__":
    main()

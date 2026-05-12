#!/usr/bin/env python3
"""Cross-benchmark results aggregator.

Walks one or more output directories, reads each run's standardized
``run_summary.json``, and emits a single CSV (or pretty-printed table) —
one row per run, columns spanning the four benchmarks.

The standardized ``run_summary.json`` shape every benchmark writes:

    {
      "benchmark": "lic" | "collabllm" | "huang_phase1" | "huang_phase2" | "tau2",
      "experiment_name": str,
      "metrics": {...},   # benchmark-specific summary metrics
      "output_dir": str,
      "timestamp": str,
      ...                 # benchmark-specific extras (e.g. variants, seeds)
    }

(Why ``run_summary.json`` not ``results.json``: LiC's pre-existing
``results.json`` is a list of per-sample dicts. We don't want to break
that. ``run_summary.json`` is the new cross-benchmark contract.)

Usage:
    python scripts/aggregate_results.py outputs/2026-05-11/ outputs/huang_eval/
    python scripts/aggregate_results.py --csv runs.csv outputs/
    python scripts/aggregate_results.py --filter benchmark=huang_phase2 outputs/

If a run dir has no ``run_summary.json`` (e.g. older LiC runs), the
aggregator falls back to ``metrics.json`` + the Hydra ``.hydra/overrides.yaml``
to reconstruct what it can. This is best-effort — newly produced runs from
the Hydra-ified entry points will have ``run_summary.json`` directly.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Optional


def _read_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _read_yaml(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        from omegaconf import OmegaConf

        return OmegaConf.to_container(OmegaConf.load(path), resolve=True)
    except Exception:
        return None


def _find_runs(root: Path) -> Iterable[Path]:
    """Yield run directories under ``root``.

    A directory is considered a run if it contains ``run_summary.json``,
    ``results.json``, ``metrics.json``, or a ``.hydra/`` subdir. We don't
    descend into matched run dirs so nested artifacts (e.g. ``traces/``) aren't
    visited.
    """
    if not root.exists():
        return
    queue = [root]
    while queue:
        path = queue.pop(0)
        if not path.is_dir():
            continue
        if any((path / name).exists() for name in ("run_summary.json", "results.json", "metrics.json")):
            yield path
            continue
        if (path / ".hydra").exists():
            yield path
            continue
        try:
            queue.extend(sorted(path.iterdir()))
        except PermissionError:
            continue


def _tau2_summary_from_legacy(run_dir: Path) -> Optional[dict[str, Any]]:
    """Reconstruct a run-summary-shaped dict from a legacy tau2-bench run.

    Tau2 runs written before the run_summary.json change have config.json
    (run-level args) and results.json (per-task list). Both files exist
    side-by-side; the absence of a Hydra .hydra/ dir distinguishes them
    from older LiC runs.
    """
    config = _read_json(run_dir / "config.json")
    results = _read_json(run_dir / "results.json")
    if not isinstance(config, dict) or not isinstance(results, list):
        return None
    if "agent_llm" not in config or "strategies" not in config:
        return None  # not a tau2 config.json

    # Compute per-strategy success rates from the per-task list.
    per_strategy: dict[str, Any] = {}
    for r in results:
        if "error" in r:
            continue
        strat = r.get("strategy")
        reward = r.get("reward")
        if strat is None or reward is None:
            continue
        bucket = per_strategy.setdefault(strat, {"n": 0, "n_success": 0, "total_cost_usd": 0.0, "rewards": []})
        bucket["n"] += 1
        if reward > 0:
            bucket["n_success"] += 1
        bucket["total_cost_usd"] += r.get("total_cost", 0) or 0
        bucket["rewards"].append(reward)
    for strat, b in per_strategy.items():
        b["success_rate"] = b["n_success"] / b["n"] if b["n"] else 0
        b["avg_reward"] = sum(b["rewards"]) / len(b["rewards"]) if b["rewards"] else 0
        del b["rewards"]

    return {
        "benchmark": "tau2",
        "experiment_name": run_dir.name,
        "strategies": config.get("strategies"),
        "num_trials": config.get("num_trials"),
        "metrics": per_strategy,
        "num_results": len(results),
        "output_dir": str(run_dir),
        "timestamp": config.get("timestamp"),
    }


def _row_for(run_dir: Path) -> Optional[dict[str, Any]]:
    """Extract one row's worth of summary fields from a run directory."""
    # Prefer the cross-benchmark standard file.
    summary = _read_json(run_dir / "run_summary.json")
    if not isinstance(summary, dict):
        # Tau2 legacy: config.json + results.json (no Hydra dir).
        summary = _tau2_summary_from_legacy(run_dir)
    if not isinstance(summary, dict):
        # Fall back: reconstruct from metrics.json + Hydra config/overrides.
        # (LiC's results.json is a per-sample list; not used here.)
        metrics = _read_json(run_dir / "metrics.json")
        overrides = _read_yaml(run_dir / ".hydra" / "overrides.yaml")
        config = _read_yaml(run_dir / ".hydra" / "config.yaml")
        if metrics is None and overrides is None and config is None:
            return None
        summary = {
            "benchmark": (config or {}).get("benchmark") or "lic",
            "experiment_name": (config or {}).get("experiment_name", run_dir.name),
            "metrics": metrics or {},
            "output_dir": str(run_dir),
            "timestamp": None,
            "_overrides": overrides,
        }

    return {
        "benchmark": summary.get("benchmark", "?"),
        "experiment_name": summary.get("experiment_name", "?"),
        "timestamp": summary.get("timestamp"),
        "output_dir": summary.get("output_dir", str(run_dir)),
        "metrics_summary": _summarize_metrics(summary.get("metrics", {})),
        "variants": summary.get("variants"),
        "analyzer_prompt_versions": summary.get("analyzer_prompt_versions"),
        "num_results": summary.get("num_results") or summary.get("num_turns"),
    }


def _summarize_metrics(metrics: dict) -> str:
    """Best-effort one-line summary of the benchmark-specific metrics blob."""
    if not metrics:
        return ""
    pieces = []
    # LiC / CollabLLM style: accuracy fields
    for k in ("accuracy", "pass_rate", "score"):
        if k in metrics:
            pieces.append(f"{k}={metrics[k]:.3f}" if isinstance(metrics[k], float) else f"{k}={metrics[k]}")
    # Huang style: per-pair win rates inside metrics["fc_vs_ao"], etc.
    # Tau2 style: per-strategy {success_rate, n_success, n, ...} blobs.
    for sub_key, sub in metrics.items():
        if not isinstance(sub, dict):
            continue
        win_rate = sub.get("win_rate") or sub.get("quality_win_rate")
        if win_rate is not None and isinstance(win_rate, (int, float)):
            pieces.append(f"{sub_key}={win_rate:.3f}")
            continue
        success_rate = sub.get("success_rate")
        if success_rate is not None and isinstance(success_rate, (int, float)):
            n = sub.get("n")
            pieces.append(
                f"{sub_key}={success_rate:.3f}" + (f" (n={n})" if n else "")
            )
    return ", ".join(pieces) if pieces else json.dumps(metrics)[:80]


def _apply_filter(row: dict, filt: dict[str, str]) -> bool:
    for k, v in filt.items():
        actual = row.get(k)
        if actual is None or str(actual) != v:
            return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="One or more directories to scan")
    parser.add_argument("--csv", type=Path, default=None, help="Write CSV here (default: pretty-print to stdout)")
    parser.add_argument("--filter", action="append", default=[],
                        help="Filter rows by field=value (e.g. benchmark=huang_phase2). Repeatable.")
    args = parser.parse_args()

    filt = dict(piece.split("=", 1) for piece in args.filter)

    rows: list[dict[str, Any]] = []
    for root in args.paths:
        for run_dir in _find_runs(root):
            row = _row_for(run_dir)
            if row is None:
                continue
            if not _apply_filter(row, filt):
                continue
            rows.append(row)

    if not rows:
        print("No runs matched.", file=sys.stderr)
        sys.exit(1)

    fieldnames = [
        "benchmark", "experiment_name", "timestamp",
        "num_results", "variants", "analyzer_prompt_versions",
        "metrics_summary", "output_dir",
    ]
    if args.csv:
        with open(args.csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({k: (json.dumps(row[k]) if isinstance(row.get(k), (dict, list)) else row.get(k)) for k in fieldnames})
        print(f"Wrote {len(rows)} rows to {args.csv}", file=sys.stderr)
    else:
        # Pretty stdout
        widths = {k: max(len(k), max((len(str(row.get(k, ""))) for row in rows), default=0)) for k in fieldnames}
        # Clamp absurdly long columns
        for k in widths:
            widths[k] = min(widths[k], 60)

        header = " | ".join(k.ljust(widths[k]) for k in fieldnames)
        print(header)
        print("-" * len(header))
        for row in rows:
            values = []
            for k in fieldnames:
                v = row.get(k)
                if isinstance(v, (dict, list)):
                    v = json.dumps(v)
                s = "" if v is None else str(v)
                if len(s) > widths[k]:
                    s = s[: widths[k] - 1] + "…"
                values.append(s.ljust(widths[k]))
            print(" | ".join(values))
        print(f"\n{len(rows)} runs.")


if __name__ == "__main__":
    main()

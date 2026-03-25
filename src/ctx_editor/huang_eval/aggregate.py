"""Aggregate evaluation results and compute win rates.

Phase 1: FC-vs-AO breakdown by turn type.
Phase 2: S3-vs-AO, S3-vs-FC on failure subset.
"""

import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def load_turn_results(results_path: str | Path) -> list[dict]:
    """Load per-turn results from a JSONL file."""
    results = []
    with open(results_path) as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))
    return results


def _win_rate(results: list[dict], pair_key: str, dimension: str) -> dict[str, float]:
    """Compute win rate for a specific pair and dimension.

    Returns dict with keys: condition_1_wins, condition_2_wins, ties, total,
    condition_1_rate, condition_2_rate, tie_rate.
    """
    judgments = [r["judgments"][pair_key] for r in results if pair_key in r.get("judgments", {})]
    if not judgments:
        return {"total": 0}

    # Parse the pair key to get condition names
    parts = pair_key.split("_vs_")
    c1, c2 = parts[0], parts[1]

    winner_key = f"{dimension}_winner"
    c1_wins = sum(1 for j in judgments if j[winner_key] == c1)
    c2_wins = sum(1 for j in judgments if j[winner_key] == c2)
    ties = sum(1 for j in judgments if j[winner_key] == "tie")
    total = len(judgments)

    return {
        f"{c1}_wins": c1_wins,
        f"{c2}_wins": c2_wins,
        "ties": ties,
        "total": total,
        f"{c1}_rate": c1_wins / total if total else 0,
        f"{c2}_rate": c2_wins / total if total else 0,
        "tie_rate": ties / total if total else 0,
    }


def aggregate_phase1(results: list[dict]) -> dict[str, Any]:
    """Aggregate Phase 1 results: FC vs AO win rates overall and by turn type.

    Returns:
        Dict with overall metrics and per-turn-type breakdowns.
    """
    metrics = {
        "total_turns": len(results),
        "turn_type_distribution": defaultdict(int),
    }

    # Turn type distribution
    for r in results:
        metrics["turn_type_distribution"][r.get("turn_type", "unknown")] += 1
    metrics["turn_type_distribution"] = dict(metrics["turn_type_distribution"])

    # Overall FC vs AO
    metrics["overall"] = {
        "quality": _win_rate(results, "fc_vs_ao", "quality"),
        "ontopic": _win_rate(results, "fc_vs_ao", "ontopic"),
    }

    # By turn type
    metrics["by_turn_type"] = {}
    for turn_type in ("new_ask", "feedback", "no_feedback"):
        subset = [r for r in results if r.get("turn_type") == turn_type]
        if subset:
            metrics["by_turn_type"][turn_type] = {
                "count": len(subset),
                "quality": _win_rate(subset, "fc_vs_ao", "quality"),
                "ontopic": _win_rate(subset, "fc_vs_ao", "ontopic"),
            }

    # Identify AO failure turns (FC wins on quality)
    ao_failures = []
    for r in results:
        j = r.get("judgments", {}).get("fc_vs_ao", {})
        if j.get("quality_winner") == "fc":
            ao_failures.append({
                "conversation_id": r["conversation_id"],
                "turn_index": r["turn_index"],
                "turn_type": r.get("turn_type"),
            })
    metrics["ao_failure_count"] = len(ao_failures)
    metrics["ao_failure_rate"] = len(ao_failures) / len(results) if results else 0

    return metrics, ao_failures


def aggregate_phase2(results: list[dict]) -> dict[str, Any]:
    """Aggregate Phase 2 results: S3 vs AO and S3 vs FC on failure subset.

    Returns:
        Dict with win rates for S3 comparisons.
    """
    metrics = {
        "total_turns": len(results),
    }

    # S3 vs AO
    for pair in ("ao_vs_s3", "fc_vs_s3"):
        if any(pair in r.get("judgments", {}) for r in results):
            metrics[pair] = {
                "quality": _win_rate(results, pair, "quality"),
                "ontopic": _win_rate(results, pair, "ontopic"),
            }

    # S1.5 vs AO (if present)
    for pair in ("ao_vs_s15", "fc_vs_s15"):
        if any(pair in r.get("judgments", {}) for r in results):
            metrics[pair] = {
                "quality": _win_rate(results, pair, "quality"),
                "ontopic": _win_rate(results, pair, "ontopic"),
            }

    # S2 vs AO (if present)
    for pair in ("ao_vs_s2", "fc_vs_s2"):
        if any(pair in r.get("judgments", {}) for r in results):
            metrics[pair] = {
                "quality": _win_rate(results, pair, "quality"),
                "ontopic": _win_rate(results, pair, "ontopic"),
            }

    # Edit rates
    for key, analysis_key in [("s3_edit_rate", "s3_analysis"), ("s2_edit_rate", "s2_analysis")]:
        analysis_results = [r for r in results if analysis_key in r]
        if analysis_results:
            edited = sum(1 for r in analysis_results if r[analysis_key].get("edited", False))
            metrics[key] = edited / len(analysis_results)

    # All known pairs for by-turn-type breakdown
    all_pairs = [
        "ao_vs_s3", "fc_vs_s3", "ao_vs_s15", "fc_vs_s15", "ao_vs_s2", "fc_vs_s2",
    ]

    # By turn type
    metrics["by_turn_type"] = {}
    for turn_type in ("new_ask", "feedback", "no_feedback"):
        subset = [r for r in results if r.get("turn_type") == turn_type]
        if subset:
            entry = {"count": len(subset)}
            for pair in all_pairs:
                if any(pair in r.get("judgments", {}) for r in subset):
                    entry[pair] = {
                        "quality": _win_rate(subset, pair, "quality"),
                        "ontopic": _win_rate(subset, pair, "ontopic"),
                    }
            metrics["by_turn_type"][turn_type] = entry

    return metrics


def format_summary(phase1_metrics: dict, phase2_metrics: dict | None = None) -> str:
    """Format metrics as human-readable summary."""
    lines = []
    lines.append("=" * 60)
    lines.append("HUANG EVALUATION RESULTS")
    lines.append("=" * 60)

    lines.append(f"\nTotal Phase 1 turns evaluated: {phase1_metrics['total_turns']}")
    lines.append(f"Turn type distribution: {phase1_metrics['turn_type_distribution']}")

    lines.append("\n--- FC vs AO (Overall) ---")
    for dim in ("quality", "ontopic"):
        wr = phase1_metrics["overall"][dim]
        if wr.get("total", 0) > 0:
            lines.append(
                f"  {dim}: FC wins {wr.get('fc_rate', 0):.1%}, "
                f"AO wins {wr.get('ao_rate', 0):.1%}, "
                f"Tie {wr.get('tie_rate', 0):.1%} (n={wr['total']})"
            )

    lines.append("\n--- FC vs AO (By Turn Type) ---")
    for tt, data in phase1_metrics.get("by_turn_type", {}).items():
        lines.append(f"  {tt} (n={data['count']}):")
        for dim in ("quality", "ontopic"):
            wr = data[dim]
            if wr.get("total", 0) > 0:
                lines.append(
                    f"    {dim}: FC wins {wr.get('fc_rate', 0):.1%}, "
                    f"AO wins {wr.get('ao_rate', 0):.1%}, "
                    f"Tie {wr.get('tie_rate', 0):.1%}"
                )

    lines.append(
        f"\nAO failure turns (FC > AO on quality): "
        f"{phase1_metrics['ao_failure_count']} "
        f"({phase1_metrics['ao_failure_rate']:.1%})"
    )

    if phase2_metrics:
        lines.append("\n" + "=" * 60)
        lines.append("PHASE 2: S3 ON AO-FAILURE SUBSET")
        lines.append("=" * 60)
        lines.append(f"\nTotal turns evaluated: {phase2_metrics['total_turns']}")

        if "s3_edit_rate" in phase2_metrics:
            lines.append(f"S3 edit rate: {phase2_metrics['s3_edit_rate']:.1%}")

        for pair in ("ao_vs_s3", "fc_vs_s3", "ao_vs_s15", "fc_vs_s15"):
            if pair in phase2_metrics:
                parts = pair.split("_vs_")
                lines.append(f"\n--- {parts[0].upper()} vs {parts[1].upper()} ---")
                for dim in ("quality", "ontopic"):
                    wr = phase2_metrics[pair].get(dim, {})
                    if wr.get("total", 0) > 0:
                        lines.append(
                            f"  {dim}: {parts[0].upper()} wins {wr.get(f'{parts[0]}_rate', 0):.1%}, "
                            f"{parts[1].upper()} wins {wr.get(f'{parts[1]}_rate', 0):.1%}, "
                            f"Tie {wr.get('tie_rate', 0):.1%} (n={wr['total']})"
                        )

        if phase2_metrics.get("by_turn_type"):
            lines.append("\n--- S3 Results By Turn Type ---")
            for tt, data in phase2_metrics["by_turn_type"].items():
                lines.append(f"  {tt} (n={data['count']}):")
                for pair in ("ao_vs_s3", "fc_vs_s3"):
                    if pair in data:
                        parts = pair.split("_vs_")
                        for dim in ("quality", "ontopic"):
                            wr = data[pair].get(dim, {})
                            if wr.get("total", 0) > 0:
                                lines.append(
                                    f"    {pair} {dim}: "
                                    f"{parts[0].upper()} {wr.get(f'{parts[0]}_rate', 0):.1%}, "
                                    f"{parts[1].upper()} {wr.get(f'{parts[1]}_rate', 0):.1%}, "
                                    f"Tie {wr.get('tie_rate', 0):.1%}"
                                )

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def write_breakdown_csv(
    results: list[dict],
    pair_keys: list[str],
    output_path: str | Path,
) -> None:
    """Write win rates by turn type as CSV."""
    import csv

    turn_types = ["new_ask", "feedback", "no_feedback", "all"]
    header = ["turn_type", "count"]
    for pair in pair_keys:
        parts = pair.split("_vs_")
        for dim in ("quality", "ontopic"):
            header.extend([
                f"{pair}_{dim}_{parts[0]}_rate",
                f"{pair}_{dim}_{parts[1]}_rate",
                f"{pair}_{dim}_tie_rate",
            ])

    rows = []
    for tt in turn_types:
        subset = results if tt == "all" else [r for r in results if r.get("turn_type") == tt]
        if not subset:
            continue
        row = [tt, len(subset)]
        for pair in pair_keys:
            for dim in ("quality", "ontopic"):
                wr = _win_rate(subset, pair, dim)
                parts = pair.split("_vs_")
                row.extend([
                    f"{wr.get(f'{parts[0]}_rate', 0):.3f}",
                    f"{wr.get(f'{parts[1]}_rate', 0):.3f}",
                    f"{wr.get('tie_rate', 0):.3f}",
                ])
        rows.append(row)

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    logger.info(f"Wrote breakdown CSV to {output_path}")

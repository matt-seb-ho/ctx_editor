"""Promote inline Huang/WildChat analyses into the shared AnalysisCache.

The Huang phase2 pipeline historically didn't use the shared
``AnalysisCache``. Instead, each ``*_analysis`` field was written inline
into ``turn_results.jsonl`` per run dir. That meant the new
``AC3RewriteStrategy`` (post-R5 refactor) couldn't reuse those analyses
when running cross-benchmark fills on WildChat.

This script walks one or more phase2 run dirs, reconstructs the
``ConversationTrace`` the analyzer would have seen, computes the
``AnalysisCache`` key the same way ``ConversationAnalyzer.analyze()``
does, converts the inline analysis dict into an ``AnalysisResult``,
and writes it to the cache. After this, future Rewrite/Reset/Augment
runs on the same conversation prefixes will hit cache.

Usage:
    python scripts/import_huang_analyses_to_cache.py \\
        --phase2-dir outputs/post_may18_r3_wildchat_fills/s3_DeepSeek_V4_Flash_seed42_1779256743 \\
        --cache-dir outputs/analysis_cache

    # Multiple phase2 dirs (glob):
    python scripts/import_huang_analyses_to_cache.py \\
        --phase2-dir 'outputs/post_may18_r3_wildchat_fills/*_seed42_*' \\
        --cache-dir outputs/analysis_cache

    # Dry run to see what would be written without actually writing:
    python scripts/import_huang_analyses_to_cache.py \\
        --phase2-dir outputs/.../some_run --dry-run

Notes:
- Re-running is idempotent: existing cache entries are skipped (not
  re-written) unless ``--overwrite`` is passed.
- ``raw_output`` is not preserved in the inline storage, so cached
  entries have ``raw_output=""``. This only affects forensics, not
  downstream strategy behavior.
- Variants written: any ``{prefix}_analysis`` field present in a turn
  record (typically ``s3_analysis``, ``s15_analysis``, ``s2_analysis``,
  ``augment_analysis``). The variant's analyzer prompt version is read
  from ``config.json`` under ``analyzer_prompt_versions``.
"""

from __future__ import annotations

import argparse
import glob
import json
import logging
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ctx_editor.huang_eval.replay import build_fc_trace  # noqa: E402
from ctx_editor.strategies.analyzer import AnalysisResult  # noqa: E402
from ctx_editor.strategies.analysis_cache import AnalysisCache  # noqa: E402

logger = logging.getLogger(__name__)


# Variant key suffix → which config field gives the prompt version.
_VARIANT_TO_CONFIG_KEY = {
    "s3": "s3",
    "s15": "s15",
    "s2": "s2",
    "augment": "augment",
}


def _load_conversations(phase1_dir: Path) -> dict[str, list[dict[str, str]]]:
    """Map conversation_id -> turns list."""
    conv_dir = phase1_dir / "conversations"
    out: dict[str, list[dict[str, str]]] = {}
    for p in conv_dir.glob("*.json"):
        try:
            data = json.loads(p.read_text())
        except json.JSONDecodeError as e:
            logger.warning("skip malformed %s: %s", p, e)
            continue
        conv_id = data.get("conversation_id") or p.stem
        turns = data.get("turns", [])
        out[conv_id] = turns
    return out


def _analysis_to_result(inline: dict[str, Any]) -> AnalysisResult:
    return AnalysisResult(
        user_intent=inline.get("user_intent", "") or "",
        aligned=inline.get("aligned", "") or "",
        issues=inline.get("issues", "") or "",
        raw_output="",  # not preserved inline
        corrective_direction=inline.get("corrective_direction", "") or "",
    )


def _process_phase2_dir(
    phase2_dir: Path,
    cache: AnalysisCache,
    *,
    dry_run: bool = False,
    overwrite: bool = False,
) -> dict[str, int]:
    stats = {"records_seen": 0, "variants_seen": 0, "written": 0, "skipped_existing": 0,
             "missing_conv": 0, "missing_phase1": 0}

    cfg_path = phase2_dir / "config.json"
    if not cfg_path.exists():
        logger.error("no config.json in %s; skipping", phase2_dir)
        return stats
    cfg = json.loads(cfg_path.read_text())

    phase1_dir_raw = cfg.get("phase1_dir")
    if not phase1_dir_raw:
        logger.error("no phase1_dir in %s; skipping", cfg_path)
        return stats
    phase1_dir = Path(phase1_dir_raw)
    if not phase1_dir.is_absolute():
        # Resolve relative to repo root (assumed: cwd or parent of phase2_dir's project root)
        candidates = [Path.cwd() / phase1_dir, phase2_dir.parent.parent.parent / phase1_dir]
        for c in candidates:
            if c.exists():
                phase1_dir = c
                break
    if not phase1_dir.exists():
        logger.error("phase1_dir %s does not exist; skipping %s", phase1_dir, phase2_dir)
        stats["missing_phase1"] += 1
        return stats

    analyzer_model = cfg.get("analyzer_model")
    prompt_versions = cfg.get("analyzer_prompt_versions", {})
    if not analyzer_model:
        logger.error("no analyzer_model in %s; skipping", cfg_path)
        return stats

    conversations = _load_conversations(phase1_dir)
    logger.info("loaded %d conversations from %s", len(conversations), phase1_dir)

    turn_results_path = phase2_dir / "turn_results.jsonl"
    if not turn_results_path.exists():
        logger.error("no turn_results.jsonl in %s; skipping", phase2_dir)
        return stats

    with turn_results_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            stats["records_seen"] += 1

            conv_id = rec.get("conversation_id")
            turn_index = rec.get("turn_index")
            if conv_id is None or turn_index is None:
                continue
            if conv_id not in conversations:
                stats["missing_conv"] += 1
                continue
            turns = conversations[conv_id]

            for variant_key in _VARIANT_TO_CONFIG_KEY:
                inline = rec.get(f"{variant_key}_analysis")
                if not inline or not isinstance(inline, dict):
                    continue
                # Some inline records skip the analyzer entirely (turn_type
                # gate not met). Those won't have user_intent/aligned.
                if not (inline.get("user_intent") or inline.get("aligned")
                        or inline.get("issues")):
                    continue

                stats["variants_seen"] += 1

                prompt_version = prompt_versions.get(variant_key)
                if not prompt_version:
                    logger.warning("no prompt_version for variant %s in %s; skipping",
                                   variant_key, cfg_path)
                    continue

                trace = build_fc_trace(turns, turn_index)
                trace_hash = AnalysisCache._hash_trace(trace)
                cache_key = AnalysisCache.make_key(
                    trace_hash=trace_hash,
                    analyzer_model=analyzer_model,
                    prompt_version=prompt_version,
                    spec_only=False,
                    memory_target_query="compare",
                    enforce_compliance=False,
                    memory_present=False,
                )

                if not overwrite and cache.lookup(cache_key) is not None:
                    stats["skipped_existing"] += 1
                    continue

                result = _analysis_to_result(inline)
                if dry_run:
                    stats["written"] += 1  # would-have-written
                    continue
                cache.store(
                    cache_key,
                    result,
                    key_inputs={
                        "analyzer_model": analyzer_model,
                        "prompt_version": prompt_version,
                        "spec_only": False,
                        "memory_target_query": "compare",
                        "enforce_compliance": False,
                        "memory_present": False,
                    },
                    experiment_origin=f"huang_phase2:{phase2_dir.name}",
                    provenance={
                        "imported_from": str(turn_results_path),
                        "conversation_id": conv_id,
                        "turn_index": turn_index,
                        "variant": variant_key,
                    },
                )
                stats["written"] += 1

    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--phase2-dir", required=True, action="append",
                    help="path or glob to a Huang phase2 run dir. May be repeated.")
    ap.add_argument("--cache-dir", default="outputs/analysis_cache",
                    help="path to the AnalysisCache root.")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would be written but don't write.")
    ap.add_argument("--overwrite", action="store_true",
                    help="re-write cache entries that already exist.")
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()

    logging.basicConfig(level=args.log_level, format="%(levelname)s %(name)s %(message)s")

    cache = AnalysisCache(args.cache_dir)

    dirs: list[Path] = []
    for pattern in args.phase2_dir:
        matches = [Path(p) for p in glob.glob(pattern)]
        if not matches and Path(pattern).exists():
            matches = [Path(pattern)]
        dirs.extend(matches)

    if not dirs:
        logger.error("no phase2 dirs matched")
        return 2

    totals = {"records_seen": 0, "variants_seen": 0, "written": 0,
              "skipped_existing": 0, "missing_conv": 0, "missing_phase1": 0}
    for d in dirs:
        logger.info("processing %s", d)
        s = _process_phase2_dir(d, cache, dry_run=args.dry_run, overwrite=args.overwrite)
        for k, v in s.items():
            totals[k] = totals.get(k, 0) + v
        logger.info("  -> %s", s)

    logger.info("=== totals ===")
    for k, v in totals.items():
        logger.info("  %s: %s", k, v)
    if args.dry_run:
        logger.info("(dry-run; no files modified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

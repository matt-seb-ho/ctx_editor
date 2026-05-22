#!/usr/bin/env python3
"""Phase 2: run AC3 variants on AO failure turns from Phase 1.

Takes Phase 1 output, selects turns where AO lost to FC on quality, and
evaluates the AC3 variants (Augment / Reset / Gated-Reset / Rewrite) to
demonstrate recovery.

Usage:
    python -m ctx_editor.huang_eval.run_phase2 \\
        phase1_dir=outputs/huang_eval/phase1/2026-... \\
        variants.s15=true variants.s2=true

Multi-seed sweep:
    python -m ctx_editor.huang_eval.run_phase2 \\
        phase1_dir=... --multirun seed=42,43,44

See ``ctx_editor/config/huang_phase2.yaml`` for all knobs (variants on/off,
per-variant analyzer prompt versions, models, etc.).
"""

import asyncio
import json
import logging
import random
from datetime import datetime
from pathlib import Path

import hydra
from dotenv import load_dotenv
from omegaconf import DictConfig, OmegaConf

load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from ..models import get_model_client
from ..models.endpoint_config import LoadBalancerConfig
from .pairwise_judge import judge_pairwise
from .replay import generate_ao, generate_augment, generate_fc, generate_s2, generate_s3, generate_s15
from .aggregate import aggregate_phase2, load_turn_results, format_summary, write_breakdown_csv

logger = logging.getLogger(__name__)


def load_phase1_data(phase1_dir: Path) -> tuple[list[dict], list[dict], dict]:
    """Load Phase 1 results, AO failure turns, and conversation data.

    Returns:
        (phase1_results, ao_failures, conversations_by_id)
    """
    phase1_results = load_turn_results(phase1_dir / "turn_results.jsonl")

    with open(phase1_dir / "ao_failure_turns.json") as f:
        ao_failures = json.load(f)

    # Load conversations
    conversations = {}
    conv_dir = phase1_dir / "conversations"
    if conv_dir.exists():
        for conv_file in conv_dir.glob("*.json"):
            with open(conv_file) as f:
                conv = json.load(f)
                conversations[conv["conversation_id"]] = conv

    return phase1_results, ao_failures, conversations


def _judgment_dict(judgment) -> dict:
    """Pack a PairwiseJudgment into the result-file shape used since Phase 2 day 1."""
    return {
        "quality_winner": judgment.quality_winner,
        "ontopic_winner": judgment.ontopic_winner,
        "quality_justification": judgment.quality_justification,
        "ontopic_justification": judgment.ontopic_justification,
        "confidence": judgment.confidence,
    }


async def process_failure_turn(
    conversation: dict,
    turn_index: int,
    turn_type: str,
    phase1_result: dict | None,
    model_client,
    respondent_model: str,
    judge_model: str,
    analyzer_model: str,
    variants: dict,
    analyzer_prompt_versions: dict,
    min_turns_s2: int,
    regenerate_baselines: bool,
    results_file: Path,
    rng: random.Random,
    memory=None,
    analysis_cache_dir: str | None = None,
    s3_compaction_prompt_name: str = "context_compaction",
    s3_open_ended_output: bool = False,
) -> dict | None:
    """Process one AO-failure turn through the requested AC3 variants.

    ``variants`` is a dict like ``{"s3": True, "s15": False, "s2": False,
    "augment": False}`` selecting which AC3 ops to evaluate.
    ``analyzer_prompt_versions`` is a dict with the same keys, e.g.
    ``{"s3": "v8", "s15": "v8", "s2": "v11", "augment": "v8"}`` selecting
    the analyzer prompt version from
    :mod:`ctx_editor.strategies.analyzer_prompts`.
    """
    turns = conversation["turns"]
    conv_id = conversation["conversation_id"]

    try:
        # We need the AO/FC responses for comparison. Regenerate or use cached.
        if not regenerate_baselines and phase1_result and "ao_response" in phase1_result:
            ao_response = phase1_result["ao_response"]
            fc_response = phase1_result.get("fc_response", "")
        else:
            ao_response, fc_response = await asyncio.gather(
                generate_ao(turns, turn_index, model_client, respondent_model),
                generate_fc(turns, turn_index, model_client, respondent_model),
            )

        result: dict = {
            "conversation_id": conv_id,
            "turn_index": turn_index,
            "turn_type": turn_type,
            "user_message": turns[turn_index]["content"][:500],
            "ao_response": ao_response,
            "fc_response": fc_response,
            "judgments": {},
            "timestamp": datetime.now().isoformat(),
        }

        # AC3-Rewrite (S3) — default on
        if variants.get("s3", True):
            s3_response, s3_analysis = await generate_s3(
                turns, turn_index, model_client, respondent_model, analyzer_model,
                analyzer_prompt_version=analyzer_prompt_versions.get("s3", "v8"),
                analysis_cache_dir=analysis_cache_dir,
                compaction_prompt_name=s3_compaction_prompt_name,
                open_ended_output=s3_open_ended_output,
            )
            ao_vs_s3, fc_vs_s3 = await asyncio.gather(
                judge_pairwise(turns, turn_index, ao_response, s3_response, "ao", "s3",
                               model_client, judge_model, rng),
                judge_pairwise(turns, turn_index, fc_response, s3_response, "fc", "s3",
                               model_client, judge_model, rng),
            )
            result["s3_response"] = s3_response
            result["s3_analysis"] = s3_analysis
            result["judgments"]["ao_vs_s3"] = _judgment_dict(ao_vs_s3)
            result["judgments"]["fc_vs_s3"] = _judgment_dict(fc_vs_s3)

        # AC3-Reset (S1.5) — programmatic, no LLM rewrite
        if variants.get("s15", False):
            s15_response, s15_analysis = await generate_s15(
                turns, turn_index, model_client, respondent_model, analyzer_model,
                memory=memory,
                analyzer_prompt_version=analyzer_prompt_versions.get("s15", "v8"),
                analysis_cache_dir=analysis_cache_dir,
            )
            ao_vs_s15, fc_vs_s15 = await asyncio.gather(
                judge_pairwise(turns, turn_index, ao_response, s15_response, "ao", "s15",
                               model_client, judge_model, rng),
                judge_pairwise(turns, turn_index, fc_response, s15_response, "fc", "s15",
                               model_client, judge_model, rng),
            )
            result["s15_response"] = s15_response
            result["s15_analysis"] = s15_analysis
            result["judgments"]["ao_vs_s15"] = _judgment_dict(ao_vs_s15)
            result["judgments"]["fc_vs_s15"] = _judgment_dict(fc_vs_s15)

        # AC3-Gated-Reset (S2) — v11 analyzer + min_turns gate
        if variants.get("s2", False):
            s2_response, s2_analysis = await generate_s2(
                turns, turn_index, model_client, respondent_model, analyzer_model,
                analyzer_prompt_version=analyzer_prompt_versions.get("s2", "v11"),
                min_turns=min_turns_s2,
                analysis_cache_dir=analysis_cache_dir,
            )
            ao_vs_s2, fc_vs_s2 = await asyncio.gather(
                judge_pairwise(turns, turn_index, ao_response, s2_response, "ao", "s2",
                               model_client, judge_model, rng),
                judge_pairwise(turns, turn_index, fc_response, s2_response, "fc", "s2",
                               model_client, judge_model, rng),
            )
            result["s2_response"] = s2_response
            result["s2_analysis"] = s2_analysis
            result["judgments"]["ao_vs_s2"] = _judgment_dict(ao_vs_s2)
            result["judgments"]["fc_vs_s2"] = _judgment_dict(fc_vs_s2)

        # AC3-Augment — new in Phase 2 of cleanup; first run via Phase 3 CLI
        if variants.get("augment", False):
            augment_response, augment_analysis = await generate_augment(
                turns, turn_index, model_client, respondent_model, analyzer_model,
                memory=memory,
                analyzer_prompt_version=analyzer_prompt_versions.get("augment", "v8"),
                analysis_cache_dir=analysis_cache_dir,
            )
            ao_vs_aug, fc_vs_aug = await asyncio.gather(
                judge_pairwise(turns, turn_index, ao_response, augment_response, "ao", "augment",
                               model_client, judge_model, rng),
                judge_pairwise(turns, turn_index, fc_response, augment_response, "fc", "augment",
                               model_client, judge_model, rng),
            )
            result["augment_response"] = augment_response
            result["augment_analysis"] = augment_analysis
            result["judgments"]["ao_vs_augment"] = _judgment_dict(ao_vs_aug)
            result["judgments"]["fc_vs_augment"] = _judgment_dict(fc_vs_aug)

        with open(results_file, "a") as f:
            f.write(json.dumps(result) + "\n")
        return result

    except Exception as e:
        logger.error(f"Conv {conv_id} turn {turn_index}: {e}")
        return None


async def run_phase2(cfg: DictConfig) -> None:
    """Main Phase 2 execution. ``cfg`` is the Hydra config from huang_phase2.yaml."""
    phase1_dir = Path(cfg.phase1_dir)
    if not phase1_dir.exists():
        logger.error(f"Phase 1 directory not found: {phase1_dir}")
        return

    output_dir = Path(cfg.logging.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(output_dir / "phase2.log"),
        ],
    )

    timestamp = datetime.now().strftime("%Y-%m-%d/%H-%M-%S")
    with open(output_dir / "config.yaml", "w") as f:
        f.write(OmegaConf.to_yaml(cfg, resolve=True))
    config_json = OmegaConf.to_container(cfg, resolve=True)
    config_json["timestamp"] = timestamp
    with open(output_dir / "config.json", "w") as f:
        json.dump(config_json, f, indent=2)

    logger.info(f"Phase 2 output: {output_dir}")
    logger.info(f"Loading Phase 1 data from {phase1_dir}")

    phase1_results, ao_failures, conversations = load_phase1_data(phase1_dir)
    logger.info(f"Phase 1: {len(phase1_results)} turn results, {len(ao_failures)} AO failures")

    if cfg.turns_file:
        with open(cfg.turns_file) as f:
            ao_failures = json.load(f)
        logger.info(f"Using custom turns file: {cfg.turns_file} ({len(ao_failures)} turns)")

    if not ao_failures:
        logger.warning("No turns to process. Nothing to do.")
        return

    if cfg.max_turns and len(ao_failures) > cfg.max_turns:
        rng_sample = random.Random(cfg.seed)
        ao_failures = rng_sample.sample(ao_failures, cfg.max_turns)
        logger.info(f"Sampled {len(ao_failures)} failure turns")

    p1_lookup = {(r["conversation_id"], r["turn_index"]): r for r in phase1_results}

    valid_failures = [f for f in ao_failures if f["conversation_id"] in conversations]
    skipped = len(ao_failures) - len(valid_failures)
    if skipped:
        logger.warning(f"{skipped} failure turns skipped (conversation data missing)")
    logger.info(f"Processing {len(valid_failures)} AO failure turns")

    # Resolve variants + per-variant analyzer prompt versions out of the config
    variants = OmegaConf.to_container(cfg.variants, resolve=True)
    analyzer_prompt_versions = OmegaConf.to_container(cfg.analyzer_prompt_versions, resolve=True)
    logger.info(f"Variants enabled: {[k for k, v in variants.items() if v]}")
    logger.info(f"Analyzer prompt versions: {analyzer_prompt_versions}")

    load_balancer_config = None
    if getattr(cfg, "load_balancer", None):
        lb_dict = OmegaConf.to_container(cfg.load_balancer, resolve=True)
        load_balancer_config = LoadBalancerConfig.from_dict(lb_dict)
        logger.info(
            f"Using load_balancer with {len(load_balancer_config.endpoints)} endpoints"
        )
    model_client = get_model_client(cfg.respondent_model, load_balancer_config)

    results_file = output_dir / "turn_results.jsonl"
    results_file.touch()

    rng = random.Random(cfg.seed)
    semaphore = asyncio.Semaphore(cfg.max_concurrent)
    all_results: list[dict] = []

    async def process_with_semaphore(failure):
        async with semaphore:
            conv = conversations[failure["conversation_id"]]
            p1_result = p1_lookup.get(
                (failure["conversation_id"], failure["turn_index"])
            )
            logger.info(
                f"Processing {failure['conversation_id'][:20]}... "
                f"turn {failure['turn_index']} ({failure.get('turn_type', '?')})"
            )
            return await process_failure_turn(
                conversation=conv,
                turn_index=failure["turn_index"],
                turn_type=failure.get("turn_type", "unknown"),
                phase1_result=p1_result,
                model_client=model_client,
                respondent_model=cfg.respondent_model,
                judge_model=cfg.judge_model,
                analyzer_model=cfg.analyzer_model,
                variants=variants,
                analyzer_prompt_versions=analyzer_prompt_versions,
                min_turns_s2=cfg.min_turns_s2,
                regenerate_baselines=cfg.regenerate_baselines,
                results_file=results_file,
                rng=rng,
                analysis_cache_dir=getattr(cfg, "analysis_cache_dir", None),
                s3_compaction_prompt_name=getattr(cfg, "s3_compaction_prompt_name", "context_compaction"),
                s3_open_ended_output=getattr(cfg, "s3_open_ended_output", False),
            )

    tasks = [process_with_semaphore(f) for f in valid_failures]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for r in results:
        if isinstance(r, Exception):
            logger.error(f"Turn failed: {r}")
        elif r:
            all_results.append(r)

    if not all_results:
        all_results = load_turn_results(results_file)

    metrics = aggregate_phase2(all_results)

    phase1_metrics_path = phase1_dir / "metrics.json"
    phase1_metrics = {}
    if phase1_metrics_path.exists():
        with open(phase1_metrics_path) as f:
            phase1_metrics = json.load(f)

    with open(output_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    pair_keys = []
    if variants.get("s3", True):
        pair_keys.extend(["ao_vs_s3", "fc_vs_s3"])
    if variants.get("s15", False):
        pair_keys.extend(["ao_vs_s15", "fc_vs_s15"])
    if variants.get("s2", False):
        pair_keys.extend(["ao_vs_s2", "fc_vs_s2"])
    if variants.get("augment", False):
        pair_keys.extend(["ao_vs_augment", "fc_vs_augment"])
    write_breakdown_csv(all_results, pair_keys, output_dir / "breakdown_by_type.csv")

    summary = format_summary(phase1_metrics, metrics)
    with open(output_dir / "summary.txt", "w") as f:
        f.write(summary)

    # Cross-benchmark-standard run summary. See run_phase1.py for the rationale
    # on the filename (``run_summary.json`` not ``results.json``).
    run_summary = {
        "benchmark": "huang_phase2",
        "experiment_name": cfg.experiment_name,
        "phase1_dir": str(phase1_dir),
        "variants": variants,
        "analyzer_prompt_versions": analyzer_prompt_versions,
        "num_failure_turns": len(valid_failures),
        "num_results": len(all_results),
        "metrics": metrics,
        "phase1_metrics": phase1_metrics,
        "output_dir": str(output_dir),
        "timestamp": timestamp,
    }
    with open(output_dir / "run_summary.json", "w") as f:
        json.dump(run_summary, f, indent=2)

    print(summary)
    logger.info(f"Phase 2 complete. Results in {output_dir}")


@hydra.main(config_path="../config", config_name="huang_phase2", version_base=None)
def main(cfg: DictConfig) -> None:
    """Hydra entry point for Phase 2.

    Example invocations:
        python -m ctx_editor.huang_eval.run_phase2 phase1_dir=outputs/huang_eval/phase1/2026-...
        python -m ctx_editor.huang_eval.run_phase2 phase1_dir=... variants.s15=true variants.s2=true
        python -m ctx_editor.huang_eval.run_phase2 phase1_dir=... variants.augment=true
        python -m ctx_editor.huang_eval.run_phase2 phase1_dir=... --multirun seed=42,43,44
    """
    print(f"\nOutput directory: {cfg.logging.output_dir}\n")
    asyncio.run(run_phase2(cfg))


if __name__ == "__main__":
    main()

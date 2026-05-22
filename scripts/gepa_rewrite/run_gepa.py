"""Run GEPA optimization on the AC3-Rewrite compaction prompt.

Single-task search mode: each evaluator call runs a fixed mini-LiC eval
(12 problems on math conv0). Seed = current v1 prompt (or v5 if better).
Reflection LM: DeepSeek-V4-Flash wrapped as a sync callable.

Usage:
    python scripts/gepa_rewrite/run_gepa.py --budget 30
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import threading
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, "/home/v-homatthew/code_ref/gepa/src")
sys.path.insert(0, "/home/v-homatthew/ctx_editor/src")

from omegaconf import OmegaConf

import gepa
from gepa.optimize_anything import optimize_anything, GEPAConfig, EngineConfig, ReflectionConfig

from ctx_editor.models.endpoint_config import LoadBalancerConfig
from ctx_editor.models.openai_model import OpenAIModelClient

# Project-local
PROMPTS_DIR = Path("/home/v-homatthew/ctx_editor/src/ctx_editor/strategies/prompts")
GEPA_OUT_ROOT = Path("/home/v-homatthew/ctx_editor/outputs/_gepa_rewrite_runs")
GEPA_OUT_ROOT.mkdir(parents=True, exist_ok=True)

# Pull evaluator
sys.path.insert(0, "/home/v-homatthew/ctx_editor/scripts/gepa_rewrite")
from evaluator import evaluate_candidate  # noqa: E402


# ---------------------------------------------------------------------
# DeepSeek-V4-Flash as a synchronous LanguageModel for GEPA reflection
# ---------------------------------------------------------------------

class DeepSeekReflectionLM:
    """Sync LanguageModel wrapper around our OpenAIModelClient + foundry LB.

    Conforms to GEPA's LanguageModel protocol: callable with str or
    list[dict], returns str.
    """

    def __init__(self, model_name: str = "DeepSeek-V4-Flash",
                 lb_config_path: str | None = None,
                 max_tokens: int = 8000,
                 temperature: float = 1.0):
        if lb_config_path is None:
            lb_config_path = "/home/v-homatthew/ctx_editor/src/ctx_editor/config/load_balancer/multi_endpoint_foundry.yaml"
        cfg = OmegaConf.load(lb_config_path)
        lb = LoadBalancerConfig.from_dict(OmegaConf.to_container(cfg, resolve=True))
        self.client = OpenAIModelClient(load_balancer_config=lb)
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._lock = threading.Lock()
        # Use a single event loop on a dedicated thread for thread-safe sync calls
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

    def __call__(self, prompt: str | list[dict[str, Any]]) -> str:
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        else:
            messages = prompt
        fut = asyncio.run_coroutine_threadsafe(
            self.client.generate(
                messages=messages,
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=240,
            ),
            self._loop,
        )
        response = fut.result(timeout=300)
        return response.content


# ---------------------------------------------------------------------
# Evaluator wrapper for GEPA (single-task search)
# ---------------------------------------------------------------------

EVAL_LOG: list[dict[str, Any]] = []


def evaluator_wrapper(candidate: str) -> tuple[float, dict[str, Any]]:
    """GEPA evaluator: single-task mode. Returns (accuracy, side_info)."""
    score, info = evaluate_candidate(candidate)
    log_entry = {
        "ts": time.time(),
        "score": score,
        "n_correct": info.get("n_correct"),
        "n_evaluated": info.get("n_evaluated"),
        "n_total": info.get("n_total"),
        "elapsed_s": info.get("elapsed_s"),
        "run_dir": info.get("run_dir"),
        "candidate_preview": candidate[:300],
    }
    EVAL_LOG.append(log_entry)
    return score, info


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main(args: argparse.Namespace) -> None:
    ts = int(time.time())
    run_dir = GEPA_OUT_ROOT / f"gepa_run_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"GEPA run dir: {run_dir}")

    seed_path = PROMPTS_DIR / f"{args.seed_prompt}.txt"
    seed_text = seed_path.read_text()
    print(f"Seed prompt: {seed_path.name} ({len(seed_text)} chars)")

    # Unbiased R6 framing per docs/post_may18_r6_plan.md § "Objective string"
    # and § "Background string". No Reset reference, no faithful re-emitter
    # editorial, {conversation} explicitly OPTIONAL.
    objective = (
        "Optimize the prompt template for the second LLM call of a "
        "two-stage context-editing pipeline. The first stage already "
        "produced an analysis of a multi-turn conversation. Your prompt "
        "tells the second LLM how to turn (some subset of) the available "
        "inputs into a single 'compacted context' message that will "
        "REPLACE the conversation history before a downstream assistant "
        "generates its next response on a fixed last user message.\n\n"
        "Maximize the downstream task accuracy (LiC math eval on "
        "DeepSeek-V4-Flash).\n\n"
        "Available inputs (use any subset):\n"
        "- {analysis_user_intent} — analyzer's consolidated task spec.\n"
        "- {analysis_aligned} — analyzer's notes on what the assistant got right.\n"
        "- {analysis_issues} — analyzer's notes on what the assistant got wrong.\n"
        "- {conversation} — the full multi-turn conversation (OPTIONAL).\n\n"
        "Output format: the rewriter may put free-form scratchpad text "
        "first; wrap the final compacted message in "
        "<new_context>...</new_context>. Only the wrapped contents reach "
        "the downstream assistant."
    )

    background = (
        "The compacted context is the only summary the downstream assistant "
        "sees of the conversation history (besides the unchanged system "
        "prompt and the last user message). The compacted message should "
        "give the assistant enough state to continue the task correctly "
        "without dragging in distractions that might pull it off course."
    )

    reflection_lm = DeepSeekReflectionLM(
        model_name=args.reflection_model,
        max_tokens=12000,
        temperature=1.0,
    )

    print(f"Reflection LM: {args.reflection_model}")
    print(f"Budget: max_metric_calls={args.budget}")
    print()

    cfg = GEPAConfig(
        engine=EngineConfig(
            max_metric_calls=args.budget,
            parallel=False,    # serial since evaluator subprocesses ctx-editor
            display_progress_bar=True,
            run_dir=str(run_dir),
        ),
        reflection=ReflectionConfig(reflection_lm=reflection_lm),
    )

    t0 = time.time()
    result = optimize_anything(
        seed_candidate=seed_text,
        evaluator=evaluator_wrapper,
        objective=objective,
        background=background,
        config=cfg,
    )
    elapsed = time.time() - t0

    # Persist outputs
    best_path = run_dir / "best_candidate.txt"
    best_path.write_text(result.best_candidate)
    (run_dir / "eval_log.jsonl").write_text(
        "\n".join(json.dumps(e) for e in EVAL_LOG)
    )
    summary = {
        "seed_prompt": args.seed_prompt,
        "budget": args.budget,
        "elapsed_s": round(elapsed, 1),
        "n_evals": len(EVAL_LOG),
        "best_score": float(getattr(result, "best_score", 0.0))
            if hasattr(result, "best_score") else None,
        "best_idx": int(getattr(result, "best_idx", -1))
            if hasattr(result, "best_idx") else None,
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nDone in {elapsed:.0f}s. Best prompt -> {best_path}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--seed-prompt", default="context_compaction",
                   help="Name of the seed prompt (under strategies/prompts/) — without .txt")
    p.add_argument("--budget", type=int, default=30,
                   help="max_metric_calls (rough = N candidate evaluations)")
    p.add_argument("--reflection-model", default="DeepSeek-V4-Flash")
    main(p.parse_args())

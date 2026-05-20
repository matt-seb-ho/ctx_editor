# GEPA — notes

**Paper**: <https://arxiv.org/abs/2507.19457> (Lakshya Agrawal et al., 2025)
**Repo**: `~/code_ref/gepa` (clone of <https://github.com/gepa-ai/gepa>)
**Blog (optimize_anything)**: <https://gepa-ai.github.io/gepa/blog/2026/02/18/introducing-optimize-anything/>
**Quickstart**: <https://gepa-ai.github.io/gepa/guides/quickstart/>

## What is it (one-liner)

**G**enetic-**P**areto Reflective Prompt Evolution. Optimize any text
parameter (prompt, code snippet, agent harness, config, even SVGs)
against any evaluation metric, using:

1. **LLM-based reflection** on full execution traces (not just scalar
   rewards) to diagnose *why* a candidate failed.
2. **Pareto-aware evolutionary search** over textual mutations.

## Why it matters here

We have an LLM-based "Rewrite" prompt that's worse than the simpler
"Reset" template. We've already done a hand-driven prompt iteration
(v1 → v2) that didn't help, and a human-inspired v3 / v4 that may
also not help (because the dominant failure mode is rewriter LLM
hallucination, not a tractable prompt-fixable problem).

GEPA is exactly the tool for "we know there's a better prompt
somewhere; let optimization find it." Reported wins include:

- 90x cheaper than Claude Opus 4.1 at Databricks for enterprise agents.
- 35x fewer evaluations than RL (paper: 100–500 metric calls vs.
  5,000–25,000 for GRPO).
- ARC-AGI agent: 32% → 89% via architecture discovery.
- Cloud-scheduling policy beating expert heuristics by 40.2% cost
  savings.

## How it works (sketch)

GEPA maintains a population of candidates and iterates:

1. Sample a few candidates from the Pareto front.
2. Evaluate them on a small subset of the training set, capturing
   full execution traces.
3. A **reflector LLM** reads the traces (errors, output strings,
   side-info) and proposes mutations to the worst-performing
   candidates.
4. Re-evaluate; add winners to the population.

The Pareto-aware selection avoids collapsing to a single objective —
useful when the metric has multiple facets (accuracy + cost +
latency, etc.).

## API surfaces

### `gepa.optimize` — DefaultAdapter for single-turn QA

```python
result = gepa.optimize(
    seed_candidate={"system_prompt": "You are a helpful assistant..."},
    trainset=[{"input": "...", "additional_context": {}, "answer": "..."}],
    task_lm="openai/gpt-4o-mini",
    reflection_lm="openai/gpt-4o",
    max_metric_calls=50,
)
```

### `optimize_anything` — the most flexible entry point

```python
from gepa.optimize_anything import optimize_anything, GEPAConfig, EngineConfig
import gepa.optimize_anything as oa

def evaluate(candidate: str) -> tuple[float, dict]:
    # Run my system with `candidate` (e.g., the rewrite prompt),
    # score it, and return (score, side-info-dict).
    result = run_lic_eval(rewrite_prompt=candidate)
    return result.accuracy, {
        "stderr": result.errors,
        "trace_summary": result.trace_summary,
    }

result = optimize_anything(
    seed_candidate=open("context_compaction.txt").read(),
    evaluator=evaluate,
    objective="Maximize LiC accuracy via better rewrite prompts.",
    config=GEPAConfig(engine=EngineConfig(max_metric_calls=100)),
)
```

The key insight is the `(score, side_info)` return — GEPA's reflector
LLM reads the side_info, not just the score, when deciding what
mutations to propose.

### `GEPAAdapter` — full control

For batch-level control, trace capture, custom reflection-dataset
formatting. We'd only need this if `optimize_anything`'s flexibility
runs out.

## Concrete plan if we want to apply GEPA to Rewrite

**Goal**: optimize `context_compaction*.txt` against LiC accuracy.

**Seed candidate**: our current best Rewrite prompt (v1, or v4 if
that's our best by then).

**Evaluator**:

- Input: a candidate prompt string.
- Action: instantiate `AC3RewriteStrategy(compaction_prompt=<temp
  file containing the candidate>)`, run a tiny LiC eval (say 12
  problems × 2 prefixes = 24 cells, DeepSeek-V4-Flash, last-turn
  replay).
- Output:
  - `score` = accuracy
  - `side_info`:
    - 2-3 sample (prepared context, final answer, gold answer)
      tuples where the candidate failed
    - the spec_divergence / hallucination tags from our existing
      diagnoser
    - a short string identifying the dominant failure mode

The reflector LLM will then know *which* prompts produced spec_
divergence vs. hallucination, and can propose targeted mutations.

**Budget**: with each evaluation costing ~$0.01 (24 LiC samples at
DeepSeek-V4-Flash rates), 100 metric calls is ~$1. Wall-time is the
dominant cost (~5 min × 100 = ~8 hours). For an overnight session,
100 metric calls × 2-min cells with parallelism might be ~3 hours.

## When to use GEPA vs. hand-iterate

- Hand-iterate when there's a clean structural intervention to try
  (we did v2, v3 no-conv, v4 strict — informed by failure-mode
  analysis).
- Switch to GEPA when:
  - Hand iterations stop improving.
  - The failure modes are diffuse / not amenable to a single fix.
  - You can write a reliable evaluator + side-info function.

Tonight's call: try v3 + v4 first (cheap, ≤30 min). If neither
beats Baseline, set up GEPA as a follow-up overnight task.

## Caveats observed in docs

- `optimize_anything` is most flexible but you have to be careful
  about cache contamination across candidates — each evaluator call
  should be independent.
- "Use a strong reflection LM" — they suggest gpt-4o or stronger
  for the reflector even when task_lm is cheap. For us, that means
  we'd use gpt-5-mini or gpt-5.4 for reflection while DeepSeek-V4-Flash
  is the rewriter (task LM).
- 30–300 training examples is the recommended size. Our LiC suite at
  176 prefix-replicates total is in range.

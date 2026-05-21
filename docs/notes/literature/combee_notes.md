# Combee — notes

**Paper**: <https://arxiv.org/abs/2604.04247> / <https://arxiv.org/html/2604.04247>
**Title**: "Combee: Scaling Prompt Learning for Self-Improving Language Model Agents"
**Authors**: Li, He et al. (UC Berkeley + Stanford + Tensormesh + Gradient Network)
**Local copy**: `/tmp/combee_dl/combee.md` (markdownify conversion of the arxiv HTML)

## One-paragraph summary

Combee is a framework for **scaling parallel prompt learning** (think:
GEPA / ACE / "agentic context engineering" loops). The core finding
is that *naively* parallelizing — running N agents in parallel,
collecting all N reflections, and asking one aggregator LLM to fold
them into a single context update — causes **context overload**:
the aggregator produces fewer and lower-quality updates as N grows,
even when all reflections fit in the context window. Combee fixes
this with three orthogonal additions:

1. **Parallel scan aggregation** — hierarchical aggregation. Instead
   of N→1 in one shot, split into √N groups of √N reflections each,
   aggregate within each group, then aggregate the √N intermediate
   updates. Same total work, but each aggregator call sees fewer
   reflections.
2. **Augmented shuffling** — duplicate each reflection p times
   (default p=2) before dispatching to the aggregator, then shuffle.
   Gives each reflection multiple chances to be incorporated.
3. **Dynamic batch size controller** — profile epoch delay at a few
   candidate batch sizes, fit a power-law `T = A·bs^(-α)`, pick the
   largest batch size still on the steep part of the curve.

Reported: up to 17× speedup over previous methods at comparable or
better accuracy across AppWorld / Terminal-Bench / Formula / FiNER.

## Is Combee the right answer for our GEPA latency problem?

**Probably not, for this specific use case.** Here's the analysis.

### Where the latency actually lives in our setup

For optimizing the AC3-Rewrite compaction prompt against LiC, the
GEPA outer loop is:

```
for iteration in range(max_iter):
    candidate = mutate(current_best)
    score, side_info = evaluate(candidate)   # ← the long step
    if reflection_lm_decides_to_keep(score, side_info):
        current_best = candidate
```

`evaluate(candidate)` runs the candidate prompt as the rewriter on N
LiC problems and reports accuracy + per-failure summaries. **One
evaluation takes ~10-15 minutes** at our usual throttled throughput
(48 problems × 1 turn × ~30s/turn at MC=4). For 50 GEPA candidates
serial: ~12 hours. Too long.

Combee accelerates the *aggregator* step (the "reflection LM
decides what to keep") under high parallelism. But our aggregator is
trivial — it sees only 1 score + 1 side_info per evaluated
candidate. We're nowhere near the "many parallel reflections per
iteration" regime that Combee is designed for.

The actual bottleneck is **per-candidate evaluation latency**, not
aggregation. The fix is **parallelizing the evaluator** — and GEPA
already exposes `num_threads` for that. Setting `num_threads=8`
gives us ≈8× the throughput, putting 50 GEPA iterations within reach
in ~1.5-2 hours.

### When Combee WOULD be the right answer for us

If we were doing **iterative prompt evolution where each iteration
consumes many (say 50+) per-task reflection traces and asks one LLM
to merge them into the new prompt**, Combee's parallel-scan
aggregation would help. Our setup doesn't have that structure —
GEPA's reflection LM consumes one (candidate, score, side_info)
tuple at a time.

### Useful side-takeaways from Combee for us

- **Augmented shuffling** — duplicating each reflection 2× before
  feeding to the aggregator. This is a one-line trick we could add
  to our GEPA setup if we ever decide to batch multiple per-sample
  failure cases into a single reflection prompt. Cheap insurance.
- **"Context overload" is a real LLM failure mode** that worsens
  with input length, even within the model's context window. This is
  consistent with our own R3 finding that the rewriter LLM hallucinates
  *more* when given the full conversation. The
  `rewriter_LLM_hallucination=63%` attribution in our diagnoses is
  the same family of failure.
- **Power-law batch-size profiling** is a clean trick for picking a
  parallelism level. We empirically arrived at MC=4 by trial and
  error after hitting 429s — Combee's approach would have nailed it
  in 2-3 calibration runs.

## Decision

Skip Combee for the rewrite-prompt GEPA run. Use GEPA's built-in
`num_threads` parallelism instead. Re-evaluate Combee if and when we
build a "learn from many parallel agent trajectories" pipeline
elsewhere in the project (e.g., a memory-cheatsheet learner).

## Reference links

- Combee paper: <https://arxiv.org/abs/2604.04247>
- GEPA (which Combee builds on): <https://arxiv.org/abs/2507.19457>
- ACE (the other framework Combee scales): "Agentic Context
  Engineering: Evolving Contexts for Self-Improving Language Models"
- Background — parallel scans / prefix sum: Blelloch 1990
- Background — augmented self-consistency: Wang et al. 2022

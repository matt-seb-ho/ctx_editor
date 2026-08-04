# Depth Study: ACON — Agent Context Optimization

**Bibkey**: kang2026acon
**arXiv**: 2510.00615
**Venue**: ICML 2026
**Authors**: Minki Kang, Wei-Ning Chen, Dongge Han, Huseyin A. Inan, Lukas Wutschitz, Yanzhi Chen, Robert Sim, Saravan Rajmohan (Microsoft)
**GitHub**: https://github.com/microsoft/acon
**Access status**: Abstract + ar5iv full HTML read; numeric tables extracted from rendered HTML. Direct PDF binary not parsed. All numbers and quotes sourced from ar5iv.labs.arxiv.org rendering; see [UNVERIFIED] tags where exact section location is uncertain.

---

## 1. What ACON Compresses and HOW

**What it compresses**: Both (a) the accumulated interaction history and (b) individual long observations at each agent step.

**Mechanism — two compression modes**:

- **History compression** (triggered when accumulated history length exceeds threshold T_hist): an LLM compressor takes the *entire accumulated history* as input and outputs a compact natural-language summary that replaces the raw history. Eq.3 in the paper: `h_t^compressed = f_compress(h_{1:t-1}, P)` where P is the compression guideline prompt.
- **Observation compression** (triggered when a single observation exceeds T_obs): the compressor takes the raw observation and outputs a condensed version. Eq.4: `o_t^compressed = f_compress(o_t, P)`.

Both modes use the *same* guideline P but are applied at different granularities.

**Guideline optimization — how guidelines are created and refined**:

The compression guideline P is a natural-language prompt that directs the compressor LLM. ACON does NOT fine-tune any model; instead it optimizes P through two alternating steps using task feedback:

1. **Utility-maximization (ut) step**: Collect a *contrastive* set of tasks — those where the uncompressed agent succeeds but the compressed agent fails. For each contrastive trajectory, an optimizer LLM receives (full trajectory, compressed trajectory) and produces natural-language feedback identifying which omitted signals caused the failure. This feedback acts as a "textual gradient." The optimizer LLM then proposes updated guideline candidates; the best candidate (by held-out evaluation) is selected as the new P. Paraphrase of paper description: "contrastive task feedback" and "compression guideline optimization in natural language space" (verbatim from abstract/intro — exact section labels not confirmed from ar5iv render).

2. **Compression-maximization (co) step**: On tasks where compression already succeeds, the optimizer queries what information was actually used by the agent, to encourage shorter compressions while preserving correctness. This alternating ut ↔ co loop continues for several optimization rounds (details in Algorithm 1 / Figure 3).

**Key design properties**:

- "entirely gradient-free" (verbatim): no parameter updates; only guideline text is updated.
- Model-agnostic: works with closed-source APIs since only prompts change.
- The optimized compressor can be **distilled** into a smaller model (Qwen3-14B, Qwen3-8B, Phi-4) to reduce runtime cost, with >95% of teacher compressor performance retained (Figure 4, Section 4.3).

---

## 2. How ACON Handles Environment / Tool State Across Turns

ACON is explicitly designed for stateful long-horizon agentic tasks. Key claims (Introduction, paraphrased from ar5iv):

> The compressor is instructed to retain "factual history, action-outcome relationships, evolving environment states, success preconditions, and future decision cues." [Paraphrase — these items are listed in the Introduction as the critical signals ACON targets; verbatim list not confirmed.]

Implementation:

- **Persistence of latest signal**: Appendix B.3 (compression hyperparameters) states the method "keeps the last action, observation pair to preserve the latest information" — i.e., the most recent action-outcome is always retained verbatim regardless of compression.
- **Contrastive feedback enforces state retention**: The optimization loop specifically detects when a compressed history drops a stateful token (e.g., a stored access_token, a username/password, a required precondition) that caused a downstream failure. Qualitative case studies in Appendix C show compressed histories correctly retaining stateful API credentials and call sequences.

**Benchmarks**:

| Benchmark | Domain | # Tasks | Agent/Compressor LLM |
|-----------|--------|---------|----------------------|
| AppWorld | Stateful app-world agent (file ops, APIs) | 168 test-normal tasks | gpt-4.1 |
| OfficeBench | Office automation agent | ~? tasks | gpt-4.1 |
| 8-objective QA | Multi-objective QA | ~? tasks | gpt-4.1 |

**Headline numbers** (Table 1, AppWorld, gpt-4.1 agent):

| Variant | Accuracy | Peak tokens (×10³) | Token reduction |
|---------|----------|-------------------|-----------------|
| No compression | 56.0% | 9.93 | baseline |
| ACON (ut) | 51.2% | 7.17 | ~28% |
| ACON (ut→co) | **56.5%** | 7.33 | **~26%** |
| LLMLingua | lower (exact omitted) | higher reduction, worse acc | — |

ACON (ut→co) on AppWorld matches or slightly exceeds no-compression accuracy while cutting peak tokens ~26%.

**OfficeBench** (Table 2a):

| Variant | Accuracy | Peak tokens (×10³) | Dep (×10⁶) |
|---------|----------|-------------------|------------|
| No compression | 76.84% | 7.27 | 4.43 |
| ACON (ut→co) | 72.63% | 4.54 | 1.91 |

~37% peak token reduction with ~4 pp accuracy drop.

**8-objective QA** (Table 2b):

| Variant | EM | F1 | Peak tokens (×10³) |
|---------|----|----|-------------------|
| No compression | 0.366 | 0.488 | 10.35 |
| ACON (ut) | **0.373** | **0.494** | 4.71 (~54% reduction) |
| ACON (ut→co) | 0.335 | 0.458 | 4.65 |

ACON (ut) slightly *exceeds* no-compression EM/F1 on this benchmark while cutting tokens ~54%.

**Small-agent results** (Section 4.4 / Figure 5):
- Qwen3-14B agent on AppWorld: 26.8% → 33.9% accuracy with ACON distilled compressor (~46% relative gain cited in abstract).
- Qwen3-14B agent on 8-objective QA: EM 0.158 → 0.197.

---

## 3. Does ACON Resolve Inter-Turn References / Entanglement Before Compressing?

**Short answer: NO — ACON does not resolve or decontextualize inter-turn references before compressing. It compresses whole-history segments and relies on learned guidelines to preserve whatever cross-turn dependencies matter for task success.**

**Evidence**:

1. **Unit of compression is the accumulated history or a single raw observation** — neither approach involves first parsing coreference links, resolving pronouns, or rewriting later turns to be self-contained. The compressor ingests the raw history as a flat sequence and summarizes it. Inter-turn references survive only if the compression guideline (learned through failure analysis) happens to retain the referents.

2. **The optimization loop is a task-level fallback, not a reference-resolution step**: When a dropped cross-turn dependency causes a task failure, the contrastive feedback loop updates the guideline to say "retain this type of information." This is a *learned heuristic* for what tends to matter, not a structural resolution of inter-turn entanglement. If a new task type has a novel entanglement pattern not seen during training, the guideline may not cover it.

3. **Observation compression is per-observation** (Eq.4): Individual long observations are compressed independently. If a later turn's action depends on a detail from an earlier observation that was independently compressed away, that link is broken — the guideline must have been optimized to retain it, or it is lost.

4. **History compression operates on raw accumulated history** (Eq.3): The compressor does not first rewrite the history to make turns self-contained, then summarize; it summarizes directly. This means entanglements (where turn T+1 uses an undefined pronoun/variable whose referent was in turn T) are preserved only if the summary happens to retain both the referent and the dependent mention. Summarization that shortens either turn may sever the link.

**Bottom line for our positioning**: ACON is *compress-then-hope* (the guideline optimization is the "hope" mechanism). Our method is *decontextualize-then-edit*: we explicitly resolve inter-turn references (making each retained segment self-contained) before any pruning decision is made. This is a structural difference, not just a better heuristic.

---

## 4. Stated Limitations and Failure Cases on Multi-Turn Dependency

From Appendix A (Limitations & Future Work) and Section 3 / Appendix C (paraphrased from ar5iv):

1. **Compressor overhead and KV-cache disruption**: Invoking the compressor LLM adds extra cost and latency. History compression can *increase* total API cost because it breaks the KV-cache for the compressed history, forcing re-computation of keys/values for the summary. Future work: KV-cache-level compression/eviction to avoid re-computation.

2. **Over-aggressive compression breaks cross-turn dependencies**: Combining both history and observation compression can produce substantial performance degradation relative to using only one compression type (Appendix C). This is the primary multi-turn failure mode: the compressor drops critical cross-turn signals (variable states, credentials, preconditions) and subsequent agent steps fail.

3. **Model coverage unverified**: Experiments are primarily on GPT-family models (gpt-4.1). Generalization to Gemini, Claude, or large open-source models is explicitly flagged as unverified. [UNVERIFIED: exact quote; sourced from Appendix A summary.]

4. **Sparse reward / optimization difficulty**: The original objective (maximize agent success) is hard to optimize directly. ACON addresses this via the contrastive feedback loop, but the paper notes this is an approximation; full RL-style optimization remains challenging.

5. **No explicit handling of novel entanglement patterns**: The guideline optimization is trained on a fixed task distribution. Novel tasks with inter-turn dependency structures not seen during optimization may expose blind spots.

---

## 5. Is ACON a Fair/Strong Comparator on the Statefulness Axis?

**What we would need to run it**:
- Access to a capable LLM API (gpt-4.1 was used; distilled Qwen3-14B/Phi-4 also viable) for the compressor.
- A training set of agent trajectories on our stateful benchmark tasks to run the contrastive optimization loop (guideline optimization requires task-level success/failure feedback, so the benchmark tasks must be run with a working agent).
- Threshold hyperparameters T_hist and T_obs tuned per task type (AppWorld used T_hist=4096, T_obs=1024).
- GitHub: https://github.com/microsoft/acon (code available).

**What result would distinguish our method from ACON**:

The critical test is a task set with *novel entanglement patterns* — cases where a later turn uses an entity or quantity whose definition was only ever stated in an earlier turn, in a form that a summarizing compressor cannot retain without explicit reference resolution. On such tasks:

- ACON's guideline (trained on the existing distribution) may produce a summary that retains the referent by chance or by a learned heuristic — but for novel patterns outside the training distribution, the guideline has no mechanism to guarantee retention.
- Our method decontextualizes first (rewrites turn T+1 to be self-contained by inlining the referent from turn T before pruning), so the entanglement is resolved regardless of distribution.

A clean experiment: hold out a set of tasks specifically designed to maximize cross-turn coreference density and evaluate both methods. ACON's contrastive loop is trained on the same set (in its training split), so the fair comparison uses a test split with structurally similar-but-novel entanglement patterns. We predict ACON's accuracy degrades more than ours on the high-entanglement dial position.

---

## Positioning vs Ours

- **Does ACON resolve references before compressing?** No. It compresses raw accumulated history and relies on a task-feedback-optimized guideline to preserve what matters. This is principled but distribution-dependent.
- **Our structural wedge**: Decontextualize-then-edit guarantees that each retained segment is self-contained by construction. ACON's guarantee is empirical (the guideline was optimized to avoid the failures it has seen). On in-distribution stateful tasks, ACON is competitive or better (it has been specifically trained to handle AppWorld-style state). On tasks with novel entanglement patterns, our structural guarantee is the differentiator.
- **Statefulness-axis comparator verdict**: ACON is the strongest available published comparator on the statefulness axis. It is specifically designed for stateful agentic settings, uses contrastive task feedback to preserve action-outcome relationships, and has strong AppWorld/OfficeBench numbers. It is a fair and strong comparator — not a strawman. Beating it on a statefulness benchmark requires our method to show: (a) comparable compression quality on state retention, AND (b) better handling of entangled references that ACON's learned guideline misses.
- **Overlap with our approach**: Both methods use LLM-based compression and both target retention of task-critical information. The difference is structural: ACON optimizes *what to retain* via failure-signal feedback; we resolve *why later turns depend on earlier ones* via explicit reference resolution, then decide what to retain. These are complementary and could in principle be combined, but the ablation that separates them is the entanglement-dial experiment.
- **Not covered by ACON**: Our method also handles the case where the assistant has committed to a wrong assumption that the user did not state — i.e., errors introduced by the assistant's own (incorrect) reasoning. ACON's compressor would preserve such erroneous content because it looks like a factual statement in the history. Our analyzer specifically targets removal of assistant-introduced hallucinations and incorrect assumptions. This is an orthogonal axis ACON does not address.

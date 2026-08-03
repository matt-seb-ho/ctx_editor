# Context-management landscape — synthesis (M2)

**Date:** 2026-08-03. **Effort:** `research/context_mgmt_survey/` (deli autonomous run).
**Inputs:** `findings/cluster{1..5}_*.md` (summarization, memory-agents, retrieval, pruning, evals+scooping).
**Purpose:** answer Matthew's question — *are we over-indexing on the Huang assistant-omit baseline
(a strawman)?* — by mapping the real incumbents, each one's failure axis, and our novelty.

---

## TL;DR

1. **We are not attacking a strawman — but we should re-center the framing.** Assistant-omit (Huang
   et al.) is a clean *academic* baseline, but the *production* incumbent is **summarization /
   compaction** (Anthropic Compaction API, Cline auto-compact, Cursor `/summarize`, and the learned
   line LLMLingua-*/MEMENTO/ACON). Foreground summarization; keep assistant-omit as the minimal
   baseline. Then it reads as "we stress-test the whole family," not "we beat one MIT paper."
2. **Every family shares one structural flaw:** they **prune or compress *before* resolving the
   references embedded in the history** ("compress/drop-then-continue"). Our decontextualize-then-edit
   inverts the order (**resolve-then-prune**), which is exactly why it should survive both knobs.
3. **The strawman worry actually strengthens the paper:** the Huang paper *itself* names its failure
   case "Follow-up without Feedback" (~33% of turns = the entanglement failure) and *explicitly scopes
   out* stateful tasks ("truly stateful tasks may behave differently") and calls blind omission "too
   coarse," listing "preserve only the relevant assistant responses" as future work. We are building
   the eval that measures the two gaps the baseline's own authors flagged but did not study.
4. **Scooping: we are clear.** No prior benchmark exposes **entanglement** as a controllable,
   faithfulness-gated knob *and* pairs it with a **statefulness** knob to compare context-management
   strategies. Closest: StructFlowBench (categorical, instruction-following, no state), LiC (our base;
   shards self-contained ⇒ ~0 entanglement by design), MT-Eval (fixed taxonomy, user→prior-user).

---

## The two-axis framing

- **Entanglement** — how much a later *user* turn depends on / refers back to the *assistant's* prior
  output ("the second option isn't working", "reverse that"). High entanglement ⇒ blindly dropping
  assistant turns destroys interpretability.
- **Statefulness** — how much persistent *environment* state must be tracked across turns (τ²-bench
  DB/tool state). High statefulness ⇒ any lossy compression/eviction silently corrupts the state
  thread.

Our claim: each context-management family is robust on at most one axis and breaks on the other; ours
is designed to survive both.

---

## Method families × failure axes (cross-cluster matrix)

| Family | Representative methods | Core mechanism | Breaks on ENTANGLEMENT because… | Breaks on STATEFULNESS because… |
|---|---|---|---|---|
| **Drop / omit** (baseline family) | **Huang assistant-omit**; ConcatUser | role filter — delete assistant turns | referents the user points back to are gone (Huang's own "Follow-up w/o Feedback", ~33%) | assistant turns carry the running state; deleting them severs it (our DB pilot: omit 32% vs 44%) |
| **KV-cache eviction** | H2O, StreamingLLM, Scissorhands, SnapKV, FastGen, PyramidKV | drop KV pairs by attention/position/layer budget | low-attention tokens ≠ low future-reference value; anchors evicted | eviction signals are stationary/local; multi-turn state transitions violate the assumption |
| **Summarization / compaction** (production incumbent) | Recursive-summ., LLMLingua-{1,2}, LongLLMLingua, MEMENTO, ACON; Anthropic/Cline/Cursor | replace history with a summary/compressed tokens | summary folds away the exact assistant phrasing later turns dereference | summarizers optimize task-relevance/efficiency, not verbatim reproduction of state-critical values |
| **Retrieval-over-history** | MemoryBank, RAGate, mtRAG (+ rewrite: CANARD, QReCC, CONQRR, ConvGQR, Choi decon.) | fetch relevant past turns on demand | elliptical/opaque queries have no retrievable signal; "lost-in-the-middle" hits even good hits | state is a *running function of all history*, not any single retrievable fragment |
| **External memory agents** | MemGPT/Letta, Generative Agents, A-MEM, Mem0, MemoryOS, MemOS, HiAgent | page turns to an external store; write facts/summaries | archival abstracts turns into summaries/facts/embeddings *before* saving ⇒ reference chain overwritten | consolidation summarizes exactly the action-observation logs that encode sequential state |
| **Reset / consolidate** | ERGO (entropy-triggered reset) | detect degradation, then lossy consolidate | consolidation is still a lossy rewrite; specific assistant outputs discarded | accumulated state must be explicitly preserved or is lost in the reset |
| **Ours** | decontextualize-then-edit | **resolve references against assistant turns, THEN surgically prune** | references are inlined *before* pruning ⇒ nothing to dangle | explicit state-preserving edit pass keeps state-critical turns |

**Unifying diagnosis.** Read the "breaks on entanglement" column top-to-bottom: every incumbent
commits an irreversible lossy operation (drop / evict / summarize / retrieve-key / archive / reset)
*before* the reference structure has been resolved. That ordering is the shared root cause. Our single
structural move — **resolve-then-prune** — is what the whole survey motivates.

---

## Scooping & novelty (from cluster 5)

- **StructFlowBench** (ACL-F 2025, arXiv 2502.14494) — *closest*. Uses 6 inter-turn relationship
  types as generation parameters. But: instruction-following *compliance*, not context-management
  degradation; categorical not continuous; no statefulness axis; no faithfulness gate.
- **LiC / Lost-in-Conversation** (Laban et al., arXiv 2505.06120) — *our base platform*. Shard count
  is a dial, but shards are **self-contained ⇒ entanglement ≈ 0 by construction**; the "concat/omit
  exploit" trivially recovers single-turn performance. That exploit is precisely what an entanglement
  knob closes. (Note: Philippe Laban is LiC's first author — this is the line the project extends.)
- **MT-Eval** (EMNLP 2024) — 4 fixed interaction types (recollection>refinement>follow-up>expansion);
  dependency is mostly user→prior-*user*, taxonomy not a parametric dial, no method comparison.

**Novelty claim (drop-in wording):** *"Unlike prior work that categorizes interaction types post-hoc
(MT-Eval, StructFlowBench) or controls only the spread of underspecification across turns (LiC), we
expose entanglement and statefulness as independently dial-able, faithfulness-gated construction
parameters, and use them to measure how context-management methods scale as both dimensions increase."*

---

## Positioning recommendation (answering the strawman worry)

1. **Re-center the incumbent.** Lead the related-work/motivation with **summarization/compaction** as
   the method users actually run (cite Anthropic Compaction API + Cline + Cursor as evidence it's
   deployed), then present assistant-omit (Huang) as the clean minimal baseline and KV-eviction /
   memory-agents / retrieval as the broader family. This alone defuses "you beat one MIT paper."
2. **Use Huang's own limitations as our motivation.** Quote that the paper flags Follow-up-without-
   Feedback and scopes out stateful tasks and calls blind omission too coarse. We formalize + measure
   those two gaps → entanglement and statefulness knobs.
3. **Method axis for the experiments** (comparators to run on the gradable benchmark, spec'd in
   `docs/plans/entanglement_benchmark_spec.md`): `accumulate-all` (upper-context baseline) ·
   `assistant-omit` (Huang) · `summarize` (recursive-summ. as the production-representative) ·
   *optionally* a retrieval-over-history condition · **`decontextualize-then-edit` (ours)**. Consider
   adding **ACON** as a strong learned-compression comparator on the statefulness axis (it's the
   best-in-class stateful compressor we found).
4. **Two-axis figure.** Rows/panels = {low, high} statefulness; x = entanglement level; one line per
   method. Predicted: omit collapses with entanglement; summarize erodes with statefulness (and with
   fine-grained referents); ours holds on both.

---

## Open items → next milestones

- **M3 (verify + refute):** citation-audit all ~40 URLs; run an adversarial "is this still a strawman?"
  pass (strongest counter: "summarization with a good state-preserving prompt already handles both" —
  test whether that collapses into a weak form of ours).
- **M4 (depth):** deep-read the top-2 incumbents — the **Huang** paper (exact method/results to cite)
  and **ACON** (is it a comparator or an orthogonal compressor?). Also read **StructFlowBench** closely
  for the novelty-distinction paragraph.
- **M5 (deliverable):** `related_work.bib` (built alongside this doc) + a one-page recommendation and a
  related-work paragraph draft for the entanglement paper; fold into `docs/entanglement_knob_findings.md`.

**Provisional answer to Matthew's question:** No, not a strawman — *provided* we re-center on
summarization/compaction as the incumbent and frame the contribution as the two-axis knob (entanglement
× statefulness) rather than "assistant-omit is bad." The survey gives us the citations and the unifying
"resolve-then-prune vs. prune-then-hope" argument to do exactly that.

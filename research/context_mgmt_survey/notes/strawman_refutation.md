# Adversarial strawman-refutation (M3)

**Date:** 2026-08-04. **Effort:** `research/context_mgmt_survey/`. **Prereq:** `notes/context_mgmt_survey.md`.
**Purpose:** red-team our own contribution. For each "you're beating a strawman / you're scooped /
this is contrived" objection a reviewer could raise, state it in its strongest form and rebut it with
evidence from the survey. Flag the one objection that needs an *experiment*, not an argument.

Severity = how much damage it does if unanswered. ★★★ = paper-threatening.

---

### O1 ★★★ "Summarization with a state-preserving prompt already handles both axes — your method is unnecessary."

**Steelman.** Just instruct the summarizer: "when you compact, preserve every referent a later turn
might point to and every piece of environment state." A good LLM summary then keeps the entangled
content and the state, so summarize ≈ our method, minus the machinery.

**Rebuttal.**
1. **It collapses *into* our method, without the guarantees.** A summarizer told to "preserve the
   referents later turns will dereference" is doing decontextualization — resolving inter-turn
   references before compressing. That IS resolve-then-prune. The difference is our version is
   (a) *surgical* (edits the offending spans, doesn't regenerate the whole history — no
   re-hallucination of untouched content), and (b) *faithfulness-gated* (we verify with the
   recoverability instrument that the rewrite is grounded in the assistant turn; a generative summary
   has no such check). So the objection doesn't refute us — it describes an uninstrumented, unguaranteed
   version of us and concedes the mechanism.
2. **Production evidence it does not happen by default.** The shipped summarizers (Cursor `/summarize`,
   Cline auto-compact, Anthropic Compaction API) discard prior content blocks and rely on the summary;
   community reports document code artifacts silently dropped, and Anthropic's docs say prior blocks
   are ignored unless custom instructions request specifics. "Just prompt it better" is exactly the
   per-domain custom-instruction burden our method removes.
3. **Lossy-generative vs. surgical is measurable.** Our recoverability instrument (from the
   entanglement effort) *quantifies* whether a referent survives a transform. This objection is
   therefore not a debate — it is **an ablation we should run** (see "Experiment E1" below).

**Verdict:** strongest objection; convert to an experiment, don't just argue.

---

### O2 ★★ "Assistant-omit is one niche Feb-2026 preprint — why build a paper around beating it?"

**Steelman.** Huang et al. is a single recent arXiv preprint; centering a benchmark on refuting it is
narrow.

**Rebuttal.** We do **not** center on it. The contribution is the **entanglement × statefulness knob**;
assistant-omit is the clean *minimal* baseline, and the *production* incumbent we foreground is
summarization/compaction (§positioning). Moreover Huang is not an adversary — it *motivates* us: it
coins "context pollution," names its own failure case "Follow-up without Feedback" (~33% of real turns),
scopes out stateful tasks, and calls blind omit "too coarse" with "preserve only the relevant assistant
responses" as future work. We build the eval that measures the two gaps its authors flagged.

---

### O3 ★★ "Entanglement is contrived — you construct artificial dependencies that don't occur in practice."

**Steelman.** Real users restate their intent; hand-built referential turns are a synthetic artifact.

**Rebuttal.** Entanglement is a *naturally occurring* variable — it is precisely Huang's "Follow-up
without Feedback," measured at ~33% of turns in in-the-wild WildChat + ShareLM technical
conversations. Statefulness is intrinsic to agentic/coding tasks (τ²-bench DB/tool state). Our
construction does not invent the phenomenon; it makes an existing variable *controllable and
faithfulness-gated* so methods can be compared along it. The faithfulness gate is exactly the guard
against "contrived": a constructed turn only counts if an independent model can still recover the
intent *with* the assistant turn present (informed recoverability high).

---

### O4 ★★ "Retrieval or external memory already solves entanglement — fetch the referenced turn."

**Steelman.** Don't drop assistant turns; retrieve the relevant one on demand (MemGPT, MemoryBank, RAG).

**Rebuttal (from clusters 2-3).** Two structural failures: (a) **no retrievable signal** — elliptical/
opaque references ("reverse that", "apply the same fix") carry no keywords or embedding to match on;
QReCC's 19 vs 75 F1 system-vs-human gap and CONQRR's absent RL gradient on opaque ellipsis are direct
evidence. (b) **state is not a fragment** — accumulated environment state is a running function of the
*entire* history, not stored in any single retrievable turn (τ-bench: you cannot retrieve "the current
reservation" — you must replay the modifications). "Lost in the middle" compounds even successful hits.

---

### O5 ★ "Your method is just conversational query rewriting / decontextualization (Choi 2021, CANARD)."

**Steelman.** Decontextualization (Choi, TACL 2021) and query rewriting (CANARD, QReCC, CONQRR, ConvGQR)
already resolve references into standalone form. You renamed prior art.

**Rebuttal (from cluster 3).** Same *primitive*, different *operation and goal*. Query-rewriting
resolves a reference to produce a one-shot search key that improves retrieval over a **static corpus**,
then discards the resolution. We resolve references to enable **safe pruning of live, mutable
conversation history**, and we **persist** the resolved rewrite into the ongoing context so deleting the
original turn preserves semantics. We additionally add the faithfulness gate and the statefulness axis,
neither of which exists in that line. Cite Choi et al. as the acknowledged inspiration and draw this
distinction explicitly — it strengthens, not weakens, the framing.

---

### O6 ★ "Long context windows are huge now — just keep everything (accumulate)."

**Steelman.** With 1M-token windows, why manage context at all?

**Rebuttal.** Keeping everything *is* the disease, not the cure: it is the pollution regime Huang
documents (over-conditioning on early wrong outputs propagates errors) and where lost-in-the-middle
degrades retrieval of the relevant turn even when it fits. Bigger windows do not remove pollution/rot;
they can worsen it. Our own prior LiC results show accumulate degrading across turns.

---

### O7 ★★ "The gains are an LLM-judge artifact."

**Steelman.** Recoverability and quality are judged by an LLM; the effect may be judge idiosyncrasy.

**Rebuttal.** From the entanglement effort: faithfulness (informed recoverability) is **judge-robust**
across two independent judge families (gpt-5.4-mini and gpt-4o agree on the contrast). And the planned
accuracy sweep runs on a **deterministically gradable** artifact-refinement benchmark
(`docs/plans/entanglement_benchmark_spec.md`) — the headline metric needs no judge at all.

---

### O8 ★★ "StructFlowBench already controls inter-turn relationship type — you're scooped."

**Steelman.** StructFlowBench (ACL-F 2025) uses 6 inter-turn relationship types as generation
parameters — an entanglement knob already exists.

**Rebuttal (from cluster 5).** Four concrete differences: (1) it targets instruction-following
*compliance*, not *context-management degradation* — it never compares accumulate/omit/summarize/edit;
(2) its dial is *categorical* (which of 6 types), not a continuous, gradable entanglement level;
(3) it has *no statefulness axis*; (4) it has *no faithfulness gate*. Cite-and-distinguish; it is the
closest prior work but does not do what we do.

---

## The one thing to run, not argue — Experiment E1

**O1 is the only paper-threatening objection that cannot be settled by citation.** Add a
**state/reference-preserving summarize** condition to the method axis of the gradable benchmark:

- `summarize-naive` — generic "summarize the conversation so far."
- `summarize-guided` — summarizer explicitly instructed to preserve every referent later turns may
  point to and all environment state (the steelman of O1).
- `decontextualize-then-edit` (ours).

**Predicted result that kills O1:** `summarize-guided` improves over `summarize-naive` but (a) still
trails ours on the entanglement and statefulness axes because generative summarization cannot guarantee
verbatim referent/state preservation, and (b) whatever gains it gets come from doing an
un-instrumented resolve-then-prune — i.e. it validates our mechanism. Either outcome is a win: it
either underperforms (ours is better) or it *is* our mechanism without the guarantees (ours is the
principled version). Fold `summarize-guided` into the sweep in `entanglement_benchmark_spec.md`.

## Net verdict

Not a strawman. Seven of eight objections are answerable from the survey today; O1 needs the
`summarize-guided` ablation (E1) — cheap to add to the already-spec'd benchmark and decisive either way.

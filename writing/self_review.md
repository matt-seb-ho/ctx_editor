# Self-Review: Externalized Executive Function via Self-Aware Context Curation

**Venue:** COLM 2026
**Review Date:** 2026-03-26
**Reviewer Stance:** NeurIPS/ICML/COLM reviewer, moderate-to-critical

---

## Summary

The paper proposes "self-aware context curation" to address multi-turn LLM performance degradation (context pollution). A separate analyzer agent reads the conversation in two steps—extracting user intent without assistant messages, then comparing against the full conversation—and rewrites the context to remove harmful content. The key empirical finding is that assistant messages act as a "cognitive hazard" that degrades even independent reviewer models. Results are shown across LiC (controlled), WildChat (real conversations), CollabLLM, and tau2-bench (agentic).

---

## Strengths

1. **Clear problem and strong motivation.** The framing of context pollution as a self-regulation deficit, connected to executive function, is compelling and well-articulated. The cognitive hazard finding (Table 3) is genuinely surprising and important.

2. **Breadth of evaluation.** Testing across four settings (LiC, CollabLLM, WildChat, tau2-bench) with increasing statefulness is a strength. The tau2-bench result (0% for omission) is dramatic and clearly demonstrates the need for curation over removal.

3. **Honest about limitations.** The paper doesn't oversell—it acknowledges that simple baselines are strong on LiC, and that context pollution isn't the dominant tau2-bench failure mode.

4. **Cognitive science framing is appropriate.** The connection to executive function and the parallel to Tree of Thought's System 1/2 framing are well-drawn without overclaiming.

---

## Weaknesses and Requested Changes

### Major Issues

**M1. The abstract is still too long and dense.**
The abstract runs approximately 200 words, which is fine for many venues, but it packs in too many specific numbers. The opening is good (context pollution/rot), but the second half reads like a compressed results section. Consider: state the problem, the method, the key insight (cognitive hazard), and ONE or TWO headline results. Move the rest to the introduction.

**M2. Figures are placeholders.**
Figures 1 and 2 are boxed text descriptions. These are critical—a good Figure 1 showing a concrete example of context pollution (e.g., a 3-turn math conversation where the assistant anchors on a wrong interpretation) would dramatically improve accessibility. Figure 2 should be a proper architecture diagram showing the data flow: conversation → Subtask 1 (user msgs only) → spec → Subtask 2 (spec + full conv) → artifact → intervention. The paper is hard to follow without these.

**M3. The "self-aware" terminology is a liability.**
Despite the caveats, calling this "self-aware context curation" invites unnecessary pushback from reviewers. The system is not self-aware in any meaningful sense—it's an external agent with structured data flow. Consider dropping "self-aware" from the method name and using it only in discussion. "Context curation via externalized executive function" or simply "structured context curation" would be more defensible.

**M4. WildChat evaluation relies entirely on LLM-as-judge with acknowledged format bias.**
The format bias caveat is honest, but it undermines the strongest result in the paper (84-86% win rates). The paper should:
- Report loss rates (not just win rates) to show asymmetry
- Consider a human evaluation on a small subset
- Report tie rates explicitly (mentioned but not tabulated)
- Discuss whether 83% win rate for Reset (which intervenes 100% of the time) vs 86% for Gated Reset (72%) is statistically meaningful given the sample size

**M5. Sample sizes are very small for the claims being made.**
19-25 per LiC task, 20 tau2-bench tasks, 30 WildChat conversations. No confidence intervals or significance tests are reported anywhere. The tau2-bench baseline range is "45-55%" which is a 10pp range on 20 samples—this is enormous variance. The paper should at minimum report confidence intervals for key comparisons, or conduct paired tests (e.g., McNemar's test on per-sample correctness).

### Minor Issues

**m1. The paper title could be clearer.**
"Externalized Executive Function via Self-Aware Context Curation" is jargon-heavy. Something like "Curing Context Pollution: How Structured Self-Analysis Rescues Multi-Turn LLM Performance" would be more accessible, though admittedly less academic.

**m2. CollabLLM section feels underdeveloped.**
The CollabLLM results are promising (especially BigCodeBench +20pp) but get minimal discussion. The conversation-aware judge is an interesting methodological contribution that deserves more explanation—even a sentence or two about what it evaluates differently than pass_rate.

**m3. The "experience accumulation" / Dynamic Cheatsheet aspect is undersold.**
Memory closing 65% of the gap to hard attention on database is a strong result for a test-time learning method. But the memory results are split between Tables 2 and 6 with minimal connective tissue. Consider a brief paragraph that synthesizes the memory story across settings.

**m4. Missing related work: context compression and summarization.**
The paper doesn't discuss context compression/summarization methods (e.g., LLMLingua, context distillation) which address a related problem. These compress context for efficiency rather than correctness, but a reviewer familiar with that area will wonder about the connection.

**m5. Gated Reset vs. Reset: the gating decision itself is not analyzed.**
When does gating make the wrong call? False positive rate (unnecessary interventions) and false negative rate (missed interventions) would strengthen the gating story. The paper mentions 72% edit rate but doesn't analyze the 28% of turns that were skipped—were any of those misses?

**m6. No cost-benefit analysis.**
The tau2-bench table includes cost, but there's no systematic discussion of the computational overhead: how many extra LLM calls does the analyzer add per turn? What's the latency impact? For a system intended for deployment, this matters.

**m7. The soft-attention section (5.5) feels like it belongs in a different paper.**
It's an interesting direction but results are preliminary (held-out splits of 12-13 per task). Consider framing more clearly as "preliminary investigation" or moving to appendix to save space.

**m8. Inconsistent handling of the "accumulate instruction" for Actions.**
The caption of Table 1 mentions this instruction is applied to all strategies, but it's unclear what this is or why it's needed. A reader unfamiliar with LiC won't understand this. Either explain briefly or move to appendix.

---

## Questions for Authors

1. What happens when you apply the method to a model other than GPT-5-mini? Is the cognitive hazard model-dependent?
2. For the WildChat evaluation, what is the inter-annotator agreement of the LLM judge (e.g., judge self-consistency)?
3. What is the latency overhead of the analyzer per turn?

---

## Recommended Changes (Priority Order)

1. **Create real Figures 1 and 2** — highest impact for readability
2. **Add confidence intervals or significance tests** to key tables
3. **Tighten the abstract** — cut to ~150 words, focus on problem/method/key insight/headline result
4. **Reconsider "self-aware" in method name** — or add stronger justification
5. **Add cost/latency analysis** — even a brief paragraph
6. **Synthesize the memory story** — brief paragraph connecting Tables 2 and 6
7. **Explain the accumulate instruction** or move to appendix
8. **Add context compression to related work** — 2-3 sentences
9. **Move soft-attention results to appendix** if space is tight
10. **Analyze gating false negatives** — even qualitatively

---

## Overall Assessment

The core idea is solid and the cognitive hazard finding is genuinely novel. The evaluation breadth is a strength. However, the paper's empirical claims outrun its statistical support (small samples, no CIs, LLM-judge-only for WildChat), and the presentation still has room for improvement (placeholder figures, jargon-heavy title). With real figures, statistical rigor, and a tighter abstract, this would be a strong accept. As is, it's borderline—the ideas are good but the evidence needs strengthening.

**Score:** 5-6/10 (borderline, lean weak accept)

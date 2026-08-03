# Cluster 4: Token/Message Pruning, Selective Context, and KV-Cache Eviction

**Scope**: Methods that selectively DROP parts of conversation history or KV cache.
This is the family to which our primary baselines (OmitAssistant, ConcatenateUser) belong.

---

## Summary Table

| Method | Venue / Year | What it drops & signal | Weakness re: ENTANGLEMENT | Weakness re: STATEFULNESS | Verified URL |
|--------|-------------|------------------------|--------------------------|--------------------------|--------------|
| **Huang et al. (OmitAssistant)** | arXiv 2026 | Drops all prior assistant messages; signal = role filter (keep only `user` + `system` turns) | Breaks "follow-up without feedback" turns where user refers to a specific prior assistant reply without restating its content (e.g., "the second option isn't working") | Not evaluated on stateful envs; evaluated on self-contained multi-turn QA where rederivation is cheap | https://arxiv.org/abs/2602.24287 |
| **H2O** | NeurIPS 2023 | Evicts KV pairs with low cumulative attention scores; signal = running sum of attention weights across heads | Low-attended tokens evicted even if later turns introduce coreference to them; entangled entity tokens not attended at decode time are silently dropped | Single-generation design; no multi-turn memory — evicted tokens cannot be recovered in later turns | https://arxiv.org/abs/2306.14048 |
| **StreamingLLM** | ICLR 2024 | Drops everything outside initial "attention sink" tokens + a recent sliding window; signal = token position | Cross-turn references outside the window silently vanish regardless of semantic importance | Older turns evicted as new turns push them out of window; accumulated env state lost without explicit re-injection | https://arxiv.org/abs/2309.17453 |
| **Scissorhands** | NeurIPS 2023 | Evicts KV pairs for tokens with low "persistence of importance" (historically low attention); signal = historical attention pattern | Entangled reference tokens that were not heavily attended at creation are evicted; importance persistence holds only within stable-distribution text | Assumes importance signals are stationary; multi-turn state changes (new constraints, updated env) violate this assumption | https://arxiv.org/abs/2305.17118 |
| **SnapKV** | NeurIPS 2024 | Per-head KV entries not activated by the observation-window query prefix; signal = attention from a short prompt prefix before generation | Drops keys not attended by the *current* query prefix; prior turns that are entangled but not active in the prefix are invisible | Single-document long-context design; no mechanism to track or reinstate accumulated state from earlier turns | https://arxiv.org/abs/2404.14469 |
| **FastGen** | ICLR 2024 | Head-specific KV cache entries based on offline-profiled attention head type; signal = head profile (local / punctuation / special-token / full) | Head types fixed at profile time; novel cross-turn dependencies not captured by the offline profile are evicted | Static profiles encode no notion of evolving env state; can't prioritize state-encoding tokens over noise | https://arxiv.org/abs/2310.01801 |
| **PyramidKV** | ICLR 2025 | Tokens in upper layers beyond a layer-specific budget (smaller budgets at higher layers); signal = pyramidal attention-information analysis | Layer-wise budget allocation is semantic-agnostic; entanglement links between tokens are not a criterion for retention | Budget optimization targets efficiency; no state tracking — equal likelihood of evicting state tokens as irrelevant ones | https://arxiv.org/abs/2406.02069 |
| **Selective Context** | EMNLP 2023 | Low self-information tokens; signal = per-token perplexity under a small LM (drops "predictable" tokens) | Can drop low-perplexity entity mentions and coreference anchors that carry entangled references (common words are structurally central but statistically predictable) | Compresses single prompt snapshot; recurring low-perplexity state identifiers (e.g., database names) may be pruned | https://arxiv.org/abs/2310.06201 |
| **LLMLingua** | EMNLP 2023 | Low-perplexity tokens at coarse (sentence) and fine (token) granularity; signal = small-LM perplexity + budget controller | Instruction-tuned compression may confidently drop reference pronouns/tokens that look obvious locally but are critical for entangled later turns | Single-prompt design; doesn't model state transitions across turns; compresses what's there, not what's needed ahead | https://arxiv.org/abs/2310.05736 |
| **ERGO** | UncertaiNLP 2025 | Misaligned/degraded context; signal = Shannon entropy spike in next-token distribution triggers adaptive consolidation/reset | Reset produces a condensed summary; specific assistant outputs the user may reference in future turns are lossy-compressed or discarded | Consolidation rewrites history into a summary; accumulated env state (e.g., partial solution state, database schema + query history) must be explicitly preserved or is lost | https://arxiv.org/abs/2510.14077 |

---

## BASELINE: Huang et al. — Assistant-Message Omission

**Full citation**:
Jenny Y. Huang, Leshem Choshen, Ramon Astudillo, Tamara Broderick, Jacob Andreas.
*"Do LLMs Benefit From Their Own Words?"*
arXiv:2602.24287 [cs.CL], 27 February 2026.
URL: https://arxiv.org/abs/2602.24287

**Precise claim**: The paper compares *Full Context* (FC, all prior turns) to *Assistant-Omitted* (AO, only system + user turns; prior assistant turns replaced by `"[Response provided]"`). Across in-the-wild multi-turn technical conversations (WildChat + ShareLM, 300 conversations, Qwen3-4B / DeepSeek-R1-Distill-Llama-8B / GPT-OSS-20B / GPT-5.2), the paper finds: (1) omitting assistant history "does not affect response quality on a large fraction of turns," (2) 36.4% of turns are self-contained, (3) cumulative context length is reduced up to ~10×, and (4) models suffer from "context pollution" — over-conditioning on prior outputs that propagates errors (e.g., carrying over UMAP-specific arguments into a t-SNE rewrite). An adaptive logistic-regression classifier can retain ≥95% of FC quality while further reducing context.

**Stated scope and limitations** (from the paper):

- *Evaluation dependence*: "these findings depend on the reliability of the automated evaluator" (LLM-judge); human study was limited.
- *Dataset scope*: filtered technical chats (math/coding keywords); authors note "other domains or truly stateful tasks may behave differently."
- *Granularity*: the AO/FC choice is binary; the paper suggests as future work to "preserve only the specific past assistant responses relevant" — acknowledging that blind omission is too coarse.
- *Failure mode explicitly acknowledged*: "Follow-up without Feedback" turns — user references prior assistant output without restating it — constitute ~33.1% of turns and are where omission most reliably hurts.

**Does the paper acknowledge entanglement or state?**
Not using those terms explicitly. The "Follow-up without Feedback" category is functionally the entanglement failure mode. Stateful tasks are named as out-of-scope ("other domains or truly stateful tasks may behave differently") but not studied. The paper does not propose or test any mechanism for either axis.

---

## Notes on Related Families

**KV-cache eviction** (H2O, StreamingLLM, Scissorhands, SnapKV, FastGen, PyramidKV): operate at the token/KV-pair level within a single-document generation budget, not at the message level. Their eviction signals (attention scores, position, head profiles, layer budgets) are purely local to the current generation context; none tracks semantic entanglement or stateful environment transitions.

**Prompt token dropping** (Selective Context, LLMLingua): operate on the full prompt before generation, using perplexity as a proxy for redundancy. Both are agnostic to conversational structure and treat all tokens as independent.

**Reset/restart** (ERGO): detects performance degradation via entropy and consolidates context. Unlike message-level omission, ERGO at least monitors *when* dropping is needed; but the consolidation step is still a lossy rewrite that cannot guarantee preservation of entangled references or stateful content.

---

## Positioning Note

Every method in this cluster drops content via a signal that is blind to two structural properties of multi-turn interactions: (1) **entanglement** — whether later user turns depend on the specific wording or content of a prior assistant turn — and (2) **statefulness** — whether the environment outside the conversation window has a persistent state that must be represented in context. KV-cache eviction methods (H2O through PyramidKV) optimize for inference throughput within a single generation; their attention-based signals cannot distinguish a "safe to evict" filler token from a reference anchor that a future user turn will require. Message-level omission (Huang et al.) is cheaper and often effective on self-contained QA, but the paper itself flags the failure mode: turns where the user says "that approach isn't working" require the prior assistant output to interpret "that approach." ERGO's entropy trigger adds a *when to reset* signal but still performs a lossy consolidation that destroys specific assistant outputs. Our decontextualize-then-edit approach differs by (a) identifying *which* content is harmful before touching it and (b) preserving what the user's next turn will need, directly addressing both axes where this entire cluster breaks.

# Writing Changelog

## 2026-03-31: Advisor feedback round — formalization, novelty, writing mechanics

### 1. Formal problem setting (new subsection: Section 3.1)

**Added** a `Problem formulation` subsection at the top of Methods with:
- Mathematical notation: $C_t$ (context), $U_t$ (user messages), $A_{t-1}$ (assistant messages), $\mathcal{T}^*$ (true task spec), $\mathcal{E}$ (editing operator)
- Distribution shift framing: Equation 1 formalizes context pollution as $p(\text{correct} \mid U_t, A_{t-1}) < p(\text{correct} \mid U_t)$, showing assistant tokens reduce correctness
- Two desiderata for the editing operator: **Decontamination** (remove biasing effect) and **Preservation** (retain useful state)
- Inspiration from MemoBrain (dependency-aware memory graphs, executive memory) and U-Fold (POMDP formulation, intent-aware context folding) for notation style

**Added** Algorithm 1: pseudocode for the full context editing pipeline (selective attention, error monitoring, gating, intervention). Placed between Intervention Strategies and Memory subsections.

### 2. Math notation sprinkled through existing Methods

- **Decomposition (Section 3.2):** References to $U_t$, $A_{t-1}$, $\hat{\mathcal{T}}$, $C_t$, $M$ (memory cheatsheet), plus Algorithm 1 line references
- **Intervention strategies (Section 3.3):** Each strategy now has a formal expression ($C'_t = C_t \oplus \text{artifact}$ for Augment, $C'_t = \textsc{Template}(\hat{\mathcal{T}}, \texttt{aligned})$ for Reset, $C'_t \sim p_\theta(\cdot \mid ...)$ for Rewrite). Gating references Algorithm 1 lines 6-8.
- **Memory (Section 3.4):** Cheatsheet denoted $M$, editing operator $\mathcal{E}$

### 3. Novelty framing strengthened (Related Work)

- **Context pollution paragraph:** Added explicit language: prior work treats context as "uniformly harmful" while we treat it as "heterogeneous" — selectively preserving useful content and removing what is harmful. This makes the conceptual distinction crisper than before.
- **Assessment:** The selective-vs-blanket distinction was already present in the abstract ("Prior mitigations that simply discard all assistant messages"), intro (paragraph 3, contributions bullet 2), and related work (paragraph 3 on compaction). The related work paragraph 1 was the weakest link and is now strengthened. No major restructuring needed.

### 4. Em dash removal

Replaced **all** em dashes (`---`) in prose throughout the paper (main body and appendix) with appropriate alternatives:
- Parenthetical asides → parentheses or commas
- Elaborations → colons or semicolons
- Appositive phrases → commas

Remaining `---` only in table cells (as dash placeholders) and prompt section titles (`Subtask 1 --- Task specification extraction`), which are appropriate uses.

### 5. Transition and flow improvements

- Intro paragraph 5 (cognitive hazard): "Interestingly, we find" → "A further challenge is that" + added "therefore" for logical flow
- Related work: added "Critically" to introduce the uniform/heterogeneous contrast
- Various small connective edits throughout

### 6. Space reclaimed (to offset formalization additions)

Compressed the following to reclaim ~35 lines:
- **Intro "irony" paragraph** (transformer attention): Cut from 5 sentences to 2, preserving the key insight (architectural attention fails at cognitive selective attention) and test-time scaling connection
- **Executive function related work:** Merged two sentences, dropped the Yao/Kahneman parallel
- **LiC experiment paragraph:** Removed redundant phrasing about "controlled evaluation of multi-turn performance degradation" and consolidated
- **WildChat experiment paragraph:** Removed repeated detail about judge dimensions
- **Discussion "editing vs removal":** Compressed 2 paragraphs to 1, removing repetition of results already in tables
- **Cost-capability tradeoff:** Tightened from 6 sentences to 4

### Space budget assessment

The formalization adds ~25 lines (problem setting) + ~15 lines (algorithm). Compressions reclaim ~35-40 lines. Net effect should be roughly neutral, but the paper was already at the page limit so it will be tight. If we go over, candidates for appendix migration:
- The tau2-bench results paragraph (Section 5.4) could be shortened to 2 sentences with details in appendix
- The CollabLLM results (Section 5.2) are already very brief but could be appendix-only
- The cognitive hazard discussion (Section 6.2) could be compressed, with the "contamination amplifies through chained calls" finding moved to appendix

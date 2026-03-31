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

### Space budget assessment (after commit 1)

The formalization adds ~25 lines (problem setting) + ~15 lines (algorithm). Compressions reclaim ~35-40 lines. Net effect should be roughly neutral, but the paper was already at the page limit so it will be tight.

---

## 2026-03-31 (commit 2): Space recovery and appendix reorganization

### 7. Algorithm moved to appendix

Algorithm 1 moved from between Sections 3.3-3.4 to Appendix A. Main body now references it as "Algorithm~1 (Appendix A)". Saves ~18 lines of vertical float space.

### 8. Models paragraph removed

Removed standalone `\paragraph{Models.}` from Experiments section. Replaced with a single opening line: "Unless otherwise noted, GPT-5-mini serves as both assistant and analyzer throughout." The model list (GPT-5, DeepSeek V3.2, Qwen 3.5) is now mentioned only in the multi-model appendix subsection where it belongs.

### 9. Additional main-body compressions

- **Tau2-bench results (Section 5.4):** Compressed from 3 sentences to 2, removing redundant restatement about "fundamentally incompatible with stateful settings"
- **Memory methods opening (Section 3.4):** Cut from 3 sentences to 2, removing "While various approaches with varying degrees of complexity exist"
- **WildChat results paragraph:** Removed "see Appendix for turn type definitions" parenthetical, tightened gating description

### 10. Appendix reorganized

**New structure:**
- **A. Algorithm** — pseudocode (moved from main body)
- **B. Evaluation details** (umbrella `\section` with `\subsection`s):
  - B.1 LiC evaluation adjustments (task-specific changes + false negative ID)
  - B.2 Multi-model evaluation protocol
  - B.3 CollabLLM evaluation details
  - B.4 WildChat turn type definitions
  - B.5 Tau2-bench agentic adaptation
  - B.6 Tau2-bench results and diagnostic analysis
- **C. Prompt templates** (analysis, compaction, memory prompts)
- **D. Soft vs. hard attention**
- **E. Memory-based learning details**
- **F. Trajectory example: WildChat Maven debugging**
- **G. Additional related work**
- **H. Extended agentic context management discussion**
- **I. Executive function as a design pattern**

**Rationale:** All benchmark-specific evaluation details are now grouped under one umbrella section, making it easy for reviewers to find methodology details for any specific benchmark. Method supplements (algorithm, prompts) come first, then evaluation, then analysis extensions, then examples, then additional related work/discussion.

### Space budget assessment (after commit 2)

Compared to the post-formalization state: moved algorithm to appendix (~18 lines), removed Models paragraph (~2 lines), additional compressions (~8 lines). Total recovery: ~28 lines. Combined with the ~35 lines recovered in commit 1, this should comfortably offset the ~25-line formalization addition and bring us back to the page limit.

# NeurIPS 2026 Reviews — Submission 27902 (AC3)

**Cleaned/reformatted from the raw OpenReview paste** (`ac3_reviews_raw.md`).
Content is verbatim except for whitespace, header, and list formatting fixes; no wording was changed.

- **Decision signal:** Meta-review leans reject; all three reviewers rate **3 (Borderline reject)**.
- **Reviewers:** iNYK (conf. 3), Vg97 (conf. 4), 5YHP (conf. 3).

---

## Meta-Review — Area Chair PfEt

*Submitted 21 Jul 2026, 22:09 (modified 23 Jul 2026, 11:24).*

The reviewers have serious reservations related to:

1. **Generalizability** — the method changes for each setting.
2. **Validity of theoretical assumptions.**
3. **Weaknesses in experimental evidence** — including limited benchmarks, lack of statistical reporting, and mixed results.

These "seem to preclude a path toward publication at NeurIPS." The authors are invited to rebut if the reservations are made in error, but if the reservations are correct, the AC considers them too large to be resolved in the rebuttal window and encourages submission elsewhere.

---

## Review 1 — Reviewer iNYK

*26 Jun 2026 (modified 23 Jul 2026). Contribution type: General.*

### Summary
The paper tackles context pollution in multi-turn LLM use: the model's own earlier outputs accumulate in context and anchor later turns, so an early misinterpretation persists even after the user corrects it. Prior work uses **Assistant Omission (AO)**, dropping all assistant messages, but the authors show this only works for self-contained turns and fails on referential ones, where partial work or tool-call state lives only in assistant turns.

They propose **AC3**, a training-free, inference-time method: a separate analyzer (1) extracts a clean task spec from user messages alone, with assistant turns structurally excluded, then (2) compares the assistant's history against that spec and edits the context (Augment/Reset/Rewrite, optionally gated) to keep verified work and remove invalidated reasoning. A lightweight memory ("cheatsheet") accumulates transferable analysis principles.

Key finding: **pollution is contagious** — if the spec extractor sees assistant messages, accuracy drops below baseline, so structural exclusion (not just prompting) is essential.

### Strengths
- The **self-contained vs. referential** distinction cleanly explains why AO is near-perfect in some settings and collapses to zero in others; the four benchmarks are ordered along exactly this referentiality axis.
- Backed by the **Table 5 ablation** (prompt-level instructions to ignore assistant turns are insufficient; structural exclusion is required), the direction is convincing. The observation that a contaminated two-stage pipeline underperforms a contaminated single-pass one carries a useful lesson for any multi-stage LLM pipeline.

### Weaknesses
- **Small samples / thin replication.** LiC has only 18–25 samples per cell, and only Gated-Reset was replicated three times (std 5–7pp), so several-point gaps sit within noise. The "exceeds the oracle on database" result (48% vs. 32%) comes from a **single Reset run**, whereas the replicated Gated-Reset averages only **38.7%**.
- **Table 2 hard-subset selection bias.** The hard subset is the 20 hardest items chosen by baseline failure rate, and the runs replay GPT-5.2 trajectories rather than each model's own generations. Selection on the trajectory, compounded by regression to the mean, will make almost any reasonable intervention look strong on such a subset; the setup measures "how much can be recovered from a fixed polluted history," not native multi-turn behavior — making the **+20–42pp** claim weaker than it appears.
- **"Robust across the spectrum" overclaims on tau2.** The abstract and Figure 1 repeatedly call AC3 "the only method robust across the spectrum," yet on tau2-bench the per-trial numbers in Appendix B.6 give **Baseline mean 53.3%** and **Gated-Reset 48.3%** — roughly 5 points below baseline on the mean. Table 1d reports best-of-3 (60 vs. 65), which masks the negative mean. "Robust" here means "did not collapse," not "better," and it still adds ~20% cost per turn.

### Questions
1. Can you re-report Reset vs. Baseline on a **random subset**, or one selected independently of baseline results? If gains survive on an unbiased subset, this supports the argument; if they largely vanish, the generalization claim should be removed.
2. Please report Baseline and Gated-Reset as **mean ± std over the three seeds** rather than best-of-3, and state explicitly whether AC3's mean clears baseline.

### Scores
Quality **2** · Clarity **3** · Significance **3** · Originality **2** · **Rating 3 (Borderline reject)** · Confidence **3**.

---

## Review 2 — Reviewer Vg97

*25 Jun 2026 (modified 23 Jul 2026). Contribution type: General.*

### Summary
The paper studies multi-turn LLM degradation caused by "context pollution." It proposes **AC3**, a training-free inference-time framework that uses an analyzer subroutine to extract a clean task spec from user turns, evaluate prior assistant outputs against that spec, then edit the context via augmentation, reset, or rewrite. Evaluated across **LiC, CollabLLM, WildChat, and tau2-bench**; reports improvements over full-context baselines on several self-contained and conversational settings, pairwise WildChat wins, and avoidance of AO's catastrophic failure in stateful tool-use.

### Strengths
- Addresses an important problem: managing history when prior assistant messages are neither uniformly useful nor harmful.
- The self-contained vs. referential/stateful distinction is well motivated.
- Correctly notes AO is not a general-purpose fix once users refer back to assistant artifacts or once tool-call results live in assistant turns.
- The hard-attention ablation (analyzer can itself be contaminated) is a useful empirical observation supporting the structural-exclusion design — **maybe move it from the appendix to the main section.**

### Weaknesses
- **Baselines too weak/narrow.** Main comparisons are full context, AO, concatenated user messages, and ERGO — useful diagnostics but not strong enough for a robustness claim. Should compare against recent context-condensation/management methods such as **MT-OSC [1]**. Related work discusses **U-Fold, Context-Folding, MemoBrain** and argues they address compaction not pollution; the distinction is reasonable but not sufficient to exclude them as empirical baselines. Since AC3 claims robustness across self-contained/referential/stateful regimes, the evaluation should include at least one strong recent context-condensation baseline (e.g., **MT-OSC on LiC-style benchmarks**) and one strong user-centric agent context-folding baseline (e.g., **U-Fold on tau2-bench**) — or clearly justify why they cannot be adapted.
- **Statistical reliability.** Many headline LiC cells use small samples, only Gated-Reset repeated 3×. The tau2 result is unpersuasive as presented: main table reports best-of-3 for Baseline and Gated-Reset, while the appendix shows high variance and indicates AC3 is within trial noise of baseline.
- **Method changes substantially across settings.** LiC relies on hard-attention user-only extraction; CollabLLM uses Rewrite **without** structural exclusion; tau2 reframes the analyzer as "strategic reflection," tracks environment state, caps resets. These make the contribution less clear — is it one method, a family of prompt-engineering patterns, or several task-specific variants?

**Reference:** [1] Singh et al., 2026. *MT-OSC: Path for LLMs that get lost in multi-turn conversation.* arXiv:2604.08782.

### Questions
1. Can you compare against stronger context-management baselines (per weakness), or justify why they cannot be adapted?
2. Can you report statistically sound results — CIs, paired tests, or bootstrap for LiC and WildChat, and **mean ± variance instead of best-of-3** on tau2?
3. How sensitive are results to the analyzer model and compute budget? AC3 adds LLM calls per turn; a fair comparison needs **equal-budget baselines** (repeated generation, self-reflection, or a strong summarizer/condensor with the same model and call count). Also report **latency**, not just API cost.
4. Clarify the **general AC3 algorithm across benchmarks**: LiC uses hard attention, CollabLLM single-pass Rewrite without structural exclusion, tau2 strategic-reflection. Which components are essential vs. task-specific?

### Scores
Quality **2** · Clarity **3** · Significance **3** · Originality **3** · **Rating 3 (Borderline reject)** · Confidence **4**.

---

## Review 3 — Reviewer 5YHP

*21 Jun 2026 (modified 23 Jul 2026). Contribution type: General.*

### Summary
Studies context pollution in multi-turn interaction: incorrect early assumptions persist and bias later responses even after correction. Proposes **AC3**, training-free inference-time analyzer that builds a consolidated task spec, evaluates prior work against it, and edits context via **Augment / Reset / Rewrite**, with a gating mechanism to skip intervention when no issue is detected, plus a lightweight cross-instance memory. Evaluated on four settings of increasing dependence on assistant history (**LiC, CollabLLM, WildChat, tau2 telecom subset**); reports substantial LiC gains, strong WildChat pairwise preferences, and that selective management survives stateful tool use where AO destroys tool history.

### Strengths
1. **Strong problem framing** — prior assistant messages contain both invalidated reasoning and indispensable task state; treating assistant context as not-uniformly-harmful is a meaningful conceptual improvement.
2. **Structural-exclusion result is compelling** — the hard-attention ablation shows decomposition can amplify errors when an upstream stage produces a biased spec; suggests information-flow constraints (not prompts alone) may be necessary when using LLMs to audit misleading context.
3. **Multiple levels of referentiality** — tau2 illustrates a real AO limitation (removing assistant messages removes tool observations → loses environment state); WildChat suggests selective editing beats retain-all or delete-all.
4. **Modular and interpretable** — clean separation of spec extraction, approach evaluation, intervention; well written; appendices disclose replay protocol, variance, prompts, and the limited scope of the agentic experiments.

### Weaknesses
1. **Strongest mechanism relies on an assumption that fails in the most important referential settings.** Hard-attention works because LiC is a shredded single-turn problem. In genuinely referential interactions ("modify the second paragraph," "extend the previous query") the referent lives only in assistant history. **Appendix D** confirms the realistic soft-attention variant (must see full conversation) performs substantially worse than hard attention across math/code/database; memory only partially closes the gap and helps very little on code. So the paper shows structural exclusion works when user messages independently specify the task, but does not solve separating useful vs. harmful assistant content when both must be visible — limiting the robustness claim.
2. **Not a single fixed method across benchmarks.** LiC = two-stage user-only extraction + Reset/Gated-Reset; CollabLLM = full-transcript single-pass Rewrite; WildChat = several operators; tau2 = strategic-reflection + state tracking.
3. **LiC evidence limited by small samples, replay, mostly single runs.** Modest per-task N; only Gated-Reset over 3 reruns; most AC3/memory rows are single-trial point estimates; no paired tests or CIs in the main table. LiC uses **replay mode** — all methods get the same pre-generated trajectory and only regenerate the final response, isolating recovery from a fixed polluted context rather than end-to-end deployment. Early rewrites could change later assistant behavior, user-sim responses, and state accumulation. Results should be read as **final-turn recovery**, not end-to-end multi-turn improvement.
4. **Referential-setting evidence weaker than headline.** On CollabLLM, AC3-Rewrite is **below AO on MATH-Hard** and **tied with AO on BigCodeBench** — supports improvement over full context but not over blanket omission. BigCodeBench cannot use executable tests (simulator doesn't pass required function signatures) so execution is replaced with a **GPT-5 correctness judge**, changing benchmark interpretation and adding judge uncertainty. WildChat pairwise win rates are strong but measure static continuation quality on fixed transcripts, use an LLM judge, and Reset/Rewrite naturally produce more consolidated/explicit responses that a pairwise judge may favor even without task-level gains. No judge agreement, position-bias checks, or human validation reported; compared methods have slightly different sample counts.
5. **Analyzer not directly evaluated as a pollution detector.** Method is motivated as identifying invalidated reasoning while preserving useful work, but only downstream answer quality is measured — not whether the analyzer identifies polluted spans, preserves necessary state, or gates at the right times. In WildChat, Gated-Reset edits ~**72%** of turns with no precision/recall of the detector or breakdown of harmful false-positive edits vs. missed pollution. Direct annotations (stale vs. useful vs. must-preserve) would distinguish genuine auditing from re-solving the task.
6. **Memory results mixed and under-characterized.** Substantial gains in some settings, neutral/harmful in others — suggests the cheatsheet can introduce stale/over-general priors (pollution at the analyzer level). Wants analysis of order sensitivity, train/eval separation, and failure cases before presenting memory as generally beneficial.

**Overall:** clearly written with an important architectural insight (structural exclusion), but current evidence supports a narrower conclusion than the main narrative: AC3 recovers from fixed polluted histories in self-contained tasks and selective editing is more compatible with referential state than blanket omission — not yet a unified, reliable improvement for genuinely referential and stateful long-horizon interaction.

### Scores
Quality **3** · Clarity **2** · Significance **3** · Originality **3** · **Rating 3 (Borderline reject)** · Confidence **3**.

---

## Cross-review quick map

| Concern | iNYK | Vg97 | 5YHP | AC meta |
|---|:--:|:--:|:--:|:--:|
| Method changes per setting (generalizability) | – | ✓ | ✓ | ✓ |
| Statistics: small N, best-of-3, no CIs | ✓ | ✓ | ✓ | ✓ |
| tau2 within noise / below baseline mean | ✓ | ✓ | ✓ | ✓ |
| Hard-subset (Table 2) selection bias | ✓ | – | ✓ | ✓ |
| Replay ≠ end-to-end | ✓ | – | ✓ | – |
| Weak/missing baselines (MT-OSC, U-Fold, equal-budget) | – | ✓ | – | ✓ |
| CollabLLM ≤ AO; BigCodeBench judge | – | – | ✓ | ✓ |
| Analyzer not evaluated as detector (precision/recall) | – | – | ✓ | – |
| Memory mixed/under-characterized | – | – | ✓ | ✓ |
| Soft-attention (Appendix D) gap on real referential turns | – | – | ✓ | ✓ |

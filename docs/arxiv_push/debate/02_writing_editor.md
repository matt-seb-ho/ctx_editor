# Writing Editor Review — arXiv Push (AC3 paper)

**Target:** `writing/overleaf_repo/neurips/neurips_2026_conference.tex`
**Scope:** writing quality, flow, presentation (not experimental validity). Terminology to keep stable: method = **AC3**; operators = **Augment / Reset / Gated-Reset / Rewrite**; **referential** vs **self-contained**; **context pollution**; **contagious pollution**.
**Method:** Paragraph Clarity Check + reverse outlining on Abstract / Introduction / Conclusion; terminology sweep across whole paper; flow/hedge audit.

---

## 1. Reverse Outline — Abstract, Introduction, Conclusion

### 1.1 Abstract (lines 109–111) — one ~250-word paragraph

| # | Sentence role | Message | Verdict |
|---|---|---|---|
| S1 | Problem | Multi-turn failure mode: model's own outputs accumulate and bias later turns | Good, leads with the problem |
| S2 | Name | Early wrong inferences anchor reasoning = *context pollution* | Good |
| S3 | Prior work limit | Prior interventions discard assistant messages, rely on user turns being sufficient | Good but clunky ("rely on user turns containing sufficient information") |
| S4 | The gap | Real apps are *referential*: state lives only in assistant turns | **Ungrammatical** — "may only exist in assistant turns, but referenced in later turns" (missing "are"). Key sentence, needs fix |
| S5 | Method | AC3 = analyzer audits each turn in 3 steps (consolidate / compare / edit) | Good, crisp, names the method |
| S6 | Insight | Pollution is *contagious*; analyzer must be shielded | Good, memorable — but "motivating context management for the context-management subagents themselves" is dense |
| S7 | Results | 4 benchmarks; 55–80% gap closed; 84–86% WildChat; 60%→0% AO collapse | Backed by tables; "$\sim$60% to 0%" is model-specific (see §2/§4) |
| S8 | Takeaway | Selective curation, not blanket removal, scales | Strong close |

**Verdict on structure:** Follows abstract Version 1/2 (Challenge → Insight → Contribution) well: problem first, method crisp, insight bonus, results backed. The *logic* is sound.

**Verdict on the single-paragraph question (task item 3):** A single paragraph is conventional for NeurIPS and I would **not** split it into multiple paragraphs. The readability problem is **not** paragraph count — it is that several sentences carry too many sub-clauses (S4, S6, S7). Fix by tightening sentences, not by adding paragraph breaks. If the arXiv version relaxes the NeurIPS template, an optional two-sentence-group break after S6 (problem+method | findings) would help, but it is a nice-to-have, not a need.

### 1.2 Introduction (lines 126–139) — 5 paragraph-units

| Para | Topic sentence | Message | Verdict |
|---|---|---|---|
| P1 (126–127) | "Multi-turn interaction is the dominant mode of use…" | Multi-turn degrades vs single-turn; Laban's 39% drop; self-reinforcing dynamic; Huang's AO fix | One clear arc; topic sentence strong. Fine. |
| P2 (129–133) | "AO works precisely when user utterances… are *self-contained*." | AO only works on self-contained turns; many turns are referential; omission then breaks references | **Strongest paragraph.** Clean self-contained→referential→example→consequence chain. |
| P3 (135) | "We propose AC3, a training-free, inference-time method…" | Method mechanics + test-time-scaling framing + two differentiators from context-management work | Dense (does 3 jobs) but coherent. **Enumeration bug:** "(1) Prior methods…" capitalized, "(2) they compact…" lowercase. |
| P4 (137) | "This design is also shaped by an unexpected finding: pollution is *contagious*." | Analyzer itself must be shielded; prompting alone insufficient | One clear message. Good. |
| P5 (139) | "Across four benchmarks…, AC3 is the only method that holds up…" | Results summary across the referentiality spectrum | Good topic sentence but **one ~90-word sentence** stuffed with parentheticals — hard to parse on first read. |

**Verdict:** Intro is strong and matches the skill's logic map (task → prior-method limit → our method → why it works → results). Two flow issues: P3 enumeration capitalization, and P5 overlength. Terminology drift ("Gated Reset" here vs "Gated-Reset" in tables).

### 1.3 Conclusion (line 405) — one ~210-word paragraph

Reverse outline:
1. Restate method (training-free, harness-level, curate not discard).
2. Evidence (LiC 55–80%; WildChat 84–86%; tau2 AO 0% vs AC3 viable).
3. Generalization + memory.
4. Contagious-pollution insight restated.
5. Close: "blanket removal cannot scale where selective curation can, and the gap… will only widen."

**Verdict:** Hits restate-problem / strongest-evidence / insight (conclusion guide items 1–3). **Two gaps against the guide and against the revision's own new contribution:**
- **No limitation / future-direction sentence** (guide items 4–5). Limitations live only in Appendix `app:limitations`; the conclusion itself makes zero concession, which reads slightly over-claimed for arXiv.
- **Missing the "appropriate intensity" second landing point.** Per `docs/jun1_megatable_findings.md` §3a, the mega-table's headline new finding is that *the right operator depends on respondent strength* (one shared analyzer, three intensity knobs). The Discussion now makes this point (§6, line 371–372) but the Conclusion still lands only "selective curation > blanket removal." The conclusion should land both.
- The closing clause "the gap… will only widen" is an **unsupported forward-looking claim** — see §3.

---

## 2. Terminology Consistency Issues (whole paper)

Ranked by how jarring they are to a fresh reader.

1. **`AC3` written literally vs `\method` macro — HIGH.** Section 5.4 (line 358) and Discussion use literal "AC3", "AC3-Augment", "AC3-Rewrite", "every AC3 operator", while the rest of the paper uses `\method` and `\method-Augment`. Same rendered output today, but (a) inconsistent source, (b) breaks the rename-safety the `\method` macro exists for, (c) `\method-Augment` vs `AC3-Augment` is a visible style split if the macro's `\xspace` ever differs. **Fix:** replace literal `AC3`/`AC3-Augment`/`AC3-Rewrite` at line 358 (and any other body occurrence) with `\method`/`\method-Augment`/`\method-Rewrite`.

2. **"Gated Reset" (space) vs "Gated-Reset" (hyphen) — HIGH.** Both forms are pervasive: body prose mostly "Gated Reset" (lines 139, 318, 321, 334, 344, 347, 360, 405, 606), tables and appendix mostly "Gated-Reset" (254, 273, 280, 300, 311, 460, 485, 504, 558). Pick one (recommend **"Gated Reset"** as the reader-facing name in prose to match "always-on Reset"; or hyphenate everywhere to match table labels — but be uniform). Same issue latent for "Reset" the operator vs "reset" the action.

3. **AO first-expansion inconsistency — MEDIUM.** Three expansions: "Assistant Omission" (fig caption, line 122), "assistant omission" (intro line 127, canonical first-use), "Assistant Messages Omitted" (line 233). Define once as **"assistant omission (AO)"** at first use (line 127) and use "AO" thereafter; make the figure caption and line 233 match. Line 233's "Assistant Messages Omitted (AO;~\citealt{...})" is a *second* definition of an already-defined acronym.

4. **"Concatenate User" vs "Concat User" — LOW.** Line 233 introduces "Concatenate User baseline" then immediately uses "Concat User"; table (265) uses "Concat User". Fine to use the short form, but introduce it explicitly: "the Concatenate User baseline (Concat User)".

5. **Operator count framing tension — LOW/MEDIUM.** Methods §3.2 (line 208–212) defines **three** operators (Augment, Reset, Rewrite) with **Gating as orthogonal**; Figure 3 caption (187) says "Augment, Reset, or Rewrite". But Table 1 and all results treat **Gated-Reset as a fourth first-class operator/row**, and the task brief lists four operators. Not wrong, but a first-time reader meets "Gated-Reset" in Table 1 (273) before understanding it = Reset + the orthogonal gate. Add a half-sentence in §3.2 Gating bullet making explicit that "Reset + gating = the Gated-Reset row reported in results."

---

## 3. Flow / Clarity / Hedge Problems (ranked)

1. **Rewrite operator hedge, §3.2 line 211 — HIGH (also grammar).** "…with a ceiling we expect to surpass deterministic mapping over time." Two problems: (a) reads as forward-looking hedge / incremental patching, and (b) `docs/jun1_megatable_findings.md` §2c shows Rewrite *already* wins on WildChat×Kimi (91.5 vs Reset 71.6), tau2×Kimi (73.7), CollabLLM×Kimi — present-day, current models. The "we expect… over time" undersells the paper's own evidence. Also ungrammatical: a "ceiling" cannot "surpass deterministic mapping" (category error; should be "surpass *that of* deterministic mapping"). **Fix:** state the present-tense win and cite the table.

2. **Intro P5 overlength, line 139 — HIGH.** ~90-word sentence with 4 parentheticals. Break into 2 sentences (thesis sentence + evidence sentence).

3. **Discussion self-distillation sentence, line 369 — MEDIUM.** One ~70-word sentence ("…but the analyzer's outputs are plain-text reasoning of the kind SOTA models already emit in their internal `<reasoning>` traces, so recent self-distillation methods… can absorb the analysis into the base model with no inference-time call overhead; embedding outputs and entropy spikes do not absorb as cleanly."). Reads defensive and runs long. Split into cost-claim + distillation-claim.

4. **Conclusion closing claim, line 405 — MEDIUM.** "…and the gap between them will only widen." Speculative, unsupported, and slightly grandiose for a paper whose tau2 result is explicitly "preliminary." Either drop or ground it ("…as interaction grows more referential and agentic, the settings where blanket removal fails outnumber those where it suffices").

5. **Abstract S4 grammar + S7 model-specificity — MEDIUM.** S4 missing verb (see §1.1); S7 "$\sim$60% to 0%" is the gpt-5-mini baseline only — Foundry baselines range 26–68%, all → 0% (jun1 §2d). Make model-agnostic.

6. **Intro P3 enumeration capitalization, line 135 — LOW.** "(1) Prior methods… (2) they compact…" → capitalize "(2) They" (or lowercase both consistently).

7. **§4 tau2 description, line 242 — LOW.** "Unlike other agentic benchmarks, tau2-bench makes conversation especially meaningful with a novel dual-control setup…" — two long sentences; the "makes conversation especially meaningful" is vague. Tighten to the concrete property (state lives across both parties' turns).

---

## 4. Concrete Before → After Rewrites (top spots; LaTeX preserved)

### R1 — Abstract S4 (grammar; line 110)
**Before:**
> However, more complex interactive applications are often \emph{referential}: partial work, prior decisions, and environmental state may only exist in assistant turns, but referenced in later turns by the user and assistant alike.

**After:**
> However, more complex interactive applications are often \emph{referential}: partial work, prior decisions, and environmental state may exist only in assistant turns, yet both user and assistant refer back to them in later turns.

### R2 — Abstract S7 (model-specific → general; line 110)
**Before:**
> …and remains viable in agentic tool use where blanket omission collapses from $\sim$60\% to 0\%.

**After:**
> …and remains viable in agentic tool use, where blanket omission collapses to 0\% across every model tested.

### R3 — §3.2 Rewrite operator (de-hedge + grammar; line 211)
**Before:**
> \item \textbf{Rewrite.} An additional LLM call generates a restructured context: $C'_t \sim p_\theta(\cdot \mid \hat{\mathcal{T}}, \texttt{aligned}, \texttt{issues}, C_t)$. Most flexible; trades occasional summarization loss for arbitrary restructurings, with a ceiling we expect to surpass deterministic mapping over time.

**After:**
> \item \textbf{Rewrite.} An additional LLM call generates a restructured context: $C'_t \sim p_\theta(\cdot \mid \hat{\mathcal{T}}, \texttt{aligned}, \texttt{issues}, C_t)$. Most flexible; it trades occasional summarization loss for arbitrary restructurings, and already surpasses the deterministic Reset mapping on the most referential benchmarks (WildChat, tau2-bench; Section~\ref{sec:wildchat-results}, Table~\ref{tab:megatable}).

### R4 — Intro P5 split (overlength; line 139)
**Before:** (single ~90-word sentence beginning "Across four benchmarks of increasing referentiality…")

**After:**
> Across four benchmarks of increasing referentiality (Figure~\ref{fig:story}), \method is the only method that holds up across the spectrum (Tables~\ref{tab:main},~\ref{tab:megatable},~\ref{tab:wildchat}). It closes 55--80\% of the multi-turn gap on self-contained LiC tasks~\citep{laban2025lost} — and exceeds the oracle on database — using Gated Reset as a single operator (e.g., $60.0\to80.0$\% on math, $15.8\to64.4$\% on code; mean over $N{=}3$ replay-mode reruns). It wins 84--86\% pairwise on real human--AI conversations from WildChat~\citep{zhao2024wildchat}, and stays viable on stateful tool-use tasks from tau2-bench~\citep{barres2025tau2}, where AO catastrophically fails ($60.0\to0$\%) by destroying tool-call results that live only in assistant turns. These gains generalize across four model families at different scales (closed and open-weight; +20--42pp average), and memory-based learning improves them further without parameter updates.

### R5 — Intro P3 enumeration (capitalization; line 135)
**Before:**
> …in two ways. (1) Prior methods address an agent's own thinking and execution trajectory following a single user request, while we address ongoing multi-turn user--agent dialogue. (2) they compact tokens for efficient long-horizon execution, while we remove pollution to improve correctness…

**After:**
> …in two ways. (1) Prior methods address an agent's own thinking and execution trajectory within a single user request, whereas we address ongoing multi-turn user--agent dialogue. (2) They compact tokens for efficient long-horizon execution, whereas we remove pollution to improve correctness…

### R6 — Conclusion (add operator-intensity point + limitation/future; line 405)
**Before (final two sentences):**
> A non-obvious finding falls out of the design: pollution is contagious, since even an independent reviewer model anchors on the assistant's reasoning if exposed to it, so the analysis pipeline must structurally exclude assistant turns rather than rely on prompting alone. As LLM interaction grows more referential and agentic, blanket removal cannot scale where selective curation can, and the gap between them will only widen.

**After:**
> A non-obvious finding falls out of the design: pollution is contagious — even an independent reviewer model anchors on the assistant's reasoning if exposed to it — so the analysis pipeline must structurally exclude assistant turns rather than rely on prompting alone. The multi-respondent results add a second lesson: a single shared analyzer supports the full operator menu, and intensity should be matched to the agent — lighter editing (Augment) for stronger respondents, heavier editing (Rewrite) for weaker ones (Table~\ref{tab:megatable}). Our agentic evidence is limited to one tau2-bench subset and simulated users (Appendix~\ref{app:limitations}); extending selective curation to long-horizon and real-user settings is the natural next step. As interaction grows more referential and agentic, the settings where blanket removal fails increasingly outnumber those where it suffices — and selective curation, not omission, is what scales.

### R7 — Discussion self-distillation split (line 369)
**Before:**
> \method incurs heavier per-turn cost than detection-only alternatives such as \citet{huang2026context} (embedding classifier) and \citet{khalid2025ergo} (output-entropy spikes), but the analyzer's outputs are plain-text reasoning of the kind SOTA models already emit in their internal \texttt{<reasoning>} traces, so recent self-distillation methods~\citep{...} can absorb the analysis into the base model with no inference-time call overhead; embedding outputs and entropy spikes do not absorb as cleanly.

**After:**
> \method incurs heavier per-turn cost than detection-only alternatives such as \citet{huang2026context} (embedding classifier) and \citet{khalid2025ergo} (output-entropy spikes). That cost is recoverable, however: the analyzer's outputs are plain-text reasoning of the kind SOTA models already emit in their \texttt{<reasoning>} traces, so recent self-distillation methods~\citep{...} can fold the analysis into the base model with no extra inference call. Embedding outputs and entropy spikes do not distill as cleanly.

### R8 — Terminology sweep (mechanical)
- Line 358: `AC3` → `\method`; `AC3-Augment` → `\method-Augment`; `AC3-Rewrite` → `\method-Rewrite` (all literal occurrences).
- Choose one of "Gated Reset" / "Gated-Reset" and apply globally (recommend "Gated Reset" in prose, keeping table cell labels as-is only if column width forces it — but flag the split in a comment).
- Line 122 caption "Assistant Omission (AO)" and line 233 "Assistant Messages Omitted (AO)" → both to "assistant omission (AO)" defined once at line 127; downstream uses "AO".

---

## 5. Prioritized Writing-Polish List for arXiv

**Must-fix (grammar / correctness of claim, cheap):**
1. R1 — Abstract S4 missing verb (ungrammatical headline-adjacent sentence).
2. R8 — `AC3` literal → `\method` (line 358) and the AO triple-definition; standardize "Gated Reset" spelling.
3. R2 — Abstract "$\sim$60% to 0%" model-specificity.
4. R5 — Intro "(2) they" capitalization.

**High-value (flow / de-hedge, moderate effort):**
5. R3 — Rewrite operator: kill "we expect… over time," state present-day win.
6. R4 — Split the 90-word Intro results sentence.
7. R6 — Conclusion: add the operator-intensity landing point + a one-line limitation/future direction; reground the closing claim.

**Polish (readability, optional):**
8. R7 — Split the long self-distillation sentence in Discussion.
9. §4 tau2 sentence (line 242): replace "makes conversation especially meaningful" with the concrete dual-control property.
10. §3.2 Gating bullet: one clause tying "Reset + gating = the Gated-Reset results row" so Table 1 doesn't surprise the reader.
11. Line 233: introduce "Concat User" as an explicit abbreviation of "Concatenate User."

**Do NOT change:** the single-paragraph abstract format (conventional; the issue is sentence density, not paragraph count) and the stable terminology set (referential / self-contained / context pollution / contagious pollution) — those are used consistently and correctly.

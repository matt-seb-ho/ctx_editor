# Adversarial Review — AC3 ("Agentic Context Management for Multi-Turn Human–AI Conversations")

Reviewer stance: skeptical, rejection-oriented. Target: `writing/overleaf_repo/neurips/neurips_2026_conference.tex` (816 lines) as of the post-NeurIPS mega-table revision. Line numbers refer to that file.

**Headline verdict:** The core contribution (selective curation > blanket omission across a referentiality spectrum) is real and the mega-table strengthens it. But the revision integrated new Table 2 / Table 3 numbers into §5 **without propagating them to the Abstract, Figure 1 caption, Introduction, and Conclusion**, which still carry the *old* "tau2 is a wash / stays within trial noise" framing. Worse, two load-bearing generalization sentences in §5 ("every AC3 operator beats Baseline on every cell") are **flatly contradicted by the table printed directly above them**. These are exactly the self-inflicted, easy-to-verify errors that get a strong paper desk-rejected or savaged in rebuttal. They must be fixed before arXiv.

---

## 1. Top rejection risks (ranked)

**R1 — "Every AC3 operator beats Baseline on every cell" is false on the paper's own Table 2 (§5.1 line 328; repeated §5.4 line 358).**
Line 328 states: "every \method operator beats Baseline (full context) on every (model, benchmark) cell where we evaluated both." Table 2 (lines 289–293) contains **six** counterexamples where an AC3 operator is *below* Baseline:
- CollabLLM · Augment · Kimi: 55.4 < Baseline 57.5
- CollabLLM · Reset · gpt-5.4: 47.0 < 55.0
- CollabLLM · Reset · Kimi: 47.0 < 57.5
- CollabLLM · Rewrite · gpt-5.4: 53.8 < 55.0
- CollabLLM · Rewrite · DSV4F: 44.9 < 50.0
- tau2 · Reset(Gated) · gpt-5.4: 52.6 < 68.4
A hostile reviewer reads the table, then the sentence, and concludes the authors either did not check their own numbers or are overclaiming. This single sentence is the biggest rejection trigger in the paper. §5.4 line 358 ("every AC3 operator beats Baseline") repeats the error specifically for tau2, where Gated-Reset on gpt-5.4 (52.6) is **15.8pp below** Baseline (68.4).

**R2 — Stale tau2 framing in Abstract / Fig 1 / Conclusion contradicts the updated §5.4.**
Abstract (line 110), Fig 1 caption (line 122), and Conclusion (line 405) all still say AC3 merely "remains viable" / "stays within trial noise of vanilla on tau2-bench." But §5.4 + Table 2 now show AC3 beating Baseline by **+15.8 to +47.4pp**. The paper's own front matter undersells its strongest new result, and a reviewer will notice the internal disagreement (is tau2 a wash or a +47pp win?). See §2 table below for every instance.

**R3 — The +47.4pp headline rests on a baseline the authors themselves flag as unreliable.**
The Kimi-K2.6 tau2 Baseline (26.3) is a rate-limit-clipped floor; Table 2 caption (line 280) says "true Baseline likely 40–50%." The +47.4pp Rewrite gain (73.7 − 26.3) is therefore inflated; against a 40–50% true baseline it is ~+24 to +34pp. Yet "+47.4pp" is promoted to the Abstract's spirit, §5.4 (line 358), and §6 Discussion (lines 369, 372). Trumpeting a number whose denominator your own footnote calls a "floor" is a gift to a skeptical reviewer.

**R4 — Single-seed / best-of-3 reporting on the decisive agentic benchmark.**
Table 2 tau2 cells are N=1 (single seed) per the round summary. The gpt-5-mini tau2 cell is reported **best-of-3** (Appendix line 558: "The table reports the best-of-3 trial for Baseline and Gated-Reset"). Best-of-3 is not a defensible central estimate; it inflates both baseline and method. The "$\sim$60%" that anchors the Abstract's "60%→0%" is this best-of-3 max (seeds {45,55,60}, mean 53.3). A reviewer will demand means±CI and read best-of-3 as cherry-picking.

**R5 — Preliminary, narrow agentic evidence carrying a "spectrum" thesis.**
tau2 is a single subset (`telecom_small`), n=19–20, one domain, and the paper's own Appendix (line 558, Table `tab:tau2-failure-modes`) shows only 1 of 11 gpt-5-mini baseline failures is pollution-driven — i.e., on the model the paper studies most carefully, the mechanism the paper is about barely fires. The whole right end of Figure 1's "referentiality spectrum" hangs on this one thin, single-seed, partially-rate-limited benchmark. Reviewers who want the agentic claim will find the evidence base thin; reviewers who don't will say the spectrum is two solid points (LiC, WildChat) plus a preliminary probe.

---

## 2. Claim–evidence misalignment table

| Location | Claim (as written) | Contradicting evidence | Fix |
|---|---|---|---|
| **Fig 1 caption, line 122** | AC3 "stays within trial noise of vanilla on tau2-bench where AO collapses entirely" | Table 2 (line 291–293): AC3 best operator beats Baseline +15.8 (gpt-5.4), +26.3 (dsv), +47.4 (kimi) | Rewrite to "substantially outperforms vanilla on tau2-bench (up to +47pp), while AO collapses to 0%." The "within trial noise" line is now the *gpt-5-mini-only* sub-story, not the headline. |
| **Abstract, line 110** | "remains viable in agentic tool use where blanket omission collapses from $\sim$60\% to 0\%" | Table 2: AC3 beats Baseline by +15.8–47.4pp, not merely "viable"; "$\sim$60%" is a gpt-5-mini best-of-3 for a model absent from Table 2 (Foundry baselines span 26–68%) | Replace "remains viable" with the quantified win; make the collapse model-agnostic: "AO collapses to 0% on every respondent." |
| **Intro, line 139** | "remains viable on stateful agentic tool-use tasks … where AO catastrophically fails (60.0\%$\to$0\%)" | Same as above; "remains viable" undersells +15.8–47.4pp | Quantify the AC3 gain; drop or model-qualify the "60.0%". |
| **Conclusion, line 405** | "on tau2-bench, where AO collapses to 0\%, Gated Reset stays within trial noise of the full-context baseline rather than catastrophically failing" | Table 2 Reset(Gated) row: gpt-5.4 **52.6 < 68.4** (Gated-Reset *loses* 15.8pp), dsv 47.4 vs 31.6 (+15.8), kimi 68.4 vs 26.3 (+42.1). "Within trial noise" is false in *both* directions on Foundry respondents. | Reframe: report per-operator winners (Augment for gpt-5.4 +15.8; Rewrite for kimi +47.4). Do NOT anchor the conclusion on Gated-Reset, which underperforms Baseline on the strongest tau2 respondent. |
| **§5.1, line 328** | "every \method operator beats Baseline … on every (model, benchmark) cell where we evaluated both" | Six sub-Baseline cells in Table 2 (see R1) | Weaken to "the best AC3 operator per cell beats Baseline in every (model, benchmark) block; on CollabLLM no single operator dominates and some trail Baseline." |
| **§5.4, line 358** | "every AC3 operator beats Baseline, but the winner is model-dependent" | tau2 Reset(Gated)·gpt-5.4 = 52.6 < Baseline 68.4 | Change to "the *winning* AC3 operator beats Baseline; the lightest/heaviest operator can trail on off-profile respondents." |
| **§5.2, line 334** | "Rewrite improves over the full-context baseline on both tasks … +20pp on BigCodeBench" | True only for gpt-5-mini headline. Table 2 CollabLLM Rewrite: gpt-5.4 53.8 < 55.0, dsv 44.9 < 50.0 | Scope the claim to gpt-5-mini, or state that CollabLLM is the ambiguous mid-point where no operator dominates (the jun1 doc's own recommendation, item 3c). |
| **Conclusion, line 405 / Abstract line 110** | "wins 84–86\% pairwise on real human–AI conversations" | Table 3 (lines 309–312) spans **71.6% to 91.5%**; many cells (71.6, 72.4, 74.1, 75.0, 76.3) are below 84% | Report the honest range (~72–92%) or name the specific column. The narrow 84–86 band is not representative of Table 3. |

---

## 3. Overclaims / unsupported statements

- **Abstract line 110, "closes 55–80\% of the multi-turn gap on self-contained tasks."** Body §5.1 (line 318) only derives 80% (math) and 78% (code); the 55% (actions: (61.3−34.8)/(82.6−34.8)=55.4%) is never stated in the body. Fine numerically but the lower bound is unsourced in-text and database is excluded because it *exceeds* the oracle — so "55–80%" silently drops one of four tasks. State the per-task closures or say "3 of 4 tasks; database exceeds the oracle."
- **Abstract line 110 / §6, "pollution is contagious … downstream accuracy drops below doing nothing."** Table `tab:cognitive-hazard` (line 668): the contaminated variant is below baseline on math (40<60) and code (11<16) but **above** on database (8>4). "Drops below doing nothing" is not universal; qualify ("on math and code").
- **Intro line 139 / Conclusion line 405, "+20–42pp average" across "four model families."** This is `tab:multi-model` (GPT-5-mini, GPT-5, DeepSeek V3.2, Qwen 3.5) — a **different four models** than Table 2's Foundry set (gpt-5.4/DSV4F/Kimi), on a **hand-selected 20-hardest-instance subset** (Appendix line 513) with GPT-4o-mini user/system agents. The headline never discloses that +20–42pp is on a difficulty-selected subset, which mechanically inflates deltas. The megatable's own LiC generalization is only +13–17pp (jun1 doc 1e). A reviewer will read "+20–42pp" as favorable-subset selection.
- **§5.1 line 328, "AO collapses entirely on tau2-bench across all three."** Supported (Table 2 AO row all 0.0), but note AO=0 on Kimi is itself rate-limit-clipped (19/20 short-exits per round summary §1); the 0% is confounded with infrastructure failure on that cell. Mention this or the reviewer will.
- **§6 line 369, self-distillation absorbs the analyzer "with no inference-time call overhead."** Pure speculation citing 2026 preprints; no experiment in this paper demonstrates it. Reads as hand-waving away the method's central cost (2–3 extra LLM calls/turn). Mark clearly as future work, not a property of AC3.
- **Fig 1 caption line 122, "AO … is near-optimal at the self-contained end."** On LiC database AO=32 is beaten by AC3 Reset=48 (Table 1) — a 16pp miss at the "self-contained end." "Near-optimal" overstates; the paper elsewhere flags database as the exception.

---

## 4. Numeric inconsistencies

- **Wrong tau2 citation.** §5 Experiments line 242 cites `\citep{yao2024tau}` (τ-bench, Yao et al. 2024, arXiv 2406.12045) for "tau2-bench," while Abstract/Intro/footnote (lines 139, 168) correctly cite `\citep{barres2025tau2}` (τ²-Bench, Barres et al. 2025, arXiv 2506.07982). The line-242 description ("novel dual-control setup") is τ²-Bench specifically, so the citation is simply wrong. Fix to `barres2025tau2`.
- **n=19 vs n=20 for tau2.** Table 1 caption (line 254) and Table 2 caption (line 280) say "$n{=}19$ per cell"; Appendix line 460 says "20-task `telecom_small` subset"; Appendix line 558 reports gpt-5-mini per-trial rates in multiples of 5 (=/20). Denominators disagree across the same benchmark (Foundry cells n=19, gpt-5-mini n=20). Reconcile and state the one-task exclusion explicitly.
- **"$\sim$60%→0%" provenance.** Abstract (110), Fig 1 (122), Intro (139) all use 60% for the tau2 baseline. That is the gpt-5-mini **best-of-3** (Appendix 558). Table 2's gpt-5.4 Baseline is 68.4, dsv 31.6, kimi 26.3 — none is 60. The headline number belongs to a model not shown in Table 2. Either use the gpt-5.4 68.4→0 collapse (in-table) or make it model-agnostic ("to 0% regardless of respondent").
- **Gap-closure percentages depend on which row.** §5.1 line 318 computes gap-closure from the Gated-Reset *mean* row (80% math, 78% code). Abstract line 110 attributes 55–80% to "Gated Reset as a single operator." But the "exceeds oracle on database" fact is Reset (48.0), not Gated-Reset (38.7, which exceeds 32 only modestly). The parenthetical blends two operators; state which.
- **CollabLLM † cells mix 1-task and 2-task averages in one column.** Table 2 caption (line 280): Reset cells marked † are "MATH-Hard only" (BigCodeBench hit content filter / endpoint failures). So the Reset row's gpt-5.4 (47.0†) and Kimi (47.0†) are single-task numbers sitting in a column whose other rows average two tasks — not comparable. A reviewer will call the CollabLLM Reset comparison apples-to-oranges.

---

## 5. Evidence weaknesses a reviewer will attack

- **No error bars on the main tables.** Only the Gated-Reset LiC row has N=3 (Appendix `app:variance`, std 5–7pp). Table 1's Augment/Reset/+Memory rows and *all* of Table 2 are single point estimates. With per-cell std of 5–7pp, several highlighted LiC deltas (e.g., Augment 80.0 vs Gated-Reset 80.0 on math — literal parity) are within noise. The Limitations section (line 808) concedes "no paired significance tests," but the Abstract/Intro state hard deltas as if calibrated.
- **tau2 is single-seed except gpt-5-mini (best-of-3).** The most novel claim (agentic generalization, +15.8–47.4pp) has the weakest statistical support: N=1, one subset, one domain. The round summary's own follow-up list (§6 item 5) flags "multi-seed on tau2 headline cells … currently a single-seed read."
- **Rate-limit-clipped cells feed headline deltas.** Kimi tau2 Baseline (26.3) and AO (0.0) are clipped floors (14/20 and 19/20 short-exits). The +47.4pp Kimi Rewrite gain and the "AO=0 across all three" claim both lean on these clipped cells. Footnoted honestly, but the paper then uses the clipped numbers as if clean in the Discussion (lines 358, 369, 372).
- **Content-filter-dropped CollabLLM cells.** BigCodeBench Reset cells were unrecoverable for gpt-5.4 and Kimi (Azure content filter / Foundry instability); reported as MATH-Hard-only. This is an infrastructure gap masquerading as a data point in Table 2.
- **Best-of-3 reporting (Appendix 558).** Explicitly reporting the max of 3 seeds for Baseline and Gated-Reset on tau2 is indefensible as a central estimate and undercuts the "within trial noise" honesty elsewhere. Switch to mean±range.
- **Hard-subset selection for the +20–42pp table.** `tab:multi-model` selects the 20 hardest true-negatives per task via GPT-5.2 failure (line 513). Selecting on baseline failure inflates the achievable delta; the headline number omits this caveat.
- **Simulated users throughout.** LiC, CollabLLM, tau2 all use simulated users (Limitations line 808). WildChat is real logs but scored by an LLM judge (GPT-5-mini), and the WildChat judge/analyzer is the *same model family* as the respondent in several cells — a self-preference-bias concern the paper does not address.
- **Analyzer = assistant model in most cells.** Cost and circularity: the "separate analyzer" is the same base model as the assistant (gpt-5-mini as both; each Foundry model "serves as both assistant and analyzer," line 513). A reviewer may ask whether gains come from *more compute* rather than *decontamination* — the paper's only guard is the soft-vs-hard-attention ablation, which is gpt-5-mini-only.

---

## 6. Prioritized must-fix list for arXiv

1. **[Blocking] Delete/rewrite the false universal at §5.1 line 328 and §5.4 line 358.** "Every AC3 operator beats Baseline on every cell" is contradicted by six cells in Table 2. Replace with "the best operator per cell beats Baseline; CollabLLM is the ambiguous mid-point where operators can trail Baseline." This is the #1 desk-reject / rebuttal-loss risk.
2. **[Blocking] Propagate the +15.8–47.4pp tau2 result to Abstract (110), Fig 1 caption (122), Intro (139), Conclusion (405).** Remove "remains viable" / "stays within trial noise" as the tau2 headline; demote it to the gpt-5-mini-specific sub-story. Ensure the Conclusion does not anchor on Gated-Reset, which loses to Baseline on gpt-5.4 tau2.
3. **[Blocking] Fix the tau2 citation at line 242** (`yao2024tau` → `barres2025tau2`).
4. **[High] Qualify the +47.4pp and "60%→0%" numbers.** State the Kimi baseline is a rate-limit floor (true ~40–50%, so ~+24–34pp) at every promotion site (110, 122, 139, 358, 369, 372). Make the "60%→0%" collapse model-agnostic or switch to the in-table gpt-5.4 68.4→0.
5. **[High] Report the WildChat win-rate as an honest range (~72–92%)**, not the cherry-picked 84–86 band (Abstract 110, Conclusion 405), since Table 3 spans 71.6–91.5.
6. **[High] Replace tau2 best-of-3 with mean±range (Appendix 558);** add at least a range to Table 2 tau2 cells, or foreground the N=1 caveat in the caption rather than the appendix.
7. **[Medium] Disclose subset selection for "+20–42pp"** (hard GPT-5.2-selected subset) at every headline mention (139, 369, 405); clarify it is a *different* four models than Table 2's Foundry set.
8. **[Medium] Scope §5.2 CollabLLM claims to gpt-5-mini** and state the mid-referentiality "no operator dominates" reading; flag the † (MATH-Hard-only) cells as non-comparable in the caption.
9. **[Medium] Reconcile n=19 vs n=20 for tau2** across captions and appendix.
10. **[Low] Soften absolute overclaims:** "drops below doing nothing" (database exception), "near-optimal at self-contained end" (database), and the self-distillation "no overhead" speculation (line 369) → mark clearly as future work.

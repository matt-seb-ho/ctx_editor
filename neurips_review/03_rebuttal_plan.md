# Rebuttal Plan — AC3 NeurIPS (Sub. 27902)

Maps each concern (labels from `01_problem_summary.md` / `02_triage.md`) to a concrete rebuttal move backed by **post-NeurIPS evidence we actually have** (`neurips_review/` evidence digest). Numbers below are load-bearing — verify against the canonical source before pasting into the official response.

> **Canonical sources.** Mega-table: `docs/reports/post_may18_progress_update_v4_bandaid_tau2.html` + `docs/reports/post_may26_megatable_round_summary.md`. LiC scale-up: `docs/reports/post_may18_r3_mega_table.md`. Variance: paper `app:variance`. tau2: **n=19 Azure Foundry** numbers (not the older n=20 OpenRouter sweep). CollabLLM re-run: `docs/reports/post_neurips_r2_collabllm.md`.

---

## Strategic frame (the one sentence the AC must walk away with)

> *The reservations are about **presentation and thin statistics on the submitted version**, not the method. Since submission we (a) unified the pipeline onto a single shared analyzer, (b) scaled LiC from ~20 to ~113–150 samples/cell, (c) replaced best-of-3 with mean±std, (d) added a multi-model agentic (tau2) matrix where AC3 beats baseline by double digits while the AO baseline collapses to 0%, and (e) corrected every overclaim the reviewers flagged. The scoped conclusion the reviewers say the evidence supports is now the conclusion the paper states.*

Two moves run throughout: **concede-then-convert** (agree with the honest critique, then show the number that survives it) and **never re-defend a claim a reviewer already broke** (esp. "robust across the spectrum" and "every operator beats baseline").

---

## Per-concern battle plan

### A — "Method changes per setting" (AC's #1; Vg97, 5YHP)
**Move:** Reframe as *one analyzer, one operator family, one knob*.
- Assert the invariant: **all four benchmarks share the same two-query `ConversationAnalyzer`** (spec-extraction → approach-evaluation). Every setting instantiates the *same* operator menu {Augment, Reset, Gated-Reset, Rewrite}.
- The only thing that varies is **which operator intensity** is appropriate, and that varies *with a measurable property of the setting* — referentiality/statefulness — not with hand-tuning. Give the derived rule: **strong model / clean history → light operator (Augment); weak model / heavily-polluted history → heavy operator (Rewrite/Reset)**. tau2 shows exactly this ordering (Augment wins on gpt-5.4; Rewrite wins on Kimi).
- Provide an **"essential vs. adaptive" table** (Vg97 Q4, 5YHP W2): Essential = shared analyzer + structural exclusion where user turns self-specify. Adaptive = operator choice + whether structural exclusion applies (it doesn't when intent weaves through assistant turns, e.g. CollabLLM — that's a *principled* switch, stated a priori, not post-hoc tuning).
- **Honest concession:** the *code* is currently four implementations of that one design (LiC classes, CollabLLM Hydra port, WildChat inline, tau2 parallel repo). Frame the unification refactor as engineering-in-progress, not a conceptual gap. Do **not** claim code-level unity that doesn't exist.

### B — Statistics: best-of-3, no CIs, tiny N (all + AC)
**Move:** Show the scale-up + mean±std that already exists; promise the rest.
- **LiC N scaled ~6×:** from 18–25 to **n≈113–150 per cell** (math ~143, code ~113–125, database 147, actions 150) on the full htn50_52 pool. Several-point gaps the reviewers worried about are no longer near the resolution limit.
- **mean±std replaces best-of-3** on the variance row (LiC Gated-Reset, N=3): math **80.0±5.0**, code **64.4±7.2**, database **38.7±6.1**, actions **61.3±6.1** — and state plainly these means clear Full-Context baseline (60.0/15.8/4.0/34.8) on every task, i.e. **AC3's mean clears baseline** (directly answers iNYK Q2).
- **WildChat N=3 with tight CIs:** Reset **89.8%±1.4**, Augment **92.1%±1.3** win-rate vs AO — not best-of-3, not noise.
- **Commit** to mean±std on remaining headline cells + a paired test / bootstrap CI for camera-ready; where we can add seeds in-window (gpt-5.4-mini), do so.

### C — Table 2 hard-subset selection bias (iNYK Q1)
**Move:** Concede the inflation, then show the gain survives on the unbiased pool.
- Agree the **20-hardest-by-baseline-failure** subset + GPT-5.2-trajectory replay inflates deltas via regression-to-mean; disclose it explicitly (already done in revision).
- **The survival number:** on the **full, non-difficulty-selected** LiC pool the gain is **+13–17pp** benchmark-average (DSV4F +17.1, gpt-5.4 +16.8, Kimi +13.9 for Reset), down from the +20–42pp headline but **clearly non-zero and consistent across 3 models**. → "gains survive on an unbiased subset," which is exactly the condition iNYK set for keeping the generalization claim.
- **New experiment (highest ROI, gpt-5.4-mini):** a clean **random-subset** Reset-vs-Baseline draw (selected independently of baseline results) to answer iNYK Q1 in its exact terms. Run only if the full-pool number is judged insufficient on its own. *(feasibility check pending — see "New experiments" below.)*

### D — tau2 overclaim / within-noise (all + AC)
**Move:** Replace the broken universal claim with the true multi-model result; report honestly.
- **Retire** "the only method robust across the spectrum" → **"the only method that does not catastrophically collapse in stateful tool use."** (Already edited in the revision; say so.)
- **The real tau2 story (n=19, 3 respondents):** **AO → 0% on all three** (blanket omission deletes tool-call state); **the best AC3 operator beats Baseline on every respondent** — gpt-5.4 Augment 84.2 vs 68.4 (+15.8), DSV4F 57.9 vs 31.6 (+26.3), Kimi Rewrite 73.7 vs 26.3. This is a **double-digit multi-model win**, not "within noise."
- **Concede two things up front** so it can't be used against us: (1) **Gated-Reset specifically loses on gpt-5.4** (52.6<68.4) — that's why we now report the *best operator per cell*, not Gated-Reset as universal default; (2) the Kimi baseline was rate-limit-clipped (26.3, likely 40–50% true), so we quote the **conservative +24–34pp**, not +47pp. The "within trial noise" line now appears **only** in the correctly gpt-5-mini-scoped appendix.
- **Weakness that remains:** tau2 is still **N=1 seed**. Commit to multi-seed tau2 for camera-ready; if in-window compute allows, add seeds now.

### E — Weak/missing baselines (Vg97 Q1/Q3; AC)
**Move:** Add the cheap decisive one now; justify the rest precisely.
- **Equal-compute control (Vg97 Q3) — run it:** a self-reflection / summarizer baseline at AC3's *matched call budget* (2–3 extra LLM calls/turn), same model, + **latency** logged. This directly tests "is it decontamination or just more compute?" Our existing guard (contagious-pollution `tab:cognitive-hazard`: a *contaminated* two-stage pipeline underperforms a single-pass one) already argues it's not just compute — pair the two. *(new experiment — see below.)*
- **MT-OSC / U-Fold:** MT-OSC (arXiv:2604.08782) is concurrent (2026); state that, and adapt it as a LiC baseline **if** the method transfers to replay mode — otherwise give the precise adaptation barrier (needs live multi-turn control we don't run in replay). U-Fold is a *compaction* method for agent trajectories; note we can slot it on tau2 as an additional context-management baseline for camera-ready. Don't dismiss with "it's different" — give the mechanism-level reason.
- **ERGO** is already in as a baseline (CollabLLM) — remind them.

### F — CollabLLM ≤ AO; BigCodeBench judge (5YHP W4; Vg97)
**Move:** Show the user-sim fix flipped the result; defend the judge honestly.
- The submitted CollabLLM numbers used a **weak gpt-4o-mini user simulator that never conveyed the task spec** — an artifact, not a method failure. With a **competent (DeepSeek-V4-Flash) user-sim**: math-hard **AC3-Augment 100%** (> Baseline 95, > AO 90); bigcodebench **AC3-Reset 20%** (> AO 15 > Baseline 5). → The "AC3-Augment regresses below baseline / ties AO" finding is **withdrawn as a user-sim artifact**.
- **Concede** the mega-table averaged CollabLLM cells still don't show a *dominant* operator (mid-referentiality regime where AO stays competitive) — that's the honest scoped claim, and it's fine: our claim is *no catastrophic collapse + best-operator ≥ baseline*, not *beats AO everywhere*.
- **BigCodeBench judge:** explain the harness limitation (simulator can't pass the required function signatures → executable tests unavailable) and note v8-Rewrite **substantially beats Reset** there (gpt-5.4 17.6 vs 0, Kimi 16.7 vs 0), i.e. the judge does discriminate. Offer judge-agreement / execution-where-possible for camera-ready.

### G — Replay ≠ end-to-end (iNYK, 5YHP)
**Move:** Defend replay as the *controlled* protocol; scope the claim.
- Replay is a **deliberate apples-to-apples design**: all methods inherit an *identical* polluted trajectory, so the measured delta is purely the effect of the intervention, not of divergent user-sim paths. This is a feature for causal attribution.
- **Scope the claim** to "recovery from a fixed polluted history" where replay is used, and point to the settings we *do* run fresh/end-to-end (CollabLLM Phase-3 fresh-sim; WildChat; tau2 is genuinely multi-turn agentic). Note the fresh-sim finding (Augment "analysis pile-on" can hurt on long convos) is exactly why **gating** exists — we did stress the deployment-realistic setting.
- Commit to one end-to-end LiC run for camera-ready (full tau2 end-to-end replay scoped at ~2 dev-days → defer honestly).

### H — Analyzer not evaluated as detector (5YHP W5)
**Move:** Offer the reconstruction data we have + a pilot.
- We already have **gate-behavior data** from the Gated-Reset reconstruction (`needs_edit` flag): gate-open **≥97%** on text (LiC 97.3%, CollabLLM 98.3%); the gate only bites on agentic + strong-model text. Its failure mode is **asymmetric** — high recall for real issues, but **false-negative closes** are the main cost (WildChat gpt-5.4 Gated-Reset 74.1 < always-on Reset 88.6, −14.5pp). That's a real, honest precision/recall-flavored characterization of the detector.
- **Commit** to a small span-annotation study (stale / useful / must-preserve) with detector precision/recall for camera-ready; offer a pilot in the rebuttal window if requested.

### I — Memory mixed (5YHP W6; AC)
**Move:** Demote to optional, ablated.
- Present memory as an **optional add-on**, already ablated with honest per-setting deltas (helps math, ~neutral on code). Agree it can inject stale priors (analyzer-level pollution) — that's consistent with our own contagious-pollution finding. It is **not** load-bearing for any headline claim; commit order-sensitivity + train/eval-split analysis.

### F′ — Soft-attention gap, Appendix D (5YHP W1)
**Move:** Concede as scoped limitation — it *strengthens* the honest framing.
- Agree: structural exclusion is provably best exactly when user turns self-specify the task; where the referent lives only in assistant history, soft-attention + memory only partially closes the gap. State this as the paper's *actual* claim and name deeply-referential separation as the open problem. This candor is what earns the Tier-1 numbers their credibility.

### J — Presentation (do regardless)
- Move the structural-exclusion / contagious-pollution ablation to the **main body** (Vg97 asked). Tighten narrative (5YHP clarity=2). Align abstract/Fig 1 wording with D.

---

## New experiments (gpt-5.4-mini via TRAPI) — decision gate

Run **only** what materially moves a Tier-1/2 verdict and is not already answered by existing docs. Ranked:

| # | Experiment | Answers | Needed? | Status |
|---|---|---|---|---|
| 1 | **Random-subset** LiC Reset vs Baseline (independent of baseline failure) | iNYK Q1 (C) | Partially pre-answered by full-pool +13–17pp | Run if full-pool number deemed insufficient |
| 2 | **Equal-budget self-reflection/summarizer** baseline @ matched calls + latency | Vg97 Q3 (E) | Genuinely missing | Highest *new*-info value |
| 3 | **Multi-seed tau2** (≥3 seeds) for mean±std | iNYK Q2 / Vg97 Q2 on the agentic cell (B/D) | Genuinely missing (tau2 N=1) | Compute-heavy; camera-ready unless in-window budget |
| 4 | **Fill missing LiC seeds** → mean±std on non-Gated-Reset rows | B | Partially have | In-window if cheap |
| 5 | Span-annotation precision/recall pilot | 5YHP W5 (H) | Nice-to-have | Pilot-only |

**Gate:** before running anything, confirm the number isn't already in the mega-table / variance appendix. Spend gpt-5.4-mini only on cells that are truly empty. #2 (equal-budget) is the one net-new experiment with the clearest rebuttal payoff.

---

## What we will NOT do (and why)
- Won't re-defend "robust across the spectrum" — retired.
- Won't claim every operator beats baseline — false (6 sub-baseline cells); claim best-operator-per-cell.
- Won't claim code-level method unity — it's one *design*, four implementations.
- Won't quote +47pp on Kimi tau2 — use conservative +24–34pp (rate-limit-clipped baseline).
- Won't quote the WildChat range as "84–86%" — honest range **72–92%**.

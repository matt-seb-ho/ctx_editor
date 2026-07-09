# arXiv revision plan

Concrete, prioritized edit plan for `writing/overleaf_repo/neurips/neurips_2026_conference.tex`. Backup/rollback point: inner HEAD `d211637`, copy at `backups/neurips_2026_conference.d211637.tex`.

**Status:** v1 (pre-debate draft, from `jun1_megatable_findings.md` + direct read of the paper). A *Debate reconciliation* section will be appended once the two reviewer subagents + synthesizer land; any conflicts adjudicated there override this list.

**Guiding constraint:** this pass bakes in results we ALREADY have and improves writing. No new experiments (those live in `followup_experiments.md`). Every claim we touch must match Tables 1–3.

---

## P1 — Reconcile stale tau2 framing with Table 2 (claim–evidence bug) ★ highest value

The §5.4 Results were upgraded to the multi-model tau2 story (AC3 beats Baseline +15.8 to +47.4pp; AO→0% everywhere), but four upstream spots still say AC3 merely "remains viable / within trial noise." These contradict Table 2 and must be upgraded. Keep "within trial noise" ONLY where it is correctly scoped to the gpt-5-mini cell (l.360, l.558).

| # | Location | Current (stale) | Change to |
|---|---|---|---|
| P1a | **Abstract**, l.110 | "remains viable in agentic tool use where blanket omission collapses from $\sim$60\% to 0\%" | AC3 *substantially outperforms* Baseline on tau2 (AO collapses to 0% across every respondent; AC3 +16–47pp over Baseline). Make the "60%" respondent-agnostic (also jun1 §2d). |
| P1b | **Fig 1 caption**, l.122 | "stays within trial noise of vanilla on tau2-bench where AO collapses entirely" | "substantially outperforms vanilla on tau2-bench (AO collapses to 0%)". NOTE: Figure 1 is a *schematic*; also check the figure art itself doesn't draw AC3≈vanilla at the tau2 end — if it does, flag for a figure redraw (may defer to followups if art regen is heavy). |
| P1c | **Introduction**, l.139 | "remains viable on stateful agentic tool-use tasks … where AO catastrophically fails (60.0\%$\to$0\%)" | AC3 beats Baseline substantially on tau2 while AO→0%; cite the +16–47pp range and Table 2. |
| P1d | **Conclusion**, l.405 | "on tau2-bench, where AO collapses to 0\%, Gated Reset stays within trial noise of the full-context baseline rather than catastrophically failing" | AC3 *beats* full context on tau2 (+16–47pp, operator-by-respondent) while AO→0%. Fold into the two-point conclusion (P3a). |

Also verify the §6 Discussion opening (l.369) already states the +15.8–47.4pp range — it does; keep as the anchor the others point back to.

## P2 — Apply remaining `jun1` "not yet applied" items

- **P2a (jun1 2c):** §3.2 Rewrite bullet (l.211) — soften "with a ceiling we expect to surpass deterministic mapping over time." Present-day evidence (WildChat×Kimi 91.5 > Reset 71.6; tau2×Kimi 73.7) already shows Rewrite winning on the referential end. Reword to "already surpasses deterministic mapping on the most referential settings (Table 3)."
- **P2b (jun1 2d):** Abstract "$\sim$60\% to 0\%" → respondent-agnostic (merged into P1a): "AO collapses to 0% regardless of respondent."
- **P2c (jun1 3b):** §3.2 first sentence (l.207) — add a pointer that operator choice is respondent-dependent, cite Table 2. Reinforces "analyzer is the contribution; operators are knobs."
- **P2d (jun1 3c):** §5.2 CollabLLM (l.334) — currently a tight paragraph; expand slightly to land "CollabLLM is the referentiality-midpoint where AO stays competitive and no single AC3 operator dominates" using the per-respondent Table 2 numbers (DSV4F Rewrite 44.9 < Augment 57.5), rather than reading as an awkward mixed-result note. Keep honest.

## P3 — Conclusion + Discussion upgrades

- **P3a (jun1 3a):** Rewrite the Conclusion to land TWO points, not one:
  1. Selective curation (any AC3 operator) > blanket removal (AO), across the referentiality spectrum.
  2. Among operators, intensity should match respondent capability (light Augment for strong, heavy Rewrite for weak); one shared analyzer supports both.
  Currently the conclusion only makes point 1 and repeats the stale tau2 "trial noise" line (P1d).
- **P3b:** Ensure the Discussion "Appropriate intensity" paragraph (l.371) and the Conclusion don't redundantly state the same thing — Discussion keeps the mechanism, Conclusion states the takeaway.

## P4 — Writing polish for arXiv (skill-guided; refine with debate)

- **Abstract readability:** it's one ~250-word paragraph. Consider light internal restructuring (problem → method → the contagious-pollution twist → results-across-referentiality → takeaway) without splitting into multiple paragraphs if venue style prefers one block. Defer final call to writing-editor debate output.
- **Terminology consistency:** audit "Gated Reset" vs "Gated-Reset", "\method" rendering, AO defined on first use, operator names. (Writing editor agent is checking this.)
- **Flow:** apply the highest-impact before→after rewrites the writing-editor agent proposes, subject to keeping every number aligned with the tables.

## Explicitly OUT of scope this pass
- New experiments / new table cells → `followup_experiments.md`.
- Figure *art* regeneration (Fig 1 schematic, method figure) unless a caption fix forces a trivial art change — flag heavy redraws as follow-ups.
- Renaming the method (AC3 stays).

## Apply order
1. P1 (tau2 reconciliation) — abstract, fig caption, intro, conclusion.
2. P2 (jun1 items).
3. P3 (conclusion two-point + discussion dedupe).
4. P4 (polish from debate).
5. Adversarial self-review pass (skill `paper-review.md`) → fix residual claim-evidence gaps.
6. Commit to inner repo (Conventional Commits), one commit per coherent group.

---
## Debate reconciliation (v2 — FINAL, drives the edits)

The adversarial debate (`debate/01`, `02`, `03_synthesis.md`) upgraded the plan. Net additions beyond v1, in apply order. **The synthesis (`debate/03_synthesis.md`) is authoritative where it conflicts with v1.**

### Blocking (do first)
- **B1 — Kill the false universal.** §5.1 l.328 and §5.4 l.358: "every AC3 operator beats Baseline on every cell" is contradicted by 6 cells in Table 2. → "the *best* operator per cell beats Baseline; on CollabLLM no single operator dominates and some trail Baseline." (Overrides v1's implicit acceptance of the jun1 phrasing.)
- **B2 — tau2 reconciliation (P1a–d)**, but with two corrections from the debate: (i) make the AO collapse **model-agnostic** ("0% on every respondent"), not "~60%→0%"; (ii) the **Conclusion must use per-operator winners, NOT Gated-Reset** (which loses 15.8pp to Baseline on gpt-5.4 tau2).
- **B3 — Citation fix** l.242 `yao2024tau` → `barres2025tau2`.

### High
- **H1 — Qualify +47.4pp / Kimi baseline** as a rate-limit floor wherever promoted (l.358, 369, 372); lead with clean gpt-5.4 (+15.8) / DSV4F (+26.3).
- **H2 — WildChat range**: "84–86%" → honest "wins in every cell (72–92%)" (Abstract l.110, Conclusion l.405).
- **H3 — De-hedge Rewrite** (§3.2 l.211) per jun1 2c + writing R3.
- **H4 — Conclusion two-point + limitation sentence** (jun1 3a + writing R6), using per-operator winners.
- **H5 — Disclose "+20–42pp"** is a difficulty-selected subset / different 4 models (l.139, 369, 405).

### Medium / polish
- **M1 — §5.2 CollabLLM**: scope to gpt-5-mini + "mid-referentiality, no operator dominates" (jun1 3c).
- **M2 — Terminology sweep** (writing R8): `AC3`→`\method` l.358; standardize "Gated Reset"; AO defined once (l.122/233 → match l.127).
- **M3 — Split overlong sentences**: Intro l.139 (writing R4), self-distillation l.369 (writing R7). Abstract S4 grammar (writing R1). Intro enum capitalization l.135 (writing R5).
- **M4 — Reconcile n=19 vs n=20** tau2 across captions/appendix.
- **M5 — Soften absolutes**: "drops below doing nothing" → "on math and code"; "near-optimal at self-contained end" (database exception); self-distillation "no overhead" → mark future work.

### Decision log
- Chose **honest/conservative framing over jun1-optimistic** on B1 and H1 (the numbers stay in the tables; only the prose claims soften to match). Rationale in `debate/03_synthesis.md`. Rollback-friendly via backup + per-group commits.
- Keep single-paragraph abstract; keep method name AC3; no figure-art regen this pass.

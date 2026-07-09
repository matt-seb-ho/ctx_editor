# Debate synthesis & adjudication (round 2)

Reconciles the two independent reviews with the `jun1_megatable_findings.md` framing (the "author-optimistic" integration already in the draft). Written by the orchestrator (Opus) with full context including the ground-truth numbers. This is the ruling that drives `arxiv_revision_plan.md` v2 and the actual edits.

Inputs:
- `debate/01_reviewer_skeptic.md` — claim–evidence & rejection risks (reviewer A).
- `debate/02_writing_editor.md` — flow/clarity/terminology (reviewer B).
- `../jun1_megatable_findings.md` — what the mega-table added + which edits were "done."

## Where the reviewers agree (accept wholesale)
- **Stale tau2 framing** in Abstract (l.110), Fig 1 caption (l.122), Intro (l.139), Conclusion (l.405) contradicts the updated §5.4/Table 2. Both flag it. → **Fix (blocking).**
- **De-hedge the Rewrite operator** (§3.2 l.211): drop "we expect… over time," state the present-day win. Both flag it; matches jun1 2c. → **Fix.**
- **Conclusion needs the "appropriate intensity" second point** + a limitation/future sentence. Both flag it; matches jun1 3a. → **Fix.**

## The core tension the debate surfaced (author-optimism vs rigor)
The draft + `jun1` promote two claims the skeptic shows are **overclaims against the paper's own tables**:

1. **"Every AC3 operator beats Baseline on every cell"** (l.328, l.358). Table 2 has **six sub-Baseline cells** (CollabLLM Augment·Kimi 55.4<57.5; Reset·gpt-5.4 47.0<55.0; Reset·Kimi 47.0<57.5; Rewrite·gpt-5.4 53.8<55.0; Rewrite·DSV4F 44.9<50.0; tau2 Gated-Reset·gpt-5.4 52.6<68.4). **Ruling: skeptic wins decisively.** This is a self-inflicted desk-reject risk. Replace with "the *best* operator per cell beats Baseline; on CollabLLM no single operator dominates and some trail Baseline." Overrides the jun1/draft phrasing.

2. **"+47.4pp" and "~60%→0%"** promoted to headline. The +47.4pp uses a Kimi baseline the caption itself calls a rate-limit-clipped "floor" (true ~40–50% ⇒ real gain ~+24–34pp); the "60%" is a gpt-5-mini *best-of-3* for a model absent from Table 2. **Ruling: skeptic wins.** Keep the tau2 win as the headline (it IS strong and real), but (a) lead with the *clean in-table* gpt-5.4 (+15.8pp) and DSV4F (+26.3pp) gains, (b) present the range as "+15.8 to +47.4pp" only where we can immediately note the Kimi baseline is a rate-limit floor, and (c) make the AO collapse **model-agnostic** ("AO collapses to 0% on every respondent") instead of citing the best-of-3 "60%".

## Additional skeptic findings accepted (not in jun1)
- **Conclusion must NOT anchor on Gated-Reset** — it *loses* 15.8pp to Baseline on gpt-5.4 tau2. Use per-operator winners (Augment for strong, Rewrite for weak). **Accept (blocking).**
- **WildChat "84–86%" is cherry-picked** — Table 3 spans 71.6–91.5. Report the honest range / "wins in every cell (72–92%)." **Accept.**
- **Wrong citation** l.242 `yao2024tau` → `barres2025tau2`. **Accept (blocking, trivial).**
- **"+20–42pp" is a *different* 4 models on a difficulty-selected subset** (Table 5), not the mega-table set; the mega-table's own default-subset LiC generalization is only +13–17pp. Disclose the subset at headline mentions. **Accept.**
- **§5.2 CollabLLM** claims are gpt-5-mini-only; scope them and state the "mid-referentiality, no operator dominates" reading (also jun1 3c). **Accept.**
- **n=19 vs n=20** tau2 denominator disagreement across captions/appendix. Reconcile (Foundry cells n=19, one task excluded; gpt-5-mini diagnostic n=20). **Accept.**
- Soften absolute overclaims: "drops below doing nothing" (database is an exception in `tab:cognitive-hazard`), "near-optimal at self-contained end" (database), self-distillation "no overhead" (mark as future work). **Accept as polish.**

## Writing-editor findings accepted (not claim-level)
- Abstract S4 grammar fix (missing verb); terminology sweep (`AC3`→`\method` at l.358; standardize "Gated Reset" spelling; AO defined once); split the 90-word Intro sentence (l.139) and the self-distillation sentence (l.369); Intro enumeration capitalization (l.135). All **accept** — mechanical, low-risk. Keep the single-paragraph abstract (don't split).

## Net effect on the "story"
The honest framing is still a strong paper and arguably *stronger* because it's rebuttal-proof: **selective curation beats blanket omission across the referentiality spectrum; AO collapses to 0% on every agentic respondent; the best AC3 operator beats full context on tau2 by double digits, and the right operator scales with respondent strength — but no single operator dominates the ambiguous mid-referentiality (CollabLLM) regime.** This tightens, rather than weakens, the contribution.

## What I deliberately did NOT change (flag for Matthew)
- I did **not** invent new numbers or re-run anything; every edit either (a) matches a number already in a table, or (b) softens a claim to match the tables. Deferred experiments that would let us *re-strengthen* some claims (multi-seed tau2, clean Kimi baseline, WildChat Gated-Reset fills) are in `followup_experiments.md`.
- I chose the **honest/conservative** framing over the jun1-optimistic one wherever they conflict (items 1–2 above). If you prefer to keep the punchier numbers, the backup at `backups/neurips_2026_conference.d211637.tex` + the per-group commits make selective rollback easy.

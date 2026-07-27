# Paper Edits — status & handoff (for the rebuttal)

The rebuttal comments (`05_comment_drafts.md`) commit to specific paper changes. This tracks which are **already in the `.tex`**, which I **applied this session**, and which are **still TODO** (commitments the rebuttal makes in future tense). Target file: `writing/overleaf_repo/neurips/neurips_2026_conference.tex`.

> **Sync caveat:** the Overleaf remote is currently **unreachable** (`git -C writing/overleaf_repo pull` fails). All edits below are committed **locally in the inner repo only** and must be pushed when the remote returns. Confirm with co-authors before pushing (collaborator-visible).

## Already in the `.tex` (verified this session) — cite as done
- **mean±std variance table** (Appendix `app:variance`, lines ~496–499): math 80.0±5.0, code 64.4±7.2, database 38.7±6.1, actions 61.3±6.1. ✓ matches rebuttal.
- **tau2 reconciled framing**: abstract/intro/Fig-1 say AO "collapses to 0%" and best AC3 operator "beats full context by double-digit margins per respondent." ✓
- **WildChat range "72–92%"** (abstract + intro). ✓
- **Hard subset disclosed** as "difficulty-selected LiC subset" + "15 of 16 model–task pairs" (intro line 139). ✓
- **Baselines** AO / Concat-User / ERGO named (Sec. experiments, line ~233). ✓

## Applied this session (committed locally, inner repo `b1a629a`, NOT pushed)
- **Overclaim softened.** Reviewers explicitly quoted "the only method robust across the spectrum" as an overclaim.
  - Abstract (line 110): `the only approach robust across the spectrum:` → `the only approach that improves over full context across the entire spectrum:`
  - Intro (line 139): `the only method that holds up across the spectrum` → `the only method that improves over full context across the entire spectrum`
  - Rationale: "improves over full context" is precisely true (best operator per cell beats FC on all four regimes; AO collapses on tau2) and removes the "robust = within-noise" ambiguity iNYK objected to. Minimal, preserves flow.
  - **If you disagree**, revert with `git -C writing/overleaf_repo revert b1a629a`.

## TODO — commitments the rebuttal makes (do before camera-ready / ICLR; phrased as future tense in the drafts)
These are NOT yet in the `.tex`. The rebuttal promises them; they are the ICLR-revision spine (see `strategy.md`).
1. **Essential-vs-adaptive component table** + a one-paragraph unified "AC3 algorithm" statement (answers the #1 generalizability concern). *High priority.*
2. **Move the structural-exclusion / contagious-pollution ablation to the main body** (Vg97 requested; currently `tab:cognitive-hazard` context). 
3. **Rename tau2 "strategic reflection"** in-text to make continuity with the shared analyzer explicit (it's the same analyzer + tool-state tracking, not a new method).
4. **Add ≥1 strong external baseline** where adaptable (MT-OSC on LiC-style; U-Fold on tau2) or a precise adaptation-barrier justification.
5. **Fold in the new experiments** from this session: random-subset end-to-end (gpt-5.4-mini) result answering iNYK Q1 + concern G; equal-budget reflection control answering Vg97 Q3. (Numbers in `experiments/exp*_results.txt`.)
6. **Demote memory** to an explicitly-optional, ablated add-on with honest per-setting deltas (5YHP W6).
7. **Analyzer-as-detector** precision/recall study (5YHP W5) — the single change most likely to raise the *Quality* score; commit for camera-ready with a pilot if possible.
8. **Qualify the "Gated-Reset is the safe default" line** — it loses to always-on Reset on strong-model text (WildChat gpt-5.4 −14.5pp) and to baseline on tau2 gpt-5.4; the honest claim is "best operator per cell," gated as a conservative default only where the gate rarely closes wrongly.

## Numbers NOT to reintroduce (internal-consistency guardrails)
- Don't say "every AC3 operator beats baseline" — 6 sub-baseline cells exist; say **best operator per cell**.
- tau2 Kimi gain: quote **conservative +24–34pp** (baseline was rate-limit-clipped), not +47pp.
- tau2 canonical numbers = **n=19 Azure Foundry** sweep (not the older n=20 OpenRouter one).

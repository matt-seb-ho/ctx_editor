# PAPER_EDITS — ready-to-apply edit specification for PAPER-1..11

**Task T31b, 2026-07-29 (autoresearch session 2).** Written incrementally; sections are filled in
priority order (posting-blocking first, then effort-to-value).

**Target file for every item unless stated otherwise:**
`writing/overleaf_repo/neurips/neurips_2026_conference.tex` (815 lines at time of writing).
That directory is a **separate git repo** synced to Overleaf and shared with Lianhui and Michel.
Nothing in this document has been applied. Pull first:
`git -C writing/overleaf_repo pull origin main`.

**How to use.** Each item gives: location + stable anchor, the *current* text quoted exactly from
the file as it stands tonight, the *replacement* text ready to paste, the finding ID and artifact
path behind every number, whether it blocks posting, and effort/risk. Where an item needs an
authorial decision rather than a mechanical substitution, it is labelled **JUDGEMENT CALL** and
the options are laid out instead of a single replacement.

**Verification standard.** Every number below was re-checked against a finding ID in
`neurips_review/autoresearch/WORKLOG.md` and, where possible, against the artifact on disk.
Numbers that could not be confirmed are flagged in-line and recorded in
`neurips_review/autoresearch/tasks/T31/worklog.md`.

---

## Status board

| ID | One-line | Blocks posting? | Status in this doc |
|---|---|---|---|
| **PAPER-7** | ERGO scored on unfiltered pools in `tab:main`; math 69.6 → **80.0**, code ≈44.0, database 12.0, actions uncorrectable | **YES — the only blocker** | ⏳ |
| **PAPER-9** | `tab:main` caption must disclose the top-25-by-failure-rate instance selection | No (camera-ready) | ⏳ |
| **PAPER-1** | LiC/CollabLLM "seeds" → "replicate runs (temperature 1.0)"; WildChat + tau2 keep "seeds" | No | ⏳ |
| **PAPER-8** | Table 3 / §gated "on the same prefixes" is false; 35 shared prefixes, McNemar p=0.125 | No | ⏳ |
| **PAPER-4** | CollabLLM MATH-Hard "100" → "matches Baseline" (91.7 vs 91.7) | No | ⏳ |
| **PAPER-3** | `+ Memory` rows are single-trial below a ~6 pp noise floor — soften or re-run | No | ⏳ |
| **PAPER-2** | Appendix cites `docs/multi_run_variance_2026-05-07.md`, which never existed | No | ⏳ |
| **PAPER-10** | AO / Concat-User in end-to-end mode are baselines, not upper bounds | No | ⏳ |
| **PAPER-6** | Drop per-run `adjusted_accuracy`; report raw; fix the "all user simulator messages" sentence | No (do before arXiv) | ⏳ |
| **PAPER-5** | Retract "preserve what's correct and remove what's harmful"; rewrite the ERGO differentiation | No | ⏳ **JUDGEMENT CALL** |
| **PAPER-11** | Withdraw the tau2 improvement claim across abstract, Fig. 1, intro, `tab:megatable`, §tau2-results, discussion, conclusion | No | ⏳ **INVENTORY + JUDGEMENT CALL** |

⏳ = not yet written · ✅ = fully specified, paste-ready · ⚖ = options presented, needs Matthew

---

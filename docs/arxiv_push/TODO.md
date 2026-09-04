# AC3 arXiv v1 — remaining work TODO

**Owner:** Matthew (matt-seb-ho). **Created:** 2026-09-04 during the internship-end preservation
sprint. This is the punch-list to take the arXiv preprint from "content-fixed, pushed to Overleaf"
to "posted." Sources: `docs/arxiv_push/REVIEW_FINDINGS_2026-09-04.md`,
`docs/arxiv_push/STATE_REPORT_2026-09-03.md`, `docs/arxiv_push/nice_to_have_experiments.md`.

Target file for all paper edits: `writing/overleaf_repo/arxiv/neurips_2026_conference.tex`
(inner repo → mgalley Overleaf remote). Pull `--rebase` before editing; push with the
`id_ed25519_deux` key.

## Already done (2026-09-04, pushed to Overleaf `be5b6d6`)
- [x] **B1** — Table 2 tau2 block rebuilt from the re-measured N=3 matrix (no invented numbers).
- [x] **S1–S3** — LiC headline reconciled to the appendix N=3 means: Table 1 Gated-Reset row
      (code 63.2→64.4, actions 66.7→61.3), headline `67–82%`→`55–84%`, code closure →84%.
- [x] **S5** — fixed the broken GPT-5-mini cross-ref in the CollabLLM appendix.
- [x] Copyedit pass (terminology/casing; "Gated Reset" hyphenation largely swept).

## HARD BLOCKERS — must clear before any public post
- [ ] **Author block.** `arxiv/neurips_2026_conference.tex` ~l.62–65 is still
      `\author{ Anonymous Authors }` with `% TODO(authors)`. Fill real names / order /
      affiliations. **Only the authors can supply this.**
- [ ] **Figure 1 art vs. corrected tau2 caption.** `assets/ctxe_story.drawio.png` still draws
      AC3 ≥ vanilla at the tau2 (stateful) end; the corrected caption says AC3 *remains viable but
      does not exceed full context* there. Redraw so the tau2 bar shows parity/slightly-below.
      Untracked candidates `assets/fig1_bars_gpt54.{pdf,png}` (+ `_h2h`) exist — confirm whether
      they are the intended replacement. `.drawio` source is missing from the repo.

## SHOULD-FIX before post
- [ ] **S4 — MT-OSC citation + expansion.** `\section` ~l.337 and "we reimplemented MT-OSC"
      ~l.342 have no `\cite` and never spell out the acronym. **Matthew is fetching the citation.**
      Add the reference + first-use expansion.
- [ ] **S6 — abstract "only method" scope.** Abstract claims AC3 is the only method that improves
      over full context on every referential benchmark, but Table 2 shows AO also beats Baseline on
      all three CollabLLM respondents, and the body calls CollabLLM "mixed." Scope the claim to
      LiC/WildChat or add the CollabLLM caveat.

## MINORS
- [ ] **M1** — Augment code value 52.6 (Table 1) vs 55.6 (appendix reading ~l.539). Reconcile.
- [ ] **M2** — l.323 "+5.5–8.8pp" over Augment on code; Table 1 gives +5.3 to +10.6. Fix range.
- [ ] **M3** — `S0`/`S1`/`S2` operator labels used in appendix (~l.523+) but never defined in-paper
      (body uses Augment/Reset/Rewrite). Add a one-line mapping.

## HYGIENE
- [ ] Delete stale `neurips/neurips_2026_conference_v2.tex` (May-9 mockup, mis-named; untracked).
- [ ] Redundant `arxiv/assets/prompts/` copy (Overleaf resolves `assets/` from root; drift risk).
- [ ] Remove stray `assets/temp` (87-byte scratch file).

## PROVENANCE (confirm-before-final)
- [ ] **FLAG-1** — MT-OSC "edits context in only 6 of 107 conversations": confirm a single source
      artifact, or fall back to the call-based "~30 firings across 107 (0.3/conv)".
- [ ] **FLAG-2** — LiC per-cell floor: draft prints the safe ceiling "up to 150/cell"; the 113
      lower bound was only asserted in a handoff, not traced to a RESULTS count.

## v2 (future work — NOT required for v1)
See `docs/arxiv_push/nice_to_have_experiments.md` §C, ranked. Highlights: root-cause the unexplained
gpt-5.4 tau2 cell; real-user eval; tau2 beyond `telecom_small`; CollabLLM/WildChat N>1 reruns;
U-Fold + high-pollution self-reflection arms; analyzer self-distillation probe.

## Preservation status (2026-09-04 sprint)
- [x] Outer `ctx_editor` (code + `neurips_review/` rebuttal artifacts) pushed → `matt-seb-ho/ctx_editor`.
- [x] Paper repo pushed → mgalley Overleaf remote.
- [x] `~/ac3` produced data + full paper repo tarballed → `srv6:/data/matt/ac3_backup_20260904/`.
- [ ] **Private matt-seb-ho mirror of the paper repo** — needs a repo to be created (no `gh`/token
      on the machine). Once `matt-seb-ho/<name>` (private) exists:
      `git -C writing/overleaf_repo remote add mattbackup git@github.com:matt-seb-ho/<name> && \`
      `GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_deux -o IdentitiesOnly=yes" git -C writing/overleaf_repo push mattbackup --all`

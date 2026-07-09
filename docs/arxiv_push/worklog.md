# arXiv push — work log

Rolling log of the post-NeurIPS → arXiv revision session. Newest entries appended. Author: Claude (Opus 4.8), driving autonomously overnight for Matthew.

---

## Session 2026-07-09 (overnight)

### Goal
Recover the project after loss of the contractor server, bake the post-NeurIPS mega-table results/findings into the paper, improve the writing, and get the draft into arXiv shape. Matthew asleep; working autonomously.

### Orientation & recovery (done earlier this session)
- Read `docs/index.md`, `jun1_megatable_findings.md`, `post_may26_megatable_round_summary.md`, and the full paper.
- **Recovered the live paper** `writing/overleaf_repo/` from the Azure blob's `ctx_editor_full_snapshot_2026-06-12.tar.gz` (it was gitignored → absent from the GitHub backup). Full `.git` intact, HEAD `d211637`. Verified the mega-table (Tables 2/3, §5.3–5.4, §6) is present.
- Confirmed: mega-table data is fully in-repo; Claude sessions were never backed up; Overleaf remote (`mgalley/...`) is unreachable from this machine.
- Wrote `state_of_project.md` (get-back-up-to-speed overview).

### Backup (rollback point)
- Inner-repo HEAD before any edits: **`d21163728cfa64be27851deedfd4d9a10ad271ea`** (`d211637`), working tree clean except pre-existing untracked assets.
- Physical copy: `docs/arxiv_push/backups/neurips_2026_conference.d211637.tex` (+ `.bib`).
- Rollback = `git -C writing/overleaf_repo checkout neurips/neurips_2026_conference.tex` (to d211637) or restore from the backup copy.

### Core finding driving the revision
The mega-table results were integrated into §5, but the **Abstract (l.110), Figure 1 caption (l.122), Introduction (l.139), and Conclusion (l.405)** still frame tau2-bench as AC3 merely *"remains viable / within trial noise of baseline."* This now **contradicts Table 2**, where every AC3 operator beats Baseline by **+15.8 to +47.4pp**. The "within trial noise" phrasing is only valid for the *gpt-5-mini* cell (l.360, l.558) and must be scoped there. Fixing this claim–evidence misalignment is Priority 1.

### Adversarial debate (in progress)
- Spawned two independent reviewer subagents (persisted to `debate/`): `01_reviewer_skeptic.md` (claim–evidence + rejection risks) and `02_writing_editor.md` (flow/clarity per the research-paper-writing skill).
- Next: a synthesizer subagent reconciles both → I finalize `arxiv_revision_plan.md` → apply edits → adversarial self-review → commit to inner repo.

### Where artifacts live
- Plan: `docs/arxiv_push/arxiv_revision_plan.md`
- Debate: `docs/arxiv_push/debate/`
- Follow-up experiments (deferred): `docs/arxiv_push/followup_experiments.md`
- Blob tarballs: `/home/t-matthewho/ac3/blob_staging/`

### Debate outcome (round 2)
Two independent reviewers landed:
- `debate/01_reviewer_skeptic.md` — found the P1 stale-tau2 framing AND a more serious internal contradiction I'd missed: **"every AC3 operator beats Baseline on every cell" is false on Table 2** (6 sub-Baseline cells), and the Conclusion anchored on **Gated-Reset, which loses 15.8pp to Baseline on gpt-5.4 tau2**. Plus: +47.4pp rests on a rate-limit-clipped baseline; WildChat "84–86%" cherry-picks a 71.6–91.5 range; wrong tau2 citation; "+20–42pp" is a different-models hard subset.
- `debate/02_writing_editor.md` — reverse outline of abstract/intro/conclusion, terminology sweep, 8 concrete before→after rewrites.

I wrote `debate/03_synthesis.md` adjudicating the **author-optimistic (jun1) vs rigor (skeptic)** tension. Ruling: took the honest/conservative framing everywhere they conflict — numbers stay in the tables; prose claims soften to match. This tightens the paper and removes rebuttal-bait.

### Edits applied (committed inner repo `ef40b01`, parent `d211637`)
All edits are in `writing/overleaf_repo/neurips/neurips_2026_conference.tex`. Net: 19 lines changed. Summary in the commit body. Highlights:
- tau2 framing reconciled across Abstract / Fig1 caption / Intro / Conclusion.
- False universal removed (Sec 5.1, 5.4) → best-operator-per-cell.
- Conclusion → two-point message, no Gated-Reset anchor, + limitation sentence.
- WildChat honest range (72–92%); +47.4pp Kimi caveat; +20–42pp subset disclosure.
- Rewrite de-hedged; CollabLLM scoped to gpt-5-mini; tau2 citation fixed.
- Cognitive-hazard "below baseline" scoped to math/code (database is the exception, per Table 6).
- Grammar/terminology polish (AC3→\method, AO defined once, sentence splits).

Self-review: residual grep confirms no stale "84–86 / every operator / +20–42pp average / 60%→0%" in the body; "within trial noise" survives only in the two correctly gpt-5-mini-scoped spots (l.360, l.558). Braces balanced; all new `\ref` targets exist. **No LaTeX toolchain on this machine**, so I could not do a real compile — a compile check is advised before posting.

### ⚠ Known issues needing Matthew's attention
1. **Figure 1 art (`assets/ctxe_story.drawio.png`) may contradict its new caption.** The caption now says \method "substantially outperforms vanilla across the spectrum, including on tau2-bench." If the schematic still draws the \method curve flat / near-vanilla at the tau2 end (the old "within trial noise" story), the art needs a redraw to show \method above vanilla at the tau2 end. I could not inspect/edit the drawio PNG. **Please eyeball the teaser.**
2. **Overleaf sync still blocked** — the `mgalley/...` remote is unreachable from this machine; commits are local only. Push path must be sorted before these land on Overleaf.
3. **"Gated Reset" vs "Gated-Reset" hyphenation** left mixed (13 vs 20). Cosmetic; deferred to a final copyedit to avoid risky global churn.
4. **Deeper claims still rest on thin evidence** (single-seed tau2, best-of-3 gpt-5-mini, rate-limit-clipped Kimi cells). Softened in prose but the fix is re-running — see `followup_experiments.md` items 1–3. If you want the punchier numbers back, they need those reruns.
5. **The abstract now avoids a hard tau2 baseline number** (says "double-digit margins" not "60%→0%"). If you prefer a concrete number, use the in-table gpt-5.4 68.4→0 collapse rather than the old best-of-3 60.

### Status
Tasks 1,3–10 complete. Task 2 (pull tau2_ctxe/collabmem raw outputs) intentionally left pending — not needed for this pass. Rollback: `git -C writing/overleaf_repo revert ef40b01` or restore `backups/neurips_2026_conference.d211637.tex`.

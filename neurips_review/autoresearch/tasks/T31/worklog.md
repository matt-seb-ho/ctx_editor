# T31b worklog — building `PAPER_EDITS.md`

**2026-07-29, autoresearch session 2. Zero API calls. No file under `writing/overleaf_repo/` was
written; no git command was run against that repo.** Deliverable:
`neurips_review/autoresearch/PAPER_EDITS.md`, committed incrementally in six commits from
`2772f8b` onward.

## Method

Read `HANDOFF.md` §4 for the item list, then for every item located the text in the **current**
`writing/overleaf_repo/neurips/neurips_2026_conference.tex` (815 lines) rather than trusting the
line numbers recorded earlier tonight, and re-derived every number from a finding ID plus, where
possible, the artifact on disk. Line numbers in `PAPER_EDITS.md` are from a full read of the file
performed at the start of this task.

## Numbers verified independently rather than copied

| Number | Where it was asserted | What I found |
|---|---|---|
| ERGO math 80.0 | HANDOFF, v5 ×5 | Confirmed. `tasks/T18/ergo_row_closed.json` → `k=0.0, kruns [0,0,0], closed:true` |
| ERGO code ≈44.0 | HANDOFF | Confirmed as **43.9**, interval [42.1, 47.4], `k=2.6667, kruns [3,2,3]` |
| ERGO actions [43.5, 52.2] | HANDOFF | Confirmed; `closed:false`, `t18: null` |
| "no actions sidecar has ever existed" | F43 | **Confirmed directly on disk**: `data/baseline_traces_v2/` holds `math_`, `code_`, `database_false_negatives.json` and no actions file |
| FN classifier sees only visible user turns | F41 | **Confirmed in source**: `src/ctx_editor/identify_false_negatives.py`, `format_user_messages` → `[m for m in messages if m.get("role") == "user"]` |
| code gap-closure 78% → 82% | HANDOFF (as a PAPER-7 consequence) | Arithmetic reproduces — **but it is a consequence of defect D2, not of the ERGO fix.** (64.4−15.8)/(77.8−15.8)=78.4%; (63.2−15.8)/(73.7−15.8)=81.9% |
| "closes 55–80%" → "67–82%" | HANDOFF (same) | Reproduces, same caveat: lower end is the actions cell moving 61.3 → 66.7 under D2 |
| tau2 re-measured matrix | F78–F81 | Cross-checked `replies/v5/00_general_response.md` CW4 against `HANDOFF.md` §2 row 0 — consistent |

## Items where HANDOFF's description does not match the paper

Recorded here because the mismatch is the finding, not an error in the reading.

1. **PAPER-1.** `grep seed` over the `.tex` and `checklist.tex` returns exactly two hits, both
   tau2 (L360, L558), and per F81 tau2 **keeps** the word. The LiC/CollabLLM passages already say
   "$N{=}3$ replay-mode reruns" at temperature 1.0. The F4 defect lived in launcher scripts and
   rebuttal drafts. Reduced to one limitations sentence.
2. **PAPER-4.** The string `100` does not occur anywhere in the 815-line `.tex`. The 100% was a v4
   rebuttal claim, never a paper claim. Closed as not-applicable.
3. **PAPER-2.** `grep -rn "multi_run_variance\|paper_experiments_provenance" writing/overleaf_repo/`
   returns **nothing**. The dangling links are in `docs/paper_experiments_provenance.md` (L41, 45,
   138) and `docs/index.md` (L140, 250) — outer repo. Not a paper edit.
4. **PAPER-10.** No table reports AO/Concat-User end-to-end; L456 states all LiC strategies run in
   replay mode. Downgraded to an optional caption line that *strengthens* the paper.
5. **PAPER-9's drafted caption is wrong twice** (see below).

## Things nobody had flagged

1. **The drafted PAPER-9 caption is factually wrong on two counts.** `tasks/T24/worklog.md` §7.4
   and HANDOFF both propose *"the 25 per task with the highest full-context failure rate across
   five GPT-5-mini baseline runs."* Per `docs/lic_dev_set_provenance.md`: **math had only 23
   eligible instances and all were kept** (not a top-25 selection), and **code used four usable
   runs, not five** (one run's artifacts lost to a directory collision). Corrected wording is in
   `PAPER_EDITS.md`. This is the fourth instance tonight of a verified number arriving inside a
   wrong sentence.
2. **Figure 1's *image* is now wrong, not just its caption.** `assets/ctxe_story.drawio.png` draws
   "Ours" strictly above the flat "Vanilla" line across the whole axis including the tau2 band,
   with an inset reading *"Fine-grained context management remains robust in more complex, more
   referential interactions!"*. **And `find` over the whole tree returns no `.drawio` source** —
   only exported PNGs. Redrawing needs a file nobody has.
3. **The "appropriate intensity" ordering inverts under the re-measured tau2 matrix.** L358, L372
   and L405 all assert light-operator-for-strong-respondent / heavy-for-weak. Reading the N=3
   matrix: gpt-5.4 → Gated-Reset 57.9 (Augment 47.4, Rewrite 47.4); DSV4F → Gated-Reset 57.9 =
   Rewrite 57.9 (Augment 50.9); Kimi → Gated-Reset 71.9 (Rewrite 66.7, Augment 57.9).
   **Gated-Reset is best or tied-best on all three.** The pattern does not merely lose its
   magnitudes; it is absent. HANDOFF's PAPER-11 line does not mention this.
4. **`checklist.tex:98` carries a stale cross-reference**, `Table~\ref{tab:main}d`, to a tau2
   panel that no longer exists — `tab:main` has been LiC-only since inner-repo commit `d211637`
   ("trim Table 1 to LiC-only"). It also asserts best-of-3 reporting for tau2, which v5 replaces
   with mean ± std.
5. **PAPER-8 has a second occurrence.** HANDOFF names `tex:299` (now L300, the caption). The same
   false claim appears again at **L347** in the body ("Gated Reset on the same prefix set").
   Fixing one leaves caption and body inconsistent.
6. **The LiC `+ Memory` rows are transductive and the paper never says so.** L709 says only "On
   LiC, we use online learning"; operationally the cheatsheet applied to an instance is distilled
   from other instances *of the evaluation set*, together with their gold answers
   (`include_full_spec_q` / `ground_truth_a`). T13 measured the effect at **0.0 pp on both tasks**,
   so disclosing it costs nothing and pre-empts a serious objection.
7. **L324's "+12.8pp" moves to +15.8pp under PAPER-7b** (Augment/code 55.6 → 52.6 while
   Augment+Memory/code stays 68.4). Not previously flagged.
8. **Printing n per cell forces PAPER-7b.** v5 promises "we will print n per cell" in four places.
   With 7a alone, four printed percentages are inconsistent with a declared per-column
   denominator. Since v5's promise is future tense, the rebuttal-era PDF does not have to carry n.

## Could not pin down

1. **PAPER-7b's interval endpoints cannot be measured.** The per-sample results for the AO,
   Concat-User, Augment and Reset rows are gone — `outputs/2026-03-21/*` and `2026-03-16/19-*`
   onward are absent from the 69,738-entry snapshot index, from `supplementary.tar.gz`, from
   `runs.yaml` (875 entries) and from every recovered tree (F45, T17 §7). Applying 7b means
   adopting T17's endpoints as point estimates. Flagged as ⚖ in the spec.
2. **`docs/multi_run_variance_2026-05-07.md` is very likely unrecoverable, not merely missing.**
   HANDOFF marks PAPER-2's effort "unknown — depends whether the runs are recoverable from
   `~/ac3/blob_staging/snapshot.tar.gz`". T17 §7 already answers it: the relevant run dirs are
   absent from that snapshot's index. I did not re-scan the tarball (no cheap way without a long
   read), so this is "very likely" rather than certain. The paper's variance table is nonetheless
   internally attested by T17's PC5.
3. **Whether `tab:megatable`'s LiC and CollabLLM blocks are replay or end-to-end.** I assumed
   replay by analogy with `tab:main` (L456) and with T1's framing, but did not verify per-run
   configs. It matters only for PAPER-10, which has no mandatory edit either way.
4. **Whether the `assets/` paths resolve for Overleaf.** The `.tex` lives in
   `writing/overleaf_repo/neurips/` and references `assets/...`, but the assets are at
   `writing/overleaf_repo/assets/`. Per CLAUDE.md the Overleaf project root is
   `writing/overleaf_repo/`, so this presumably compiles today; I did not attempt a build.
5. **ERGO/code display value.** 43.9 (measured on the corrected pool) vs 44.0 (the published
   figure, which the corrected value coincidentally reproduces). Both are consistent with v5's
   "≈44.0". Recommended 43.9; left as a stated minor judgement call because 43.9 is not an integer
   over n=19 (k is a 3-replicate mean).
6. **PAPER-5's J-decisions and PAPER-11's J1–J3** are deliberately not chosen. They are
   contribution-framing decisions, and D20's lesson — that two of the red team's own proposed
   replacements were measured and found false — applies directly: an agent proposing new framing
   under time pressure is proposing hypotheses, not fixes.
7. **Red-team M1** (self-correction count reading 3 / 5 / 7 / 10 across four files) is a rebuttal
   tone decision, not a paper item, and was left where HANDOFF left it.

## What was not done

* No file under `writing/overleaf_repo/` was created, modified or staged. `git -C
  writing/overleaf_repo status` was never run in a mutating mode; the only inner-repo command
  issued was `git log --oneline -5`, read-only.
* The `docs/` fixes described under PAPER-2 were **not** applied, though they are in the outer
  repo and would have been permitted. They are a separate scope and the operator may want to
  attempt run recovery first. `docs/index.md` therefore still carries two entries pointing at a
  file that has never existed.
* No experiment was run and no API call was made.

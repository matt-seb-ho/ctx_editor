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
| **PAPER-7** | ERGO scored on unfiltered pools in `tab:main`; math 69.6 → **80.0**, code ≈44.0, database 12.0, actions uncorrectable | **YES — the only blocker** | ✅ (7a paste-ready; 7b ⚖) |
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

## PAPER-7 — ERGO's denominators in `tab:main` ✅ **BLOCKS POSTING**

**Summary.** ERGO, and only ERGO, was scored on the *unfiltered* replay pools (n = 23/25/25/25)
while every other row in `tab:main` used the arm-symmetric pre-filtered pools (n = 20/19/25/23).
Correcting it raises a competitor: **math 69.6 → 80.0**, **code 44.0 → 43.9 (essentially
unchanged)**, **database 12.0 unchanged**, **actions uncorrectable — must print as an interval
[43.5, 52.2] or be dropped, never as a corrected point estimate**.

**Why it blocks.** `replies/v5/` discloses this correction to the reviewers in **five** places —
`00_general_response.md` Common Weakness 5 (L195–L199), `01_reviewer_iNYK.md:29`,
`02_reviewer_Vg97.md:11`, `04_response_to_AC.md:66` (correction 5), `05_final_remarks.md:47`
(correction 7). Posting v5 while `tab:main` still prints 69.6 announces an error and
simultaneously demonstrates we have not corrected it (**F58**). **Confirmed as the only blocker**:
of PAPER-1..11, this is the only item whose *numbers* a reviewer can check against the PDF while
reading the reply. PAPER-11 is larger but is a *withdrawal* — v5 states it in its own words and
needs no table to verify it.

### 7a — the blocking edit (mechanical, ~20 min, zero judgement)

**Location.** `writing/overleaf_repo/neurips/neurips_2026_conference.tex`, §Results →
§Lost in Conversation → `tab:main`. Anchor: the single line beginning `ERGO~\citep{khalid2025ergo}`
(currently **L266**, inside the `\begin{tabular}` that starts at L257 under `\label{tab:main}`).

**Current text (exact, L266):**

```latex
ERGO~\citep{khalid2025ergo} & \scored{69}{69.6} & \scored{44}{44.0} & \scored{12}{12.0} & \scored{48}{48.0} \\
```

**Replacement text (paste-ready):**

```latex
ERGO~\citep{khalid2025ergo}$^{\S}$ & \scored{80}{80.0} & \scored{44}{43.9} & \scored{12}{12.0} & \scored{48}{43.5--52.2} \\
```

Then extend the caption. **Current caption text (exact, L254)** — the sentence to extend is the
last one:

```latex
Multi-respondent results for LiC, CollabLLM, and tau2-bench are in Table~\ref{tab:megatable}; multi-respondent WildChat results are in Table~\ref{tab:wildchat}.}
```

**Replacement (paste-ready):**

```latex
Multi-respondent results for LiC, CollabLLM, and tau2-bench are in Table~\ref{tab:megatable}; multi-respondent WildChat results are in Table~\ref{tab:wildchat}. $^{\S}$ERGO was initially scored on the \emph{unfiltered} replay pools ($n{=}23/25/25/25$) while every other row used the pre-filtered pools ($n{=}20/19/25/23$); the row above places it on the same pools as every other row, which raises math from 69.6 to 80.0. Code is measured at 43.9 (essentially the published 44.0) and database is unaffected. The actions cell cannot be corrected --- no filter artifact has ever existed for that task --- so it is printed as the interval its unknown spans. Paired exact sign tests on the same items find \emph{no} ERGO-vs-\method{} difference in this table statistically distinguishable at $n{\approx}20$ in either direction (code $p{=}0.375$, math $p{=}1.00$); at this sample size the table does not settle these orderings.}
```

**Evidence.**

| Cell | Published | Corrected | Basis | Finding | Artifact |
|---|---|---|---|---|---|
| ERGO math | 69.6 (16/23) | **80.0** (16/20) | k = 0/3 pruned items solved, **measured**, 3/3 replicates | F44, **F47** | `tasks/T18/ergo_row_closed.json`, `tasks/T18/worklog.md` |
| ERGO code | 44.0 (11/25) | **43.9** (8.33/19), interval [42.1, 47.4] | k = 2.67/6 measured (3, 2, 3 across replicates) | **F48** | same |
| ERGO database | 12.0 (3/25) | **12.0** exact | nothing pruned on database (25 + 0) | F43 | `tasks/T17/RESULTS.md` §1 |
| ERGO actions | 48.0 (12/25) | **[43.5, 52.2]** | no `actions_false_negatives.json` has ever existed; the paper's own n=23 is an ad-hoc normalisation confessed at `tex:508` | F43 (D2 bullet), F47 | `tasks/T17/RESULTS.md` §1a |
| Significance frame | — | code p=0.375, math p=1.00 | paired exact sign tests, same items | **F49** | `tasks/T18/worklog.md` |

**⚠ DO NOT USE — T17's 57.9 for code.** T17's first pass assumed k = 0 for every task and produced
ERGO/code = 57.9. **T18 measured k directly and got 2.67/6**, giving 43.9. Shipping 57.9 would
**overstate a competitor by ~14 pp** — an error in the opposite direction and equally
unacceptable. It appears in `tasks/T17/RESULTS.md` §3–§5 and in `corrected_tabmain.json`; those
files are superseded on this cell only. `replies/v5/README.md:131` and `CHANGES.md:245` both carry
the same prohibition.

**Risk notes for 7a.**

1. **43.9 vs "≈44.0".** v5 says "code is essentially unchanged (≈44.0)". Both 43.9 and 44.0 are
   consistent with that phrasing. **Printing 43.9 is recommended** because it is what was measured
   on the corrected pool; printing 44.0 would coincidentally equal 11/25 and invites a reviewer to
   back out the old denominator. Note 43.9 is **not** an integer over n=19 (it is 8.33/19) because
   k is a mean over three replicate measurements — if you print n per cell (7b), add "the code
   cell is a mean over three replicate measurements of the pruned-item split (k = 3, 2, 3 of 6)".
   *Minor judgement call.*
2. **Actions as an interval.** `\scored{48}{43.5--52.2}` widens the Actions column slightly.
   Alternative if the table overflows: print `---` in the cell and give the interval in the
   caption. **Never a point estimate** (v5 README:131 guardrail).
3. **Colour bins.** `\scored{80}{80.0}` puts ERGO/math in the `tshade5` band (78–88), the same
   band as AC3-Gated-Reset's 80.0. That is correct and intended — the tie is the disclosure.
4. **The `\S` marker** does not collide with anything: `tab:main` currently uses `\diamond`,
   `\dagger` and `\ddagger` only.

**No printed sentence in the paper becomes false from 7a.** Verified against the current file: the
LiC prose (L317–L328) compares against AO and the full-context Baseline, never against ERGO; the
one explicit ERGO claim, at **L779** ("it underperforms simple concatenation on database and
actions"), still holds after correction (12.0 < 32.0 on database; ≤52.2 < 87.0 on actions), as
does the identical framing at L233. **The damage is to the table's visual ordering, not to any
sentence** (F44, T17 §5).

### 7b — the comparability pass (optional, same edit session, ~1 h) ⚖ **judgement call**

T17 recommends fixing the *second* defect in the same pass so the change reads as "make the column
comparable" rather than "raise a competitor". **v5 does not commit to any of 7b** — verified by
grep: no reply file mentions 73.7, 66.7, 63.2 or 52.6 in a `tab:main` context. So 7b is
camera-ready scope, and skipping it creates no contradiction with the posted rebuttal.

**Defect 2 (F43 bullet D2):** four cells sit one sample *below* the pool denominator (AO/code
14/18, Concat-User/math 16/19, AC3-Augment/code 10/18, AC3-Reset/code 11/18) and the Gated-Reset
actions row sits two *above* it (n=25 where every other actions row is n=23). Two of the five move
against prior work, three against us — it is roughly self-cancelling.

**These are intervals, not measurements.** Each endpoint depends on whether the dropped sample was
a per-run FN adjustment (restore it as a failure) or a genuine harness error (keep it out). Only
one is directly attested: the Gated-Reset headline actions run is **known** to have scored 17/25
raw and 17/23 filtered (`tex:508`, `docs/reports/v10_paper_updates.md:24-26`), i.e. k=0 for that
run. **Applying 7b therefore means adopting T17's interval endpoints as point estimates, and three
of the five move in our favour.** That is the judgement call: it is defensible, but doing it in the
same pass that raises ERGO is only safe if the caption says plainly that both directions were
corrected.

Cell-by-cell (all from `tasks/T17/RESULTS.md` §3–§4, F43):

| Row · task | Current | 7b value | Interval | Direction |
|---|---|---|---|---|
| AO · code (L264) | 77.8 | **73.7** | [73.7, 77.8] | against prior work |
| Concat User · math (L265) | 84.2 | **80.0** | [80.0, 84.2] | against prior work |
| AC3-Augment · code (L269) | 55.6 | **52.6** | [52.6, 55.6] | against us |
| AC3-Reset · code (L271) | 61.1 | **57.9** | [57.9, 61.1] | against us |
| AC3-Gated-Reset · code (L273) | 64.4 | **63.2** | [63.2, 64.4] | against us |
| AC3-Gated-Reset · actions (L273) | 61.3 | **66.7** | [58.0, 66.7] | **for us** |

**Two body-number changes are consequences of 7b, NOT of 7a.** `HANDOFF.md` bundles them into
PAPER-7; they are in fact driven entirely by AO/code 77.8 → 73.7 and Gated-Reset/actions
61.3 → 66.7. **Do not make these edits if you apply only 7a.** Re-derived and verified here:

* code gap-closure. Published: (64.4 − 15.8)/(77.8 − 15.8) = 48.6/62.0 = **78.4%**. Under 7b:
  (63.2 − 15.8)/(73.7 − 15.8) = 47.4/57.9 = **81.9% ≈ 82%**, on a **57.9pp** gap.
* the range. Published lower end is actions: (61.3 − 34.8)/(82.6 − 34.8) = 26.5/47.8 = **55.4%**;
  upper end is math (80.0 − 60.0)/(85.0 − 60.0) = **80.0%** → "55–80%". Under 7b actions becomes
  (66.7 − 34.8)/(82.6 − 34.8) = 31.9/47.8 = **66.7%** and code becomes 82% → **"67–82%"**.

**7b body edits, paste-ready.**

L318 — current:

```latex
on code, Gated Reset reaches 64.4\%, closing 78\% of the 62.0pp gap.
```

replacement:

```latex
on code, Gated Reset reaches 63.2\%, closing 82\% of the 57.9pp gap.
```

"55--80\%" appears in **three** places and becomes "67--82\%" in each. Verified by grep — no other
occurrence in the file:

* **L110** (abstract): `it closes 55--80\% of the multi-turn gap on self-contained tasks`
* **L139** (intro): `It closes 55--80\% of the multi-turn gap on self-contained LiC tasks`
* **L405** (conclusion): `Gated Reset closes 55--80\% of the LiC gap`

L324 also needs a touch if 7b is applied — `improves code by +12.8pp` is Augment+Memory (68.4)
minus Augment (55.6); under 7b Augment/code becomes 52.6 so the delta is **+15.8pp**. *(Verified
arithmetic; not previously flagged anywhere.)*

**Printing n per cell.** v5 promises "We will print n per cell" in four places. Because n is uniform
within a column, the honest fulfilment is per-column n in the header. **This forces 7b** — with
7a alone, four printed percentages would be inconsistent with a declared denominator. Header
replacement (L259):

```latex
\textbf{Strategy} & \textbf{Math}$^{(20)}$~$\uparrow$ & \textbf{Code}$^{(19)}$~$\uparrow$ & \textbf{Database}$^{(25)}$~$\uparrow$ & \textbf{Actions}$^{(23)}$~$\uparrow$ \\
```

plus in the caption: `Superscripts on the column headers give the per-task denominator $n$.`
Since v5's promise is future tense ("we will print"), **not** printing n in the rebuttal-era PDF
does not contradict anything posted.

### Effort / blocking

| | |
|---|---|
| **7a** | ~20 min, mechanical, zero API calls. **BLOCKS POSTING.** |
| **7b** | ~1 h, camera-ready, adopts interval endpoints as point estimates — needs a human sign-off |
| **Contradiction risk with v5** | **None for 7a.** 7b goes beyond v5 but does not contradict it |


---

## PAPER-9 — disclose the difficulty selection behind `tab:main` ✅ (one correction inside)

**Summary.** The paper never states that `tab:main`'s LiC pool is difficulty-selected. Its 4.0%
database baseline therefore reads as a measurement of GPT-5-mini when it is largely **what the
selection procedure guarantees**. Highest value per minute on the whole list: it is the
discrepancy a reviewer is most likely to catch unaided (a 52-point spread across our own tables —
red-team item H1).

**Blocking:** no. Camera-ready. v5 already discloses the selection to the reviewers
(`00` CW5, `01` W2, `02`, `04`, `05` — F68/F70/T25), so the paper is *behind* the replies but
does not contradict them; the replies describe the pool correctly.

### ⚠ Correction to the wording HANDOFF and `tasks/T24/worklog.md` §7.4 both propose

The drafted caption reads *"the 25 per task with the highest full-context failure rate across five
GPT-5-mini baseline runs."* **Two of those facts are wrong**, verified against the primary source
`docs/lic_dev_set_provenance.md`:

* **math is not a top-25 selection.** Math had only **23 eligible** instances, so *all* were kept
  (`lic_dev_set_provenance.md:50,54`). `data/dev_math_subset.json` holds 23, matching `tab:main`'s
  math n of 20 after 3 pruned items.
* **code used four runs, not five.** One `gpt5_mini` run's artifacts were lost to a directory
  collision (`lic_dev_set_provenance.md:32`).

Do not paste the drafted sentence. Use the version below.

### Location

`writing/overleaf_repo/neurips/neurips_2026_conference.tex` **L254** — the `\caption{...}` of
`tab:main` (the same caption PAPER-7 extends; a **merged** replacement is given at the end of this
item so the two edits do not collide).

### Current text (exact, the opening of L254)

```latex
\caption{\textbf{Per-task LiC results (GPT-5-mini, accuracy \%).} Cells shaded by score (darker $=$ higher). Indented \texttt{+ Memory} rows add the memory-based learner.
```

### Replacement — PAPER-9 alone (paste-ready)

```latex
\caption{\textbf{Per-task LiC results (GPT-5-mini, accuracy \%).} \textbf{Instances are difficulty-selected}: from each task's full LiC pool (math 103, code 100, database 107, actions 105) we keep instances the GPT-5-mini full-context baseline answered incorrectly in at least 60\% of five independent baseline runs (four for code), then take the 25 with the highest error rate --- math yielded only 23 eligible instances and all are kept. The Baseline row is therefore close to a fixed point of that procedure rather than an independent estimate of GPT-5-mini's multi-turn accuracy, and its absolute level is not comparable to accuracies we report on unselected pools. Because the design-oracle rows are computed on the \emph{same} instances, the gap-closure percentages quoted in the text are measured against a same-pool ceiling rather than against 100\%. Cells shaded by score (darker $=$ higher). Indented \texttt{+ Memory} rows add the memory-based learner.
```

### Evidence

| Claim | Value | Source |
|---|---|---|
| Selection criterion | `valid_appearances ≥ 3`, `errors ≥ 3`, `errors/valid_appearances ≥ 0.6`; sort by error rate desc; top 25 | `docs/lic_dev_set_provenance.md:44-50` |
| Runs used | 5 GPT-5-mini baseline runs; **code had only 4 usable** | `docs/lic_dev_set_provenance.md:26-32` |
| Full pools | math 103, code 100, database 107, actions 105 | `docs/lic_dev_set_provenance.md:17-20` |
| Eligible → selected | math 23→23, code 40→25, database 75→25, actions 55→25 | `docs/lic_dev_set_provenance.md:52-57` |
| "4.0% is what the construction guarantees" | database had 75 items already at ≥60% error; only the top 25 kept, so the retained set is dominated by 5/5-wrong items | **F68** · `tasks/T24/worklog.md` §"pool selection" |
| Gap-closure is roughly pool-independent | AC3-Reset closes 50% on this pool vs **51% / 60%** on the complete unselected pool (107/100) | **F68, F69** · `tasks/T24/worklog.md` §7.1 |
| Denominators reconcile | 23−3=20 math, 25−6=19 code, 25−0=25 database, 25→23 actions (ad-hoc) | F43 · `tasks/T17/RESULTS.md` §1 |

### Secondary exposure — two body sentences that currently imply the opposite

Flagged in `tasks/T24/worklog.md` §"Secondary exposure" but **not** carried into HANDOFF's
PAPER-9 line. Both contrast a "difficulty-selected subset" against "the default subset", which
reads to any reviewer as *the default subset is not difficulty-selected*.

**L328**, current:

```latex
with gains of +20--42pp on average on this difficulty-selected subset, across closed and open-weight architectures at different scales. Tables~\ref{tab:megatable} and~\ref{tab:wildchat} extend this picture beyond GPT-5-mini on the default subset:
```

replacement:

```latex
with gains of +20--42pp on average on that subset, across closed and open-weight architectures at different scales. Tables~\ref{tab:megatable} and~\ref{tab:wildchat} extend this picture beyond GPT-5-mini on the default subset (also difficulty-selected, but from GPT-5-mini rather than GPT-5.2 logs; Table~\ref{tab:main} caption):
```

**L139**, current:

```latex
Reset improves 15 of 16 model--task pairs on a difficulty-selected LiC subset (Table~\ref{tab:multi-model}), and the multi-respondent mega-table reproduces the ordering on the default subset.
```

replacement:

```latex
Reset improves 15 of 16 model--task pairs on a harder difficulty-selected LiC subset (Table~\ref{tab:multi-model}), and the multi-respondent mega-table reproduces the ordering on the default subset (itself difficulty-selected; see the Table~\ref{tab:main} caption).
```

One more, optional: **L513** (`app:multi-model-protocol`) says "we **re-ran** the subset selection
protocol using GPT-5.2 LiC logs (instead of GPT-5-mini)", presupposing a protocol it never
describes. With the caption above in place this now resolves, but a cross-reference is cheap:
append `(the original protocol is described in the Table~\ref{tab:main} caption)` after
"…instead of GPT-5-mini)".

### Merged `tab:main` caption — PAPER-7 (7a) + PAPER-9 together (paste-ready)

If you apply both in one pass, replace the whole of L254 with:

```latex
\caption{\textbf{Per-task LiC results (GPT-5-mini, accuracy \%).} \textbf{Instances are difficulty-selected}: from each task's full LiC pool (math 103, code 100, database 107, actions 105) we keep instances the GPT-5-mini full-context baseline answered incorrectly in at least 60\% of five independent baseline runs (four for code), then take the 25 with the highest error rate --- math yielded only 23 eligible instances and all are kept. The Baseline row is therefore close to a fixed point of that procedure rather than an independent estimate of GPT-5-mini's multi-turn accuracy, and its absolute level is not comparable to accuracies we report on unselected pools. Because the design-oracle rows are computed on the \emph{same} instances, the gap-closure percentages quoted in the text are measured against a same-pool ceiling rather than against 100\%. Cells shaded by score (darker $=$ higher). Indented \texttt{+ Memory} rows add the memory-based learner. $^{\diamond}$ marks \emph{design-oracle} baselines (collapsing multi-turn to single-turn by construction); \method \emph{exceeds} them in two cells marked $^{\dagger}$. $^{\ddagger}$ Gated-Reset row reports the mean over $N{=}3$ replay-mode reruns per cell (last-turn regen with fixed user-sim trajectory); other ours-rows are single-trial point estimates --- see Appendix~\ref{app:variance}. $^{\S}$ERGO was initially scored on the \emph{unfiltered} replay pools ($n{=}23/25/25/25$) while every other row used the pre-filtered pools ($n{=}20/19/25/23$); the row above places it on the same pools as every other row, which raises math from 69.6 to 80.0. Code is measured at 43.9 (essentially the published 44.0) and database is unaffected. The actions cell cannot be corrected --- no filter artifact has ever existed for that task --- so it is printed as the interval its unknown spans. Paired exact sign tests on the same items find \emph{no} ERGO-vs-\method{} difference in this table statistically distinguishable at $n{\approx}20$ in either direction (code $p{=}0.375$, math $p{=}1.00$); at this sample size the table does not settle these orderings. Multi-respondent results for LiC, CollabLLM, and tau2-bench are in Table~\ref{tab:megatable}; multi-respondent WildChat results are in Table~\ref{tab:wildchat}.}
```

### Effort / risk

10–15 min. Mechanical once the corrected facts above are used. **Risk: none to the argument** —
the mitigation is strong and is measured (gap-closure moves 50% → 51%/60% across a 52-point
baseline spread, F68/F69). The only trap is pasting the drafted sentence with its two factual
errors.


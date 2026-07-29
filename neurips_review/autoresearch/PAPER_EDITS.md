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
| **PAPER-9** | `tab:main` caption must disclose the difficulty selection (math is 23-of-23, **not** top-25) | No (camera-ready) | ✅ paste-ready |
| **PAPER-1** | "seeds" appears only twice in the paper, both tau2, both correct — reduces to one limitations sentence | No | ✅ paste-ready |
| **PAPER-8** | "on the same prefixes" is false; **two** locations (L300 + L347), 35 shared, McNemar p=0.125 | No | ✅ paste-ready (one ⚖ hedge) |
| **PAPER-4** | CollabLLM MATH-Hard "100" — **no occurrence of `100` in the paper**; not applicable | No | ✅ closed, no edit |
| **PAPER-3** | `+ Memory` rows are single-trial below a ~6 pp noise floor — soften or re-run | No | ⏳ |
| **PAPER-2** | The dangling citation is in `docs/`, **not** in any `.tex` — an outer-repo docs fix | No | ✅ closed, no paper edit |
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


---

## PAPER-8 — "on the same prefixes" is false ✅ (two locations, not one)

**Summary.** The gpt-5.4 WildChat Gated-vs-Reset comparison was **not** run on the same prefixes:
Reset was scored on 44 turns, Gated-Reset on 58, with **35 shared**. On the matched 35 the gap
survives (88.6 vs 74.3, **−14.3pp**) but rests on **seven discordant turns, 6 vs 1, exact McNemar
p = 0.125**.

**Blocking:** no. The claim is struck from v5 entirely, so nothing posted depends on it.

**HANDOFF points at `tex:299`; the string is at L300 and there is a *second* occurrence at L347
that HANDOFF does not mention.** Both must be fixed or the caption and the body disagree.

### Location 1 — `tab:wildchat` caption, **L300** (final clause)

Current (exact substring):

```latex
The \mgpt~Gated-Reset cell ($-$14.5pp vs.\ always-on Reset on the same prefixes) is discussed in Section~\ref{sec:wildchat-results}; corresponding cells on the Foundry respondents were not run.
```

Replacement (paste-ready):

```latex
The \mgpt~Gated-Reset cell ($-$14.5pp vs.\ always-on Reset; the two arms were scored on partly different turn pools, $n{=}44$ and $n{=}58$ with 35 in common, and on those 35 shared prefixes the gap is $-$14.3pp at exact McNemar $p{=}0.125$) is discussed in Section~\ref{sec:wildchat-results}; corresponding cells on the Foundry respondents were not run.
```

### Location 2 — §`sec:wildchat-results`, **L347** (second sentence)

Current (exact substring):

```latex
always-on Reset wins 88.6\% vs.\ AO (Table~\ref{tab:wildchat}), while Gated Reset on the same prefix set scores 74.1\%, a $-$14.5pp gap driven by false-negative \texttt{needs\_edit=False} decisions when the analyzer judges a turn ``on track'' but a clean reset would still have helped.
```

Replacement (paste-ready):

```latex
always-on Reset wins 88.6\% vs.\ AO (Table~\ref{tab:wildchat}), while Gated Reset scores 74.1\%. The two arms were evaluated on partly different turn pools --- 44 and 58 turns, 35 shared --- so we also report the matched comparison: on the 35 prefixes both arms were scored on, the gap is $-$14.3pp, but it rests on seven discordant turns (6 vs.\ 1, exact McNemar $p{=}0.125$), so we read it as a direction rather than a resolved effect. It is consistent with false-negative \texttt{needs\_edit=False} decisions when the analyzer judges a turn ``on track'' but a clean reset would still have helped.
```

### Evidence

| Number | Value | Source |
|---|---|---|
| Reset 88.6% | 39/44, reproduces to the digit | **F55**, `tasks/T20/worklog.md` §U2 positive control |
| Gated-Reset 74.1% | 43/58, reproduces to the digit | same |
| Pool overlap | \|s15\|=44, \|s2\|=58, **shared 35**, s15-only 9, s2-only 23 | `tasks/T20/worklog.md` §U2.1 |
| Matched gap | Reset 31/35 = 88.6%, Gated 26/35 = 74.3% → **−14.3pp** | §U2.2 |
| Significance | 7 discordant (6 vs 1), exact McNemar **p = 0.125** | §U2.3 |
| Raw traces | `~/ac3/recovered/ctx_editor/outputs/post_may26_wildchat_gpt54/{s15,s2}_gpt5_4_seed42_*/turn_results.jsonl`; script `tasks/T20/recompute_u2.py` | §U2 |

### ⚖ One judgement call attached

The paragraph then says *"We recommend always-on Reset when intervention cost is not a constraint
and the respondent is near-ceiling."* After the edit, that recommendation rests on a p = 0.125
result from seven discordant turns. **Options:** (a) leave it — it is a recommendation, not a
claim, and the direction is consistent; (b) hedge to "we tentatively recommend"; (c) drop the
sentence. **Recommend (b)** — cheapest, and it matches v5's posture of keeping underpowered
negatives without upgrading them. Matthew's call.

**Effort:** 10 min (5 if only L300). **Risk:** none — the substance survives matching.

---

## PAPER-1 — "N=3 seeds" ✅ **and it turns out the paper does not have the defect**

**Summary as written in HANDOFF:** reword LiC/CollabLLM "seeds" → "replicate runs (temperature
1.0)"; WildChat and tau2 keep "seeds".

**What is actually in the file.** I grepped `seed` across
`neurips_2026_conference.tex` (815 lines) and `checklist.tex` (223 lines). **The word appears
exactly twice, and both are tau2**:

* **L360** — "Gated Reset stays within trial noise of the full-context Baseline across 3 seeds"
* **L558** — "Per-trial success rates across seeds 42--44 are: …" and "reward is invariant to seed"

Per **F81**, tau2 **keeps** the word: `--seed` genuinely threads on that fork
(`run_parallel:131` → `orchestrator:526-528` → `llm_config.py:41-48` → litellm), best-effort at
the provider. So **both surviving occurrences are correct and require no edit.**

The LiC and CollabLLM passages already use the honest wording — L254 "$N{=}3$ replay-mode reruns",
L318 "mean over $N{=}3$ replay-mode reruns", L485 "We re-ran … two additional times, giving
$N{=}3$ per cell", L458 "All LLM calls … use `temperature` $=$ $1.0$". **Nothing to reword.** The
F4 defect lived in the launcher scripts and in the rebuttal drafts, not in the paper.

### The one edit that remains: the limitations caveat

**Location.** `app:limitations`, **L808**, immediately after the sentence beginning
*"\emph{Sample size and statistical reporting.}"*.

Current text (exact substring):

```latex
\emph{Sample size and statistical reporting.} Per-cell sample sizes are modest and we do not report paired significance tests on the main tables; the headline gaps should therefore be read as suggestive of the qualitative trends Figure~\ref{fig:story} summarizes rather than as point-calibrated effect sizes.
```

Replacement (paste-ready):

```latex
\emph{Sample size and statistical reporting.} Per-cell sample sizes are modest and we do not report paired significance tests on the main tables; the headline gaps should therefore be read as suggestive of the qualitative trends Figure~\ref{fig:story} summarizes rather than as point-calibrated effect sizes. \emph{What the replicates vary.} The $N{=}3$ LiC and CollabLLM replicates differ only through temperature-1.0 sampling: no decoder seed is varied, and under replay the user-simulator trajectory is held fixed. They therefore bound sampling variance for a fixed history, not seed variance and not end-to-end variance including the user simulator. The tau2-bench replicates do vary a decoder seed (42--44), best-effort at the provider.
```

### Evidence

| Claim | Finding | Artifact |
|---|---|---|
| `cfg.seed` read only by `huang_eval/`; every `seed=$((42+rep))` inert on LiC/CollabLLM | **F4** | `tasks/RECON/worklog.md` |
| CollabLLM loaders hardcode `random.Random(42)`, so replicates draw the same 20 problems | **F4** | `tasks/T8/worklog.md` |
| tau2's `--seed` genuinely threads → keep "seeds" there | **F81** | `tasks/T6/worklog.md` §13:56 |
| True seeding fixed going forward; prior runs reproduce bit-for-bit | F19 | `tasks/RECON/worklog.md` |

**Effort:** 10 min. **Risk:** none. **Blocking:** no — but it is an integrity item and it is now a
one-paragraph edit rather than a sweep, so do it early.

---

## PAPER-4 — CollabLLM MATH-Hard "100%" ✅ **no target exists in the paper**

**Summary as written in HANDOFF:** any CollabLLM MATH-Hard "100" → "matches Baseline" (91.7 vs
91.7).

**Verified against the current file: the string `100` does not occur anywhere in
`neurips_2026_conference.tex`.** The paper's only CollabLLM MATH-Hard numbers are:

* **L541** (`app:collabllm`) — "Baseline 40.0\% / 62.5\%, Rewrite 45.0\% / 82.5\% on MATH-Hard /
  BigCodeBench" (GPT-5-mini);
* **L280–L293** (`tab:megatable`, CollabLLM block) — benchmark-averaged, 44.9–57.5.

The 100% was a **v4 rebuttal claim about AC3-Augment on MATH-Hard**, not a paper claim. It is
already corrected in v5 (F16: N=3 gives AC3-Augment **91.7 ± 7.6** vs Baseline **91.7 ± 5.8** —
identical means *and* identical 55/60 per-problem totals; per-replicate delta [+5, −10, +5] =
**0.0 ± 8.7**).

**Action: none in the paper. Close PAPER-4 as not-applicable** — but keep the finding, because it
is the number to use if a MATH-Hard figure is ever added: say *"matches Baseline"*, which still
refutes 5YHP's regression claim. Evidence: **F16**, `tasks/T8/worklog.md`.

**Effort:** 0. **Blocking:** no.

---

## PAPER-2 — the missing provenance doc ✅ **not a paper edit either**

**Summary as written in HANDOFF:** "The appendix variance table cites
`docs/multi_run_variance_2026-05-07.md`, which does not exist."

**Verified: no `.tex` file in `writing/overleaf_repo/` cites it.** `grep -rn
"multi_run_variance\|paper_experiments_provenance" writing/overleaf_repo/` returns **nothing**.
The dangling references are all in the **outer** repo's docs:

| File | Line | Text |
|---|---|---|
| `docs/paper_experiments_provenance.md` | 41 | `See [multi_run_variance_2026-05-07.md](...)` |
| `docs/paper_experiments_provenance.md` | 45 | "The Gated-Reset row's N=3 spread is captured in …" |
| `docs/paper_experiments_provenance.md` | 138 | "Appendix variance table … Captured in …" |
| `docs/index.md` | 140 | topical entry for the missing file |
| `docs/index.md` | 250 | chronological-log row, dated 2026-05-07 |

So **PAPER-2 is a 5-minute outer-repo docs fix, not an Overleaf edit**, and it does not need to
travel through the shared-repo pull/push dance. `docs/index.md` currently violates the CLAUDE.md
rule that index entries must resolve.

**What the paper's variance table actually rests on, and it is fine.** T17's positive control PC5
verified the per-run values printed at **L496–L499** (75.0/80.0/85.0; 72.2/63.2/57.9;
44.0/32.0/40.0; 68.0/56.0/60.0) reproduce the printed means 80.0 / 64.4 / 38.7 / 61.3 to 0.1pp,
and the only denominators consistent with those per-run values are 20 / {18,19,19} / 25 / 25. So
the numbers are internally attested even though the doc that was supposed to hold their raw form
was never committed.

**Recommended fix (outer repo, no paper change):** in `docs/paper_experiments_provenance.md`
replace the three links with a pointer to the surviving evidence — the per-run table at
`neurips_2026_conference.tex:492-502` plus `tasks/T17/RESULTS.md` PC5 — and note that the raw
run directories (`outputs/2026-03-16/19-*` onward) are absent from `snapshot.tar.gz`,
`supplementary.tar.gz`, `runs.yaml` and every recovered tree (**F45**, T17 §7). Then remove or
retarget the two `docs/index.md` entries. Same pass should fix the second half of F8: the
provenance doc names configs `assistant_omit` and `concat_baseline` that do not exist.

**Effort:** 20 min. **Blocking:** no. **Risk:** none.
**I did not apply this** — it is a docs edit outside T31b's scope, and the operator may prefer to
attempt recovery of the runs first.


---

## PAPER-3 — the `+ Memory` rows are single trials below their own noise floor ✅ (+ one undisclosed protocol detail)

**Summary.** Table 1's `+ Memory` gains (+10.0 math, +12.8 code, +12.0 database on Augment) are
**single-trial point estimates against a measured ~6 pp run-to-run standard deviation** for the
cheatsheet learner. They are inside 2σ. Either re-run at N ≥ 4 or soften. **Blocking:** no —
memory is dropped from v5 entirely, so nothing posted depends on it.

### What was measured (F12, F13, D7)

| Quantity | Value | Note |
|---|---|---|
| Across-ordering std, Augment+Memory online, database (n=25, 4 orderings) | **28.0 ± 6.5** | 20.0 / 28.0 / 28.0 / 36.0 |
| Same-ordering std, relearn cheatsheet (Control B) | **25.3 ± 6.1** | across-ordering does **not** exceed it → ordering is not a distinguished factor; the learner is simply noisy |
| Same-ordering, fixed cheatsheet, resample eval (Control A) | 29.0 ± 3.8 | |
| math online, 4 orderings | **75.0 ± 4.1** | 75 / 80 / 75 / 70 |
| Instance-level instability across orderings | database **8/25 (32%)**, math **4/20 (20%)** | |
| N=4 remeasure on **gpt-5.4-mini** | **−8.0 pp** online / −4.5 offline (database); **−5.0** online / +0.0 offline (math) | different respondent, so **not a direct refutation** of the GPT-5-mini rows — the variance argument is the model-independent part |

Artifacts: `tasks/T12-T13/worklog.md` §9, `outputs/T12_T13/`, cheatsheets in
`tasks/T12-T13/memories/`.

**The counterweight is real and should ship with the softening (F13, D7):** contamination is
**measurably zero**. Learn set vs the canonical `lic_eval_subset`: **0/120 exact duplicates, 0
near-duplicates** (max Jaccard 0.416, boilerplate only). Overlap with the dev subsets Table 1 uses
is 11/98 (11.2%), and on exactly those instances memory is **equal or worse**. The within-instance
transduction probe returns **0.0 pp on both tasks**.

### Option A — soften (15 min, recommended)

**Location 1 — `tab:main` caption, L254.** Append to the `+ Memory` sentence.

Current substring:

```latex
Indented \texttt{+ Memory} rows add the memory-based learner.
```

Replacement:

```latex
Indented \texttt{+ Memory} rows add the memory-based learner; these are single trials, and a separate four-ordering measurement puts the learner's own run-to-run standard deviation at roughly 6pp (Appendix~\ref{app:memory-details}), so \texttt{+ Memory} differences smaller than about 12pp should not be read as resolved.
```

**Location 2 — §Results, L323–324.** Current:

```latex
\noindent\textbf{Memory amplifies analysis.}
Augment~+~Memory reaches 90.0\% on math, exceeding the AO oracle (85.0\%), and improves code by +12.8pp and database by +12.0pp; on Actions it is neutral, matching the no-memory Augment baseline at 47.8\%. Memory has no effect on Baseline, confirming memory improves analysis and edit quality, not raw task performance.
```

Replacement:

```latex
\noindent\textbf{Memory is a promising but underpowered direction.}
Augment~+~Memory reaches 90.0\% on math, exceeding the AO oracle (85.0\%), and is +12.8pp on code and +12.0pp on database; on Actions it is neutral, matching the no-memory Augment baseline at 47.8\%, and on database it is $-$4.0pp under Reset. These are single trials, and we measured the learner's own variability separately: across four trajectory orderings the online cheatsheet's accuracy has a standard deviation of roughly 6pp, and the across-ordering spread does not exceed the spread from simply relearning the cheatsheet at a fixed ordering --- so the learner is high-variance at this scale rather than order-sensitive. We therefore report these rows as a direction rather than a measured effect. Memory has no effect on Baseline, which is consistent with memory acting on analysis and edit quality rather than on raw task performance.
```

**Location 3 — intro, L139**, final sentence. Current:

```latex
Memory-based learning improves results further without parameter updates.
```

Replacement:

```latex
A lightweight memory-based learner is a promising further direction, though at our sample sizes its gains are not separable from its own run-to-run variance (Section~\ref{sec:memory-discussion}).
```

**Location 4 — conclusion, L405.** Current substring:

```latex
and a memory-based learner further improves analysis quality without parameter updates.
```

Replacement:

```latex
and a memory-based learner is a promising extension, though not one our sample sizes can separate from its own run-to-run variance.
```

**Location 5 — discussion, L383 (`sec:memory-discussion`).** Current substring:

```latex
Memory amplifies analysis when headroom exists: Augment~+~Memory reaches 90\% on LiC math (exceeding AO, Table~\ref{tab:main}) and improves DeepSeek's Reset on WildChat by +13.8pp (Table~\ref{tab:wildchat-memory}), while being neutral on near-ceiling GPT-5-mini.
```

Replacement:

```latex
Memory appears to amplify analysis when headroom exists: Augment~+~Memory reaches 90\% on LiC math (exceeding AO, Table~\ref{tab:main}) and improves DeepSeek's Reset on WildChat by +13.8pp (Table~\ref{tab:wildchat-memory}), while being neutral on near-ceiling GPT-5-mini. We report this as a direction rather than a measured effect: the LiC rows are single trials and the learner's run-to-run standard deviation across four trajectory orderings is roughly 6pp, so the LiC gains are within about twice their own noise. What we can state positively is that the gains are not contamination: the memory learn set has zero exact and zero near-duplicate overlap with the canonical LiC evaluation set, and on the 11 of 98 dev-subset instances that do overlap, memory is equal or worse.
```

### ⚠ Separately: an undisclosed protocol detail nobody has flagged as a paper item

**L709** says *"On LiC, we use online learning."* What that means operationally is that the
cheatsheet Table 1's `+ Memory` rows use is **distilled from other instances of the evaluation set
itself, together with their gold answers** (`include_full_spec_q` / `ground_truth_a` both true).
That is a transductive protocol, and the paper never says so. **T13 measured its effect and it is
0.0 pp on both tasks** (15 database / 14 math instances observed in both positions, empty vs
loaded cheatsheet), so the disclosure costs nothing and pre-empts a serious objection. Suggested
addition at the end of the `app:memory-details` paragraph at L709:

```latex
On LiC the online regime is transductive: the cheatsheet applied to a given instance is distilled from other instances of the same evaluation set, including their reference answers. We measured the effect of that exposure directly by comparing the same instance evaluated with an empty cheatsheet against the same instance evaluated with a cheatsheet distilled from 5--20 other evaluation instances: the difference is $0.0$pp on both database ($n{=}15$) and math ($n{=}14$). The designated memory learn set also has zero exact and zero near-duplicate overlap with the canonical LiC evaluation set.
```

Evidence: **F12, F13, D7**; `tasks/T12-T13/worklog.md` §9.

### Option B — re-run at N ≥ 4

Hours of compute on GPT-5-mini, which is **unreachable** from this environment (F46: `dl-openai-3`
returns 401; TRAPI serves only `gpt-5.4-mini`/`gpt-4o`). A re-run on a different respondent does
not replace the row. **Recommend Option A.**

**Effort:** 20–30 min for Option A across five locations. **Risk:** low; it is a softening, and
the contamination result is a net gain in the same paragraph.

---

## PAPER-10 — "design-oracle" labelling for AO / Concat-User ✅ **conditional; currently no mislabelled table**

**Summary as written in HANDOFF:** if any table reports assistant omission or Concatenate-User in
**end-to-end** (non-replay) mode, label them baselines rather than upper bounds.

**Verified: no table in the paper does.** `tab:main` is explicitly replay-mode for every LiC
strategy (L456: *"we run all LiC strategies in \emph{replay mode}"*), and `tab:megatable`'s LiC
block replays the same protocol. The `$^{\diamond}$` design-oracle marker at L264–L265 is
therefore not the defect F69 describes. **PAPER-10 has no mandatory edit today.**

**But the label is still stronger than the evidence, and the fix is cheap.** F69/T24 measured AO
and Concat-User end-to-end on the **complete unselected** LiC pool and they are nowhere near a
ceiling:

| Arm, LiC database, complete 107-item pool, end-to-end | Accuracy |
|---|---|
| Fully-specified single turn (**true ceiling**) | **94.4%** |
| AO ("design oracle") | 69.2% |
| Concat User ("design oracle") | 63.6% |
| AC3-Reset | **75.7%** |

So on an unselected pool **AC3-Reset clears both "oracles"** — a cleaner replication of the
paper's "exceeds the design oracle on database" claim than `tab:main`'s 48.0 vs 32.0, which rests
on 25 selected items. On the paper's 25 items both oracles sit at 32.0%; on code the headroom is
small (Concat 93.0 vs ceiling 98.0) and AC3-Reset does not clear them.

**Recommended addition** to the `tab:main` caption, after the `$^{\diamond}$` sentence:

```latex
The $^{\diamond}$ label is a statement about the LiC \emph{construction} (each instance is a single-turn question sharded across turns), not a measured ceiling: measured end-to-end on the complete unselected database pool ($n{=}107$), AO reaches 69.2\% and Concat User 63.6\% against a fully-specified single-turn ceiling of 94.4\%, with \method-Reset at 75.7\% above both.
```

**Evidence:** **F69**, `tasks/T24/worklog.md` §"design-oracle label" (lines 275–277, 337–348) and
§7.1; ceiling positive control — LiC's own `full` band for this pool is 89.7–98.1%
(`data/sota_model_results.csv`), ours 94.4%, inside the band.

**Effort:** 10 min. **Blocking:** no. **Risk:** none — this edit *strengthens* the paper's
strongest LiC claim by giving it an unselected-pool replication.


---

## PAPER-6 — the false-negative appendix describes a procedure the code does not run ✅

**Summary.** `app:false-neg` (L473–L480) says the FN classifier collates *"all user simulator
messages"*. The code keeps only `role == "user"` entries from the stored trace, so on reset and
rewrite arms — whose stored trace holds the *edited* context — it sees **1.00 user turns per
sample** against **5.35** on baseline. Recomputing that metric per run therefore excludes 50–78%
of an editing arm's failures against 9% for baseline. **The paper's `tab:main` is nonetheless
safe**: its denominators come from a **pool-level pre-filter computed once on baseline traces and
applied identically to every arm** — that is arm-symmetric and correct, and it must be
**defended, not conceded**.

**Blocking:** no; v5 is raw throughout. **Do before arXiv** — it moves published magnitudes
elsewhere and the appendix as written invites exactly the wrong reading.

### Verified on disk tonight (independent of T14)

* `src/ctx_editor/identify_false_negatives.py`, `format_user_messages`:
  `user_msgs = [m for m in messages if m.get("role") == "user"]` — **only** user-role messages,
  from whatever trace it is handed.
* `src/ctx_editor/execution/replay.py:21+`, `load_user_sim_induced_ids`: docstring states the IDs
  are *"pre-computed by running `identify_false_negatives` on the baseline traces"* and loaded
  from a sidecar.
* `data/baseline_traces_v2/` contains `math_false_negatives.json`, `code_false_negatives.json`,
  `database_false_negatives.json` — and **no actions sidecar**, confirming T17 §1a directly.

### Location — `app:false-neg`, L478 and L480

Current text (exact, L478 in full):

```latex
We account for this with a post-hoc false negative identification procedure applied to all tasks. For each instance where the assistant fails, we collate all user simulator messages and compare them against the original single-turn question. We query GPT-5 (prompt provided in supplemental materials) to determine whether the user simulator's messages, taken as a union, provide sufficient information to solve the original problem.
```

Replacement (paste-ready):

```latex
We account for this with a pool-level pre-filter, computed once and applied identically to every arm. For each instance where the \emph{full-context baseline} assistant fails, we collate the user-role messages of that baseline trace and compare them against the original single-turn question. We query GPT-5 (prompt provided in supplemental materials) to determine whether those messages, taken as a union, provide sufficient information to solve the original problem. The resulting per-task list of instance IDs is stored alongside the replay pool and every strategy is evaluated on the same reduced pool, which is why all rows of Table~\ref{tab:main} share the denominators $n{=}20/19/25/23$ (math $23{-}3$, code $25{-}6$, database $25{-}0$; the actions column is normalized to a common 23 samples, as noted in Appendix~\ref{app:variance}).

We deliberately do \emph{not} recompute this classifier per run. A reset or rewrite arm stores the \emph{edited} context, in which the original user turns have been consolidated into a single specification message; the classifier would then see about one user turn per sample on those arms against about five on the full-context baseline, and would exclude their failures at a far higher rate. Computing the filter once on baseline traces removes that asymmetry by construction: it is a property of the \emph{instance}, not of the arm.
```

Then, current L480 first sentence:

```latex
Instances flagged as insufficient are excluded from accuracy calculations, as the assistant's failure is attributable to the evaluation setup rather than to context pollution or the intervention strategy.
```

Replacement:

```latex
Instances flagged as insufficient are excluded from the evaluation pool for \emph{all} arms, as the failure is attributable to the evaluation setup rather than to context pollution or the intervention strategy. All accuracies we report are raw accuracies on that common pool; we report no per-run adjustment of any kind.
```

### Evidence

| Claim | Value | Finding | Artifact |
|---|---|---|---|
| Judge visibility asymmetry | **1.00** user turns/sample on AC3-Rewrite vs **5.35** on baseline | **F41** | `tasks/T14/RESULTS.md` |
| Exclusion-rate asymmetry | 50–78% of failures excluded on reset arms vs **9%** on baseline | F28, F40 | `tasks/T14/{RESULTS.md,corrected_matrix.*}` |
| Inflation magnitude | reset arms **+13.9 to +55.9 pp**; no-reset arms +0.2 to +6.5 | F41 | same |
| Visibility isolated from judge-swap | second full re-judge: **+0.5%** on no-reset arms, **−48.9%** on reset arms | F41 | same |
| `tab:main` denominators are sound | pool-level pre-filter reproduces 20/19/25/23 exactly; **defend, do not concede** | **F42, D13** | `tasks/T17/RESULTS.md` §1, PC1 (28/28 archived runs, 0 exceptions) |
| Per-run adjustment's footprint in `tab:main` | at most 4 cells, ≤1 sample each; 2 of 4 favour prior work | F42 | same |

**Cross-check with v5:** v5 concedes the per-run metric loudly in five places while **defending**
the denominators. The replacement text above does both in the same paragraph, so the paper and the
replies agree. T19 added an explicit rule (F50) forbidding the metric concession from bleeding
into an admission that the denominators are wrong — the wording above respects it.

**Effort:** 45 min, not the 2–3 h HANDOFF estimates: the paper never names `adjusted_accuracy`, so
there is no metric to delete from any table — only the appendix description to correct.
**Risk:** low. The only judgement is how loudly to state the asymmetry; the wording above states
it as a design rationale rather than as a confession, which is both accurate and stronger.

---

## PAPER-5 — retract "preserve what's correct and remove what's harmful" ⚖ **JUDGEMENT CALL**

**Summary.** T2B tested this causally on **natural** spans with no detector, judge or LLM anywhere
in the label path, and it does not hold for **either** operator. Preservation of causally useful
spans is **0% for both**; edit precision is **63.6% = the base rate for both**. The mechanism the
evidence supports is *detect → discard the assistant side → rebuild the specification from the
user side*. **Do not re-attribute the claim to AC3-Rewrite** — Rewrite is the *worse* of the two
(keeps 0/66 probe-admissible spans against Reset's 5/66).

**Blocking:** no — v5 already retracts it (`03_reviewer_5YHP.md:132`, `CHANGES.md` §11.1).
**But the paper currently asserts it in six places, so after posting the paper contradicts the
reply.** That makes PAPER-5 the highest-priority *non-blocking* item after PAPER-11.

### The evidence, both directions

| Question | Answer | Finding |
|---|---|---|
| Is natural pollution real? | **Yes, and concentrated.** Effect SD **0.155** vs a replicate-matched parametric null's 0.125 (2,000 sims, **p = 0.0085**); **16** large-effect spans (\|Δ\| ≥ 0.25) where the null predicts 9.3 (**p = 0.017**). Mean effect **+0.020** [−0.010, +0.048] — the typical span is inert; the phenomenon lives in a ~6% excess minority | **F65** |
| Are the operators selective? | **No — neither.** Reset keeps **5/66** probe-admissible spans, Rewrite **0/66**. Removal on causally harmful spans **100% (7/7, both)**. Preservation on causally useful spans **0% (0/4, both)**. Edit precision **63.6% = the base rate for both**. Label-free aggregate agrees (Reset removed−kept **−0.014, p = 0.85**) | **F66** |
| What survives and is still ours | Analyzer **names the injected pollutant in `issues` 78.6%** of the time (89.7% on the causally-harmful subset); the factorial gives Baseline clean 24.7% → **9.3%** with the pollutant → **AC3 59.8% with the pollutant still present**; **100% removal** of causally-harmful natural spans | F23, F26, **F66** |

Artifacts: `tasks/T2B/{RESULTS.md,worklog.md,per_span.json,per_span_alignment.json}` (`289de75`),
`outputs/T2B/`; earlier `tasks/T2A/{RESULTS.md,inject.py,measure.py}`, `outputs/T2A/`.
**F25 is superseded by F66** — T2A's own first paragraph flagged synthetic salience as an
upper-bound caveat, and the caveat turned out to be exactly right, so T2B *extends* T2A rather
than contradicting it. That reconciliation is load-bearing and should ship with any rewrite.

### Every location, with the current text

| # | Line | Current text (exact substring) | Nature |
|---|---|---|---|
| 1 | **L110** (abstract) | `(3) edit the context to keep verified work and remove invalidated reasoning` | mechanical |
| 2 | **L135** (intro) | `and then edits the conversation context (by augmenting it with the analysis, resetting it from the clean specification, or rewriting it) to keep verified work and remove invalidated reasoning` | mechanical |
| 3 | **L151** (Fig. 2 caption) | `by rewriting the conversation to keep verified work and remove invalidated reasoning` | mechanical |
| 4 | **L191** (Methods opening) | `compares the assistant's work against that clean specification, and rewrites the conversation to keep what is correct and remove what is harmful` | mechanical |
| 5 | **L394** (Related Work) | `We instead treat context as \emph{heterogeneous}, distinguishing correct assistant work from polluting content.` | **the ERGO differentiation — authorial** |
| 6 | **L405** (conclusion) | `mitigates multi-turn degradation by selectively curating rather than discarding context` | **authorial** |

Two further sites depend on the decision but are *not* straightforwardly false:

* **L174, the "Preservation" desideratum** (`$p_\theta(\text{correct} \mid C'_t) \geq
  p_\theta(\text{correct} \mid U_t)$ whenever $A_{t-1}$ contains useful referential state`). This
  is a **desideratum**, not a claim that AC3 achieves it. It can stand — but if it stands, the
  paper should say somewhere that AC3 satisfies it *empirically on referential benchmarks* (the
  tau2 AO-vs-AC3 contrast, WildChat) rather than *by selective span preservation*.
* **L727** (`app:trajectories`): `The rewritten context preserves the correct diagnosis (Maven needs a JDK) while removing the flawed reasoning.` This is one qualitative trajectory and is accurate as an anecdote; it becomes misleading only if it is offered as the general mechanism.

Also in the **outer repo**: `CLAUDE.md` §Project Overview carries the identical sentence
(*"Unlike prior work that simply discards all assistant messages, we preserve what's correct and
remove what's harmful"*), and `docs/project_motivation.md` develops it.

### Mechanical replacements (safe to paste regardless of which framing option is chosen)

**#1, L110:**

```latex
(3) edit the context to remove invalidated reasoning and rebuild the working specification from the user side
```

**#2, L135:**

```latex
and then edits the conversation context (by augmenting it with the analysis, resetting it from the clean specification, or rewriting it) so that the assistant continues from a specification rebuilt from the user's own messages rather than from its own invalidated reasoning
```

**#3, L151:**

```latex
by rebuilding the conversation around a user-grounded specification and dropping the invalidated reasoning
```

**#4, L191:**

```latex
compares the assistant's work against that clean specification, and then rebuilds the conversation around that specification rather than around the assistant's prior reasoning
```

### ⚖ The authorial decision — #5 and #6

T2B does not just retract a sentence; it **dissolves the differentiation from ERGO**. "Unlike prior
work that discards all assistant messages, we are selective" was the paper's stated distinction,
and T2B says we largely *do* discard them. Three coherent options, each internally consistent with
the measured evidence. **Matthew's call — I am deliberately not choosing.**

**Option A — differentiate on *what is rebuilt from*, not on selectivity.** ERGO resets by an LLM
rewrite of prior **user** messages; AC3 consolidates a specification from the user side **and
audits the assistant's work against it**, so the reset context carries an explicit statement of
what was verified and what was invalidated. This is measurable and true: the analyzer names the
injected pollutant 78.6% of the time, and the factorial shows AC3 reaching 59.8% *with the
pollutant still in context* against a clean baseline of 24.7%.
*Cost:* the paper stops claiming span-level selectivity, which several passages currently lean on.
*Benefit:* nothing in it is at risk from a future ablation.

**Option B — differentiate on *what is preserved at the artifact level*.** AC3 keeps an explicit
`aligned` record of verified work, which blanket omission cannot; the claim becomes "we preserve
the *conclusions* of correct assistant work, not its *text*". This is closer to the current
framing and is what the Reset template actually does.
*Cost:* it is untested. T2B measured span-level preservation, not conclusion-level. Making this
claim would put a new unverified assertion in place of a retracted one — the exact failure mode
D20 was written about.
*Benefit:* least rewriting.

**Option C — lead with the referentiality result and drop the selectivity framing entirely.** The
paper's strongest surviving distinction is that AO collapses structurally where state lives in
assistant turns (tau2 AO = 0% on 9/9 cells, 171 rollouts) while AC3 remains viable, and that AC3
beats full context across LiC and WildChat. Selectivity becomes an implementation detail rather
than the contribution.
*Cost:* this is the largest rewrite and it converges with PAPER-11, which removes the far end of
the same "spectrum of referentiality" narrative. **Do PAPER-5 and PAPER-11 in one sitting if you
choose C.**
*Benefit:* every claim in it is measured, and it survives the tau2 withdrawal unchanged.

**One thing to avoid under any option.** Do not write "we preserve what is correct" about
AC3-Rewrite. Rewrite is the *less* preserving operator (0/66 vs Reset's 5/66). F25 briefly
suggested re-attribution and **F66 overturned it**; re-attributing would ship a claim that the
best evidence we have contradicts.

**Effort:** 30 min for #1–#4; 1–3 h for #5–#6 depending on option. **Blocking:** no, but the paper
will contradict `03_reviewer_5YHP.md:132` until it is done.


---

## PAPER-11 — the tau2 withdrawal ⚖ **SCOPED INVENTORY — do not attempt the rewrite from this document**

**Summary.** T6 re-ran the full published tau2 matrix at N=3 (3 models × 5 arms × 3 replicates ×
19 tasks = **855 scored rollouts**, 899 run, 15/15 cells, same hyperparameters and model
identities as the committed sweep scripts). **Two of three published baselines do not replicate:
DSV4F 31.6 → 70.2 ± 11.0, Kimi 26.3 → 78.9 ± 0.0.** On **all three models the re-measured
Baseline is at or above every AC3 arm.** The tau2 improvement claim is **withdrawn**.
**What survives: AO → 0.0% on every model, every replicate, 9 cells / 171 rollouts, structural
and exact.**

**Blocking:** no. v5 posts the withdrawal in its own words (`00` CW1+CW4, `01` W3, `02` W2/Q2,
`04` correction 6, `05` correction 8, `README`, `CHANGES` §12.3), and a reviewer reading "we
withdraw this claim" needs no paper edit to verify it. **But it must land before any revision or
arXiv push, and it is the highest-stakes item on the list.**

**Rule, codified in `replies/v5/README.md` Blocker 2 and worth restating here:** the positive
control **reproduced** (gpt-5.4 Baseline 68.4 vs published 68.4; AO 0.0 across 9 cells vs
published 0/0/0), `gpt-5-mini` *was* reachable, invocation strings were byte-identical and no
model was substituted anywhere. **Do not soften the withdrawal into "mixed results" or "not
comparable across model eras."** (F79.)

### The re-measured matrix (the numbers any replacement must use)

| tau2-bench (reward %) | gpt-5.4 | DeepSeek-V4-Flash | Kimi-K2.6 |
|---|---|---|---|
| Full context — **as published** (N=1) | 68.4 | **31.6** | **26.3** |
| **Full context — re-measured, N=3** | **68.4 ± 13.9** | **70.2 ± 11.0** | **78.9 ± 0.0** |
| Assistant omission, N=3 | **0.0 ± 0.0** | **0.0 ± 0.0** | **0.0 ± 0.0** |
| \method-Augment, N=3 | 47.4 ± 5.3 | 50.9 ± 8.0 | 57.9 ± 9.1 |
| \method-Gated-Reset, N=3 | 57.9 ± 21.1 | 57.9 ± 10.5 | 71.9 ± 11.0 |
| \method-Rewrite, N=3 | 47.4 ± 5.3 | 57.9 ± 13.9 | 66.7 ± 8.0 |

Paired against the re-measured baseline: **Augment is significantly worse on all three**
(−21.1 p = 0.008 / −19.3 p = 0.043 / −21.1 p = 0.012); Gated-Reset and Rewrite are negative
everywhere without reaching significance. AO is −68.4 / −69.6 / −78.9, **p < 0.0001**.

**Evidence:** **F78–F81, D21**. `tasks/T6/worklog.md` (Tables 1–2, §"the finding the rebuttal has
to deal with", §"Did the positive control reproduce?", §"Bug found in the fork"); per-rollout
traces at `~/ac3/tau2_ctxe/ctx_edit/outputs/T6_reps/<model>_<arm>/traces/*.json`; aggregators
`t6_aggregate.py` / `t6_paired.py`; diagnostic at `outputs/T6_diag/`. Same table printed in
`replies/v5/00_general_response.md` CW4.

### ⚠ Two consequences nobody has recorded, both found while building this inventory

**(1) Figure 1 is an image, and the image itself is now wrong — not just its caption.**
`assets/ctxe_story.drawio.png` draws the "Ours" curve **strictly above** the flat "Vanilla" line
across the whole x-axis, *including the tau2-bench band*, with an inset reading *"Fine-grained
context management remains robust in more complex, more referential interactions!"*. Under the
withdrawal, at the tau2 end AC3 is at or below vanilla on all three respondents. **The teal curve
must cross or meet the orange line inside the tau2 band, and the inset text must change.** This is
a redraw, not a caption edit. **And the draw.io source is not in the repo** — `find` over the
whole tree returns no `.drawio` file, only exported PNGs (`ctxe_story.drawio.png`,
`ctxe_story.drawio(1).png`, `fig1_v6.drawio.png`, `task_comparison.drawio.png`). Whoever holds the
draw.io document must redraw it; budget this separately from the text edits.

**(2) The "appropriate intensity" narrative loses its tau2 leg, and the ordering inverts.**
L358 and L372 both claim *"the strongest respondent (gpt-5.4) benefits most from the lightest
operator (Augment, +15.8pp), while the weakest (Kimi-K2.6) benefits most from the heaviest
(Rewrite)"*. On the re-measured matrix, reading down the AC3 rows: gpt-5.4 → **Gated-Reset 57.9**
(Augment 47.4, Rewrite 47.4); DSV4F → **Gated-Reset 57.9 = Rewrite 57.9** (Augment 50.9);
Kimi → **Gated-Reset 71.9** (Rewrite 66.7, Augment 57.9). **Gated-Reset is best or tied-best on
all three**, so the light-for-strong / heavy-for-weak pattern does not merely lose its magnitudes
— **it is not there any more.** The WildChat half of the same argument (Rewrite wins on Kimi-K2.6,
Reset on gpt-5.4) is untouched and survives. **L372 therefore needs an authorial decision, not a
number swap** — see the judgement calls below.

### Full location inventory

Ordered by position in the file. "Must become" is the constraint, not the wording.

| # | Line | Section | Current text (substring) | What it must become | Kind |
|---|---|---|---|---|---|
| 1 | **110** | abstract | `\method is the only approach that improves over full context across the entire spectrum` | the pre-drafted fallback, applied verbatim in v5: **"the only method tested that improves over full context on every self-contained and referential benchmark, and the only method that remains viable in the stateful agentic setting"** | mechanical (wording fixed by v5) |
| 2 | **110** | abstract | `and substantially outperforms full context in agentic tool use --- by double-digit margins per respondent --- where blanket omission instead collapses to 0\% on every model tested` | **delete the improvement half.** Keep only: blanket omission collapses to 0% on every model tested | mechanical |
| 3 | **110** | abstract | `selective curation, not blanket removal, is what scales to multi-turn human--AI interaction` | survives on LiC + WildChat, but see **PAPER-5** — the same sentence is load-bearing there | ⚖ interacts with PAPER-5 |
| 4 | **122** | Fig. 1 caption | `\emph{\methodfull{} (\method, ours)} substantially outperforms vanilla across the spectrum --- including on tau2-bench, where AO collapses entirely (to 0\%) while \method still beats full context` | **false as written.** Must become: AC3 outperforms vanilla on the self-contained and referential benchmarks; on tau2-bench AC3 remains viable while AO collapses to 0%, but does not beat full context | mechanical text, **plus the image redraw above** |
| 5 | **122** | Fig. 1 caption | `\emph{Full context} (vanilla) plateaus throughout.` | **false at the tau2 end** — vanilla is the top arm there (68.4 / 70.2 / 78.9). The schematic's whole shape is at issue | ⚖ depends on the redraw |
| 6 | **139** | intro | `\method is the only method that improves over full context across the entire spectrum` | same replacement as #1 | mechanical |
| 7 | **139** | intro | `And on stateful agentic tool use in tau2-bench~\citep{barres2025tau2}, the best \method operator beats full context by double-digit margins on every respondent, while AO catastrophically collapses to 0\%...` | **delete the improvement clause; keep the AO collapse.** Suggested: "And on stateful agentic tool use in tau2-bench, AO catastrophically collapses to 0\% on every respondent by destroying tool-call results that live only in assistant turns, while \method{} remains viable" | mechanical |
| 8 | **242** | Experiments, tau2 para | (benchmark description, no result claim) | **no change needed** | — |
| 9 | **280** | `tab:megatable` caption | `\mkimi~tau2-bench Baseline/AO cells are rate-limit-clipped floors at Foundry workers=4 (true Baseline likely 40--50\%; AC3 cells ran clean).` | **the concession becomes the finding.** Both the Kimi *and* the DSV4F baselines were clipped; re-measured they are 78.9 and 70.2. This sentence must be replaced by a statement that the published Baseline row was withdrawn and re-measured at N=3 | mechanical (given the new table) |
| 10 | **280** | `tab:megatable` caption | `or task reward (tau2-bench, \texttt{telecom\_small}, $n{=}19$ per cell)` | add: mean ± std over N=3 replicate runs (seeds 42/43/44), 19 tasks per replicate | mechanical |
| 11 | **289–293** | `tab:megatable` **tau2 block** | the six values per row (`68.4 / 31.6 / 26.3`; `0.0 / 0.0 / 0.0`; `84.2 / 57.9 / 57.9`; `52.6$^{*}$ / 47.4$^{*}$ / 68.4$^{*}$`; `73.7 / 57.9 / 73.7`) | **replace wholesale with the re-measured matrix above**, as mean ± std. Note the `$^{*}$` marker (Gated-Reset) still applies — always-on Reset was never run on tau2 | mechanical, but the `\scored` colour bins all change |
| 12 | **328** | §multi-model | `the best \method operator per cell beats Baseline (full context) in every (model, benchmark) block, while AO collapses entirely on tau2-bench across all three` | **false.** Must become: beats Baseline in every LiC and CollabLLM block; on tau2 no AC3 arm beats the re-measured Baseline, while AO collapses to 0% | mechanical |
| 13 | **328** | §multi-model | `on tau2-bench the spread widens and the winning operator changes by respondent` | **false** — Gated-Reset is best or tied-best on all three. Delete or restate | mechanical |
| 14 | **356** | §tau2-results ¶1 | AO collapses to 0% … infinite re-lookup loops … blanket omission incompatible with stateful tool use | **KEEP — this is the paragraph the section exists for.** Strengthen with the N=3 evidence: 9 cells / 171 rollouts, not one non-zero reward, via the confirmed `max_steps` termination path, paired −68.4 / −69.6 / −78.9 pp, p < 0.0001 | mechanical strengthening |
| 15 | **358** | §tau2-results ¶2 | the entire *"winning operator changes with respondent strength"* paragraph — `+15.8pp`, `+26.3pp`, `+47.4pp`, the "appropriate intensity" reading | **DELETE or REWRITE FROM SCRATCH.** Every magnitude in it is withdrawn and the ordering it asserts is not present in the re-measured matrix | ⚖ **authorial** |
| 16 | **360** | §tau2-results ¶3 | `only 1 of 11 baseline failures is attributable to context pollution (Table~\ref{tab:tau2-failure-modes})` | **soften — see sub-item U4 below** | ⚖ |
| 17 | **360** | §tau2-results ¶3 | `Across all four respondents the load-bearing finding is the same: selective editing is the only context-management approach that remains viable when tool-call results live only in assistant turns.` | **survives verbatim** — "viable", not "better". This sentence is already the honest claim | none |
| 18 | **369** | Discussion ¶1 | `on tau2-bench, AO collapses to 0\% on every respondent we tried while editing beats full context by +15.8 to +47.4pp over Baseline (the upper end against a rate-limit-clipped Kimi baseline...)` | **delete the magnitude clause entirely.** Keep the AO collapse | mechanical |
| 19 | **372** | Discussion ¶2 | `On tau2-bench, the strongest respondent (gpt-5.4) benefits most from the lightest operator (Augment, $+$15.8pp), while the weakest (Kimi-K2.6) benefits most from the heaviest (Rewrite, the largest gain in the sweep).` | **DELETE.** The pattern is not in the re-measured data (see consequence (2) above). The paragraph's WildChat half survives and can carry it alone, but the paragraph's thesis then rests on one benchmark | ⚖ **authorial** |
| 20 | **405** | conclusion | `and on tau2-bench, where AO collapses to 0\% on every respondent, the best \method operator beats full context by double-digit margins` | **delete the improvement clause.** Keep the AO collapse; add "remains viable" | mechanical |
| 21 | **405** | conclusion | `Second, a single shared analyzer supports the full operator menu, and intensity should match the respondent: lighter editing (Augment) for stronger agents, heavier editing (Rewrite) for weaker ones (Table~\ref{tab:megatable}).` | **same problem as #19** — this is the conclusion's statement of the withdrawn pattern | ⚖ **authorial** |
| 22 | **558** | `app:tau2-diagnostic` | the whole per-trial gpt-5-mini paragraph: `Per-trial success rates across seeds 42--44`, `The table reports the best-of-3 trial` | **best-of-3 must go** — v5 commits to mean ± std. Note this cell (gpt-5-mini) was **not** re-run by T6, which targeted the three-model matrix, so its numbers stand but its reporting convention must change | mechanical |
| 23 | **562–577** | `tab:tau2-failure-modes` | the 11-failure breakdown, "Context pollution 1" | **soften — U4, see below** | ⚖ |
| 24 | **808** | `app:limitations` | `\emph{Tau2-bench scope.}` … `the load-bearing finding is the \emph{collapse} of AO … not the absolute success rate of \method` | **already the right posture.** Extend with the withdrawal, the unexplained gpt-5.4 collapse and the fork parser bug — draft below | mechanical addition |
| 25 | **checklist.tex L98** | NeurIPS checklist, error bars | `For tau2-bench (Table~\ref{tab:main}d) we ran 3 trials for both Baseline and Gated-Reset (the table cell shows the best of 3...)` | **two defects**: (a) `Table~\ref{tab:main}d` is a **stale cross-reference** — `tab:main` has been LiC-only since inner-repo commit `d211637`, so this renders as a panel that does not exist; (b) best-of-3 must become mean ± std over N=3. Nobody has flagged (a) | mechanical |

### Sub-item U4 — the failure-mode table (`tab:tau2-failure-modes`)

**Status: unverified, and it characterises a tau2 baseline that has since moved.** The "1 of 11"
figure is traceable to `~/ac3/tau2_ctxe/ctx_edit/EXPERIMENT_LOG.md` commit `169b044` (2026-03-24)
with the table verbatim identical to the paper's — but **the 20 traces are gone**, never tracked
in git, absent from both tarballs and from disk, and **no labels file or rubric ever existed**.
Two further defects: it is the **45.0% trial, the worst of three {45, 55, 60}**, while the table
reports best-of-3, so 11 failures does not reconcile with the reported cell; and n is ambiguous
(20 vs 19). **F56.** Standing recommendation, unchanged: **soften now, defer re-derivation to
camera-ready.** v5 already says this to the reviewers in its own words
(`00_general_response.md` CW4, final paragraph: *"we do not have a defensible failure taxonomy for
it … one author's reading of a single trial's traces, without a rubric and without a second
annotator … For the camera-ready we will annotate all trials against a published rubric with a
second annotator"*). **The paper must not keep asserting the taxonomy while the reply disowns it.**

### Draft limitations addition (L808) — paste-ready, and the one part of PAPER-11 that is not a judgement call

Append to the `\emph{Tau2-bench scope.}` sentence:

```latex
\emph{Tau2-bench scope, and a withdrawn comparison.} Tau2-bench results use only the \texttt{telecom\_small} subset and are framed as a preliminary exploration of the agentic regime. Re-running the full three-respondent matrix at $N{=}3$ (855 scored rollouts) established that two of the three full-context baselines we originally reported were degraded --- rate-limit-clipped floors rather than honest performance --- and that against re-measured baselines no \method{} operator improves over full context on this benchmark. We therefore withdraw the tau2-bench improvement comparison. The load-bearing finding is unaffected and reproduces exactly: assistant omission returns \textbf{0\%} on every respondent, every replicate, 9 cells and 171 rollouts, because blanket omission destroys the tool-call results that exist only in assistant turns and the agent re-calls tools until it exhausts its step budget. Two things we cannot yet explain and prefer to state. First, on gpt-5.4 the \emph{baseline} reproduced exactly (68.4 vs 68.4) while every \method{} arm fell by 10 to 37 points against the published values; we ruled out model substitution, gating failure, degenerate termination and rate limits, and we report the collapse as unexplained rather than attribute it. Second, we found a real defect in our tau2 harness --- the analyzer's tag extractor misses when the model answers in JSON, so 53\% of analyzer calls fell back to splicing a raw completion into the agent's briefing --- which can only degrade \method{} arms and cannot touch full context or omission; patching it moved accuracy by $+2.3$pp, so it is worth fixing but is not the explanation.
```

### ⚖ The authorial decisions — options presented, not chosen

**J1 — What is the paper's headline contribution without the tau2 improvement?** The abstract's
spine is a *spectrum* argument: AC3 wins everywhere along a referentiality axis with tau2 at the
far end. Removing tau2's improvement leaves the far end supported only by "AC3 remains viable
while AO collapses". Three framings:

* **(a) Keep the spectrum, weaken the far end.** Use v5's exact fallback wording (#1 above).
  *Pro:* zero divergence from what reviewers will have read; the fallback is already drafted and
  posted. *Con:* the spectrum's punchline becomes "we do not break" rather than "we win", and
  Figure 1's shape has to change to match.
* **(b) Re-centre on LiC + WildChat and demote tau2 to a stress test.** The headline becomes
  "closes most of the multi-turn gap on self-contained tasks and wins every real-conversation
  cell; tau2 shows that the *alternative* fix fails structurally". *Pro:* every claim is measured
  and none is at risk. *Con:* a larger rewrite of abstract, intro, Fig. 1 and conclusion, and it
  gives up the four-benchmark sweep as the organising idea.
* **(c) Re-centre on the AO-refutation.** Make the paper's thesis "blanket omission is not a
  general fix", with tau2 as the decisive counterexample and AC3 as the constructive answer.
  *Pro:* AO = 0% on 9/9 cells is the single strongest, most reproducible result in the whole
  submission, and it is *unaffected* by the withdrawal. *Con:* it reframes the contribution from
  "our method wins" to "the field's current fix is wrong", which changes who the paper is arguing
  with.

**J2 — Does the "appropriate intensity" thesis survive on WildChat alone?** #19 and #21 assert
it from tau2 + WildChat; the tau2 half is gone and the surviving tau2 ordering (Gated-Reset best
or tied-best on all three) points the *other* way. Options: **(i)** keep the thesis on WildChat
only and say so; **(ii)** retire the thesis and present the three operators as a design knob
without a directional rule; **(iii)** replace it with the *measured* tau2 ordering — Gated-Reset
dominates in the agentic setting, which is a defensible and useful statement about gating in
state-carrying environments, though at N=3 on 19 tasks it is not resolvable. **I recommend
against (iii) as written**: it would replace a withdrawn pattern with a new underpowered one,
which is exactly the failure mode D20 records.

**J3 — Does Figure 1 stay a schematic?** It is labelled "Schematic of qualitative trends", which
gives licence to redraw the tau2 band with the teal and orange curves meeting. Alternatively it
could be replaced by a real bar chart from the measured data. **Redraw needs the draw.io source,
which is not in the repo.**

### Effort

3–5 h of text, **plus a figure redraw of unknown cost** because the source file is missing, plus
whatever J1 costs. **Do PAPER-5 and PAPER-11 in one sitting**: J1 option (b) or (c) and PAPER-5
option C converge on the same rewrite, and doing them separately means rewriting the abstract
twice.


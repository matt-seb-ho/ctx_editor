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


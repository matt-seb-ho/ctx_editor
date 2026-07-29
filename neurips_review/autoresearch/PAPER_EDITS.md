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


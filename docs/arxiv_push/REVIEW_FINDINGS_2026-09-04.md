# arXiv draft — fresh review-pass findings (2026-09-04)

An independent clean-eyes review of `writing/overleaf_repo/arxiv/neurips_2026_conference.tex`,
run at Matthew's request as a second opinion on top of the prior (2026-07-09) adversarial debate
and the (2026-08-12) evidence fold-in. Method: the `research-paper-writing` skill checklist + two
independent reviewer subagents (a claim–evidence skeptic and a copyeditor), then **manual
verification of every serious finding against the actual table cells** before recording it here.

**Headline correction to the 2026-09-03 state report.** That report relayed the prior session's
assessment that the draft is "internally consistent and honest *as written*." **This review found
that is not true in three verified places.** The prose was made honest; the *tables and headline
numbers were not fully reconciled to it.* None of this is fatal to the paper's story — but it is
posting-blocking, because a reviewer inspecting the tables sees claims the text says it withdrew.

Status legend: ✅ verified by me against the file · 🟡 reviewer-reported, plausible, not yet
hand-verified.

> **RESOLVED 2026-09-04 (inner-repo commit `9e9d2ae`).** B1 and S1–S3 are now **fixed**.
> B1: Table 2's tau2 block was rebuilt from the verified re-measured N=3 matrix (source:
> `neurips_review/autoresearch/tasks/T6/worklog.md` Table 1, cross-checked against
> `neurips_review/autoresearch/PAPER_EDITS.md` — my three known rows matched exactly, and the
> worklog's "seed-42 N=1 ref" column reproduced Table 2's old cells, confirming they were the
> withdrawn single-run numbers). S1–S3: Table 1 Gated-Reset row set to the appendix N=3 means
> (code→64.4, actions→61.3); headline 67–82% → 55–84%; code closure 82%/78% → 84%. No numbers
> were invented. Remaining open items below: S4 (MT-OSC cite), S5 (l.577 cross-ref), S6 (abstract
> scope), M1–M3, plus the non-review blockers (author block, Figure 1, push).

---

## Applied already (committed `f73371a`, revertible)

A mechanical **copyedit pass** — claim-neutral only:
- "Gated-Reset" → "Gated Reset" in prose (31 hits; kept the `\method-Gated-Reset` row label).
- "Full-Context"→"full-context"; "design-oracle" noun→"design oracle"; "human-AI"→"human--AI".
- Expanded "Lost in Conversation (LiC)" at first use; model-name casing; `AC3`→`\method`; dropped
  dead `\fix`/`\new` review macros.

No numbers or claims were touched. Everything below is **not** yet applied — it needs data or a
judgment call.

---

## BLOCKING — must resolve before any public post

### B1 ✅ The tau2-bench withdrawal is prose-only; Table 2 still shows the withdrawn wins
This is the most serious issue and it is real.

- The body (l.371) withdraws every tau2 improvement claim: it says two of three baselines were
  **rate-limit-clipped floors**, re-measured at N=3 to Baseline = **68.4 / 70.2 / 78.9** (gpt-5.4 /
  dsv / kimi), with **no \method operator beating them**, and Gated Reset = 57.9 / 57.9 / 71.9.
- But **Table 2** (`tab:megatable`, l.291–295) still prints the **old** tau2 Baseline
  **68.4 / 31.6 / 26.3**, so its operator cells read as large wins — e.g. Augment Kimi **57.9** vs
  Baseline **26.3**, Rewrite Kimi **73.7** vs **26.3**. A reader sees exactly the improvements the
  prose says are gone.
- **The re-measured baselines (70.2 / 78.9) appear in no table anywhere**, yet l.334 and l.402
  cite Table 2 for the claim "no operator beats the *re-measured* baseline."
- **Caption contradicts body:** caption (l.283) says Kimi's "true Baseline likely 40–50%"; body
  says re-measured **78.9**.
- **Numeric disagreement:** Table 2's Reset\* (= Gated Reset) tau2 cells = 52.6 / 47.4 / 68.4;
  body says Gated Reset = 57.9 / 57.9 / 71.9. Different numbers for the same quantity.
- The appendix (l.593, `app:tau2-diagnostic`) also points readers to "Table 2 (tau2 block)" for
  "headline tau2 results" — i.e. straight at the stale numbers.

**Fix requires data, not wordsmithing.** The paper does not currently contain a complete
re-measured N=3 tau2 matrix (Baseline/AO/Augment/Reset/Rewrite × 3 respondents). The body gives
baselines + Gated Reset + "Augment significantly worse"; Augment/Rewrite exact re-measured values
are not in the text. Options:
1. **Reconstruct the table** from the canonical N=3 tau2 run (the "855 scored rollouts" re-run
   referenced in the withdrawal commit `5565100` and `docs/sans_issue_injection_redux.md` /
   `docs/reports/post_may18_r6_overnight_progress.md`). Needs Matthew/co-author to confirm the
   source of truth, then a careful re-typeset. Best outcome.
2. **Interim safe fix:** replace the tau2 block cells with the re-measured baselines + Gated Reset
   we *do* have, mark Augment/Rewrite "n/a (superseded)" pending the pull, and delete the caption's
   "40–50%" parenthetical. Removes the contradiction without inventing numbers.

Either way, do **not** post with the current Table 2.

---

## SHOULD-FIX — internal-consistency cluster on the LiC headline

Root cause: **Table 1's Gated-Reset row and the body's gap-closure %s use the original
point/normalized values, while the variance appendix reports different N=3 means — and the caption
claims the row *is* the N=3 mean.**

### S1 ✅ The headline "67–82%" floor is unsupported by the paper's own appendix
Abstract (l.111), intro (l.140), conclusion (l.439) all claim "closes 67–82% of the multi-turn
gap." The **67% floor** comes only from actions Gated-Reset = **66.7** (Table 1, l.275):
(66.7−34.8)/(82.6−34.8)=66.7%. But the variance appendix's own N=3 actions mean is **61.3** (l.534),
giving **55%**; and l.543 *explicitly rejects* the normalization that yields 66.7. Using the
appendix means throughout, the honest range is **≈55–84%**, not 67–82%.

### S2 ✅ Table 1 caption's "mean over N=3" is false for 2 of 4 cells
Caption l.257 says the Gated-Reset row is "the mean over N=3 reruns per cell." Actual:
- code: Table 1 = **63.2**, but N=3 mean = **64.4** (63.2 is Run 2).
- actions: Table 1 = **66.7**, N=3 mean = **61.3** (5.4pp gap; matches neither mean nor any run).
- math (80.0) and database (38.7) do match. Intro l.140 ("15.8→63.2 on code; mean over N=3") thus
  labels a single run as the mean.

### S3 ✅ Code gap-closure reported as three different values
78% (appendix l.539, orphaned — no body location says 78) / 82% (body l.320, from the Run-2 value
63.2) / 84% (from the mean 64.4). Pick one basis (the N=3 mean → 84%) and use it everywhere.

**Recommended fix for S1–S3 (needs Matthew's sign-off — it changes a headline number):** make
Table 1's Gated-Reset row equal the appendix N=3 means (code 63.2→64.4, actions 66.7→61.3), then
propagate: headline range 67–82% → **≈55–84%**, code closure → 84%, and align the intro/conclusion
wording. This is a real weakening of the floor (55 vs 67), so it is a decision, not a silent edit.

### S4 ✅ `MT-OSC` is a named baseline with no citation and no expansion
Section title l.337 and "we reimplemented MT-OSC" (l.342). Absent from every `\cite`; acronym never
spelled out. A reviewer can't tell what was reimplemented. Add the reference + expansion. (This is
also FLAG-1 territory in `nice_to_have_experiments.md`.)

### S5 🟡 Broken cross-ref at l.577
"Headline GPT-5-mini numbers … are aggregated in the CollabLLM block of Table~\ref{tab:megatable}."
Table 2 has no GPT-5-mini column (columns are gpt-5.4/dsv/kimi), and those averages don't appear in
it. Re-point or drop the reference.

### S6 🟡 Abstract "only method that improves … on every … referential benchmark" vs CollabLLM
Table 2 shows AO also beats Baseline on all three CollabLLM respondents (57.5>55.0, 52.5>50.0,
63.2>57.5), and the body itself calls CollabLLM "mixed, no single operator dominant" (l.347). The
"only method" framing isn't distinguished on CollabLLM. Consider scoping the abstract claim.

---

## MINOR 🟡 (reviewer-reported, low-risk)
- **M1** Augment code value 52.6 (Table 1) vs 55.6 (appendix reading l.539).
- **M2** l.323 "outperform Augment on code (+5.5–8.8pp)" — Table 1 gives +5.3 to +10.6.
- **M3** `S0`/`S1`/`S2` operator labels used in the appendix (l.523+) but never defined in-paper
  (body names them Augment/Reset/Rewrite).

## Clean (no findings)
- All 33 `\cite` keys resolve; all `\ref` labels defined (no `[?]`/`??` in output).
- tau2 improvement claims in *prose* are consistently withdrawn (the survivors are in the **table**,
  B1).
- No em-dashes in prose; no leftover FIX/NEW margin markers.

---

## Recommended sequence
1. **Decide the tau2-table fix (B1)** — reconstruct from the N=3 run (preferred) or apply the
   interim superseded-marking. Blocking.
2. **Decide the LiC headline (S1–S3)** — adopt the ≈55–84% range from the appendix means, or
   re-examine which number is canonical. Blocking-ish (it's in the abstract).
3. Add MT-OSC citation/expansion (S4); fix the l.577 cross-ref (S5); consider the CollabLLM
   abstract scope (S6).
4. Author block + Figure 1 (from the 2026-09-03 report) remain the other two hard blockers.
5. Then post.

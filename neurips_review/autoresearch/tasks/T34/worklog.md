# T34 — Re-derive the `CHANGES.md` tally so it reconciles

**Date:** 2026-07-29 (overnight autonomous session)
**Scope:** bookkeeping only. Zero API calls, zero experiments, no `git checkout`,
`writing/overleaf_repo/` untouched. **No claim, no row, no number in any row and no
reviewer-facing text was changed.**

**Target:** `neurips_review/replies/v5/CHANGES.md` — the Tally section, the bucket scheme,
and §14.4 (T33's escalation note). One consequential knock-on edit to
`neurips_review/replies/v5/README.md` item (4), which recorded J4 as still open.

---

## 1. The problem, restated from the artifacts

T33 escalated J4 (`AR/tasks/T33/worklog.md`, item J4; `CHANGES.md` §14.4) because the Tally
did not reconcile against the rows it summarises:

* §§1–6 were counted at **81** numbered rows; the tally printed a total of **69**.
* "Corrected 17" stood against roughly **21** rows so labelled.
* **Eleven rows carried statuses that mapped to no bucket at all**.
* Only "Newly added 21" appeared to reconcile.

The diagnosis in the brief is right and is worth keeping on the record: an earlier pass (T28)
asserted the counts were the sum of the rows, and that was **true when written**. It decayed
because later passes (T19, T21, T25, T28 itself, T32) introduced *new status vocabulary*
— "replaced by results", "promise fulfilled", "HOLD → resolved", "not used", "bookkeeping" —
that no bucket covered, and each pass recorded its delta in a prose paragraph rather than
re-deriving the table. **The decay mechanism is prose-increment, not miscounting.** That is
why the fix includes a named rule and not just corrected numbers.

## 2. Method

Rows were extracted mechanically, not by eye, from lines 1–170 of `CHANGES.md` (the span
covering §§1–6) with a regex on table rows whose first cell is a row ID of the form
`\d+\.\d+[a-z]?`. Each row's **Status** cell was captured verbatim. The enumeration below is
that extraction; the bucket column is the only thing added.

**§6 (`05_final_remarks.md`) contains no numbered rows** — it is prose mirroring §§1–5. All
rows therefore sit in §§1–5, which is why "§§1–6" and "1.1–5.10" describe the same set.

## 3. Full row-by-row enumeration (82 rows)

Status text is verbatim from the file, including emphasis markers.

### §1 `00_general_response.md` — 24 rows

| # | Status as written | Bucket |
|---|---|---|
| 1.1 | `**unchanged**` | Unchanged |
| 1.2 | `**unchanged**` | Unchanged |
| 1.3 | `**unchanged**, now explicitly labelled *raw accuracy*` | Unchanged |
| 1.4 | `**corrected** (wording)` | Corrected |
| 1.5 | `**unchanged**` | Unchanged |
| 1.6 | `**qualified by T25**` | Corrected *(judgement call — §4.2)* |
| 1.7 | `**corrected**` | Corrected |
| 1.8 | `**unchanged**` | Unchanged |
| 1.9 | `**CORRECTED — the largest numeric change in v5**` | Corrected |
| 1.10 | `**unchanged in substance**, wording fixed` | Corrected *(judgement call — §4.2)* |
| 1.11 | `**corrected** (wording)` | Corrected |
| 1.12 | `**newly added**` | Newly added |
| 1.13 | `**struck / corrected against us (T28)**` | Struck *(precedence)* |
| 1.14 | `**unchanged, and strengthened**` | Unchanged |
| 1.15 | `**struck**` | Struck |
| 1.16 | `**CORRECTED — softened** (T21, from T20/§7 U4)` | Corrected |
| 1.17 | `**struck (pending T6)**` | Struck |
| 1.18 | `**replaced by results**` | Replaced by results |
| 1.19 | `**unchanged**` | Unchanged |
| 1.20 | `**newly added**` | Newly added |
| 1.21 | `**newly added**` | Newly added |
| 1.22 | `**newly added**` | Newly added |
| 1.23 | `**newly added — disclosure that moves against us**` | Newly added |
| 1.24 | `**resolved (T19)**` | HOLD → resolved |

§1 subtotal: Unchanged 7, Corrected 7, Struck 3, Replaced 1, Newly added 5, HOLD→resolved 1 = **24**.

### §2 `01_reviewer_iNYK.md` — 10 rows

| # | Status as written | Bucket |
|---|---|---|
| 2.1 | `**unchanged**` | Unchanged |
| 2.2 | `**newly added**` | Newly added |
| 2.3 | `**corrected**` | Corrected |
| 2.4 | `**HOLD → resolved (T28); the improvement claim is withdrawn** + **newly added concession**` | HOLD → resolved *(precedence over the trailing "newly added")* |
| 2.5 | `**corrected** (upgraded from assertion to measurement)` | Corrected |
| 2.6 | `**corrected**` | Corrected |
| 2.7 | `**unchanged**, with a new limits paragraph` | Unchanged |
| 2.8 | `**unchanged**` | Unchanged |
| 2.9 | `**corrected** (wording)` | Corrected |
| 2.10 | `**newly added — disclosure**` | Newly added |

§2 subtotal: Unchanged 3, Corrected 4, Newly added 2, HOLD→resolved 1 = **10**.

### §3 `02_reviewer_Vg97.md` — 12 rows

| # | Status as written | Bucket |
|---|---|---|
| 3.1 | `**replaced by results**` | Replaced by results |
| 3.2 | `**HOLD → resolved (T28)** + **newly added concession**` | HOLD → resolved *(precedence)* |
| 3.3 | `**corrected**` | Corrected |
| 3.4 | `**corrected** (wording)` | Corrected |
| 3.5 | `**newly added**` | Newly added |
| 3.6 | `**unchanged**` | Unchanged |
| 3.7 | `**promise fulfilled**; numbers **unchanged** and now labelled raw/N=1` | Replaced by results *(judgement call — §4.2)* |
| 3.8 | `**unchanged**` | Unchanged |
| 3.9 | `**newly added**` | Newly added *(no `*(new)*` marker — see §5.2)* |
| 3.10 | `**unchanged**` | Unchanged |
| 3.11 | `**newly added, then REVISED by T25**` | Newly added *(judgement call — §4.2)* |
| 3.12 | `**newly added — disclosure**` | Newly added |

§3 subtotal: Unchanged 3, Corrected 2, Replaced 2, Newly added 4, HOLD→resolved 1 = **12**.

### §4 `03_reviewer_5YHP.md` — 26 rows (including 4.18a)

| # | Status as written | Bucket |
|---|---|---|
| 4.1 | `**unchanged**` | Unchanged |
| 4.2 | `**newly added — the strongest new mechanism evidence**` | Newly added |
| 4.3 | `**newly added — concession**` | Newly added |
| 4.4 | `**half struck; the struck half is now permanent (T28)**` | Struck *(precedence)* |
| 4.5 | `**corrected, then partly restored**` | Corrected |
| 4.6 | `**corrected**` | Corrected |
| 4.7 | `**unchanged**` | Unchanged |
| 4.8 | `**CORRECTED — claim struck**` | Struck *(precedence)* |
| 4.9 | `**corrected — strengthened**` | Corrected |
| 4.10 | `**CORRECTED — now N=3** (T21)` | Corrected |
| 4.11 | `**STRUCK — factually wrong**` | Struck |
| 4.12 | `**struck**` | Struck |
| 4.13 | `**replaced by results**` | Replaced by results |
| 4.14 | `**newly added — disclosure**` | Newly added |
| 4.15 | `**replaced by results**` | Replaced by results |
| 4.16 | `**newly added — correction to a paper claim; RE-CORRECTED by T25**` | Newly added *(judgement call — §4.2)* |
| 4.17 | `**newly added**` | Newly added |
| 4.18 | `**corrected (T16), and U1 retired**` | Corrected |
| **4.18a** | `**newly added — self-stated limitation**` | Newly added *(**the row T33's count of 81 missed** — see §5.1)* |
| 4.19 | `**struck**` | Struck |
| 4.20 | `**unchanged**` | Unchanged |
| 4.21 | `**unchanged**` | Unchanged |
| 4.22 | `**newly added — answers W6 with the strong half**` | Newly added |
| 4.23 | `**newly added — self-stated limitation**` | Newly added |
| 4.24 | `**not used**` | Bookkeeping / not used |
| 4.25 | `**unchanged**` | Unchanged |

§4 subtotal: Unchanged 5, Corrected 5, Struck 5, Replaced 2, Newly added 8, Bookkeeping 1 = **26**.

### §5 `04_response_to_AC.md` — 10 rows

| # | Status as written | Bucket |
|---|---|---|
| 5.1 | `**unchanged**` | Unchanged |
| 5.2 | `**corrected**` | Corrected |
| 5.3 | `**corrected**` | Corrected |
| 5.4 | `**half struck / HOLD → resolved (T28)**` | Struck *(precedence over HOLD → resolved)* |
| 5.5 | `**corrected**` | Corrected |
| 5.6 | `**newly added**` | Newly added |
| 5.7 | `**newly added**` | Newly added |
| 5.8 | `**unchanged**, extended` | Unchanged |
| 5.9 | `**newly added — disclosure**` | Newly added |
| 5.10 | `**bookkeeping (T19); discharged (T28)**` | Bookkeeping / not used |

§5 subtotal: Unchanged 2, Corrected 3, Struck 1, Newly added 3, Bookkeeping 1 = **10**.

### §6 `05_final_remarks.md` — 0 rows

Prose only; mirrors §§1–5. Contributes nothing to the tally, which is worth stating because
the tally is labelled "§§1–6" and a reader may otherwise go looking for the missing rows.

## 4. The bucket scheme and why each boundary falls where it does

### 4.1 Assignment rule

Read the row's **Status** cell only, take the tokens it contains, and where a cell carries
more than one token assign the single highest-precedence one:

> **Struck > Corrected > HOLD → resolved > Replaced by results > Newly added > Unchanged > Bookkeeping.**

Precedence runs least-flattering-first, so it doubles as the tie-break for judgement calls:
where a row can honestly be read two ways, take the reading that concedes more. Every row
then lands in exactly one bucket and the buckets sum to the row count — which is the property
the old table lacked.

### 4.2 The statuses that mapped nowhere, and the decisions taken

**"replaced by results" (1.18, 3.1, 4.13, 4.15) and "promise fulfilled" (3.7) → new bucket
*Replaced by results*.** These are v4 sentences of the form "we are adding X / we will report
X", discharged by a measurement. Nothing in v4 was *wrong*; a promise was kept. Folding them
into *Corrected* would inflate our own error count with items that are not errors — which is
the flattering-looking direction here but is still false, and it would corrupt the number the
"corrections we are making to our own numbers" list is built from. Folding them into
*Unchanged* would hide that the text was substantially rewritten. Own bucket. "Promise
fulfilled" is the same event under a different word and is folded in with it.

**"HOLD → resolved" (2.4, 3.2) and "resolved (T19)" (1.24) → new bucket *HOLD → resolved*.**
A claim deliberately sealed pending an in-flight audit (the tau2 blocks for T6; the
provisional-pending-T14 flag for 1.24), then unsealed by that audit's result. This is a
*process* state, not a defect: unlike *Corrected*, nothing wrong was ever printed; unlike
*Struck*, the row was not removed. 1.24 is not a tau2 hold but is structurally identical — a
caveat sealed pending an in-flight task, lifted when the task landed — so it is folded in
rather than given a bucket of one.

**"not used" (4.24) and "bookkeeping" (5.10) → new bucket *Bookkeeping / not used*.** Neither
row audits a reviewer-facing assertion. 4.24 records a framing ("memory is order-robust")
retired by F12 *before it was ever written into a reply*; 5.10 records where an internal note
sat relative to a HOLD block. Counting them as audited claims overstates the audit's scope;
deleting them loses the record, which is the entire reason 4.24 exists ("recorded so it is
not reintroduced"). They are counted, in a bucket that says what they are.

**"qualified by T25" (1.6) → *Corrected*.** Judgement call, taken against us. The two v4
means are correct and unchanged, but v5 materially qualifies what they support (the
head-to-head over the same 36 triples is +2.6pp on 15 W / 17 L / 4 T, a wash outside
LiC-database). New reviewer-facing wording exists where v4's did not, so it is a wording
change: *Corrected*, not *Unchanged*.

**"unchanged in substance, wording fixed" (1.10) → *Corrected*.** Judgement call, taken
against us. The bucket definition is "a v4 number **or wording** changed"; the wording was
fixed ("reruns" → "runs", per-run deltas added). The lead word "unchanged" describes the
substance, not the text. T33's table counted this one as "Unchanged (+1)"; T34 counts it as
a correction, per the least-flattering rule.

**"struck / corrected against us" (1.13), "half struck" (4.4, 5.4), "CORRECTED — claim
struck" (4.8) → *Struck*.** Precedence, and it is the least-flattering reading: if any part
of a claim is gone from v5, the row records a removal. This is the largest single re-bucketing
— it is why *Struck* moves from a printed 6 to 9 while *Corrected* does not simply absorb
them.

**"newly added, then REVISED by T25" (3.11) and "newly added — correction to a paper claim;
RE-CORRECTED by T25" (4.16) → *Newly added*.** These two are the only place where the
precedence rule is deliberately not applied, and the reason is definitional rather than
charitable. *Corrected* is defined as "a **v4** number or wording changed"; both rows'
Claim columns read `*(new)*`, so there is no v4 claim for them to have corrected. What was
revised was v5's own first attempt, in-flight, before anything was posted. Booking them as
corrections of v4 would be a category error that happens to look self-flagellating.
**Recorded here explicitly because it is the one judgement call that does not follow the
least-flattering tie-break**, and a reader is entitled to check it. Both rows remain
individually visible in the §Tally row lists.

## 5. Two counting errors in T33's escalation table, reported and corrected

Neither is a bucket disagreement. Both are recorded in `CHANGES.md` §14.4 as well as here.

### 5.1 The row count is 82, not 81 — row 4.18a was missed

T33's table asserts "**81 numbered rows**, 1.1–5.10, no gaps or duplicates". The mechanical
extraction returns **82**. The difference is exactly **4.18a**, which is a full table row with
its own Claim cell (`*(new — added by T19)*`), its own Status (`**newly added —
self-stated limitation**`), its own Evidence (F39, `AR/tasks/T16/report.md`) and its own
New-wording cell. It is a distinct claim — the firing-rate-vs-detection-rate caveat, disclosing
that 29% (LiC) / 73% (CollabLLM) of gate-open records have the analyzer writing
`issues: "None"` while still setting `needs_edit=true` — not a sub-note of 4.18, which is the
gate-rate correction itself. The lettered ID presumably caused an ID-range scan
("1.1–5.10") to skip it.

### 5.2 *Newly added* is 22, not 21 — the one bucket believed to reconcile did not

T33 recorded "Newly added | 21 | **21** ✓". Under the assignment rule, **22** rows carry a
*newly added* status. The 21 that T33 (and the printed tally) counted are exactly the rows
whose **Claim** column reads `*(new)*`. The 22nd is **3.9**, whose Claim column reads
"Q3 analyzer-model sensitivity — **v4 never answered this half of the question**". By the
tally's own printed definition — *a result that did not exist in v4* — 3.9 is newly added, and
its Status cell says so. It lacks the `*(new)*` marker only because the *question* existed in
v4 even though the answer did not.

This matters more than one row: "Newly added reconciles" was the reason to believe the rest of
the table was merely stale rather than mis-derived. It did not reconcile; it agreed by
coincidence with a differently-defined set.

Rows **2.4** and **3.2** also carry a trailing `+ **newly added concession**` token. They lead
with *HOLD → resolved* and are counted once, there. Had they been double-counted the bucket
would read 24, which is a third way the old number could have been produced and is worth
naming so it is not "rediscovered" later.

## 6. Reconciled counts

| Bucket | Count |
|---|---|
| Unchanged | 20 |
| Corrected | 21 |
| Struck | 9 |
| Replaced by results | 5 |
| HOLD → resolved | 3 |
| Newly added | 22 |
| Bookkeeping / not used | 2 |
| **Total numbered rows, §§1–6** | **82** |

20 + 21 + 9 + 5 + 3 + 22 + 2 = 82. ✓

Stated outside the total, because neither describes a §§1–6 row:

* **On HOLD = 0.** No row carries a live hold; all three former holds are in *HOLD → resolved*.
* **UNVERIFIED = 1** (U6). This lives in **§7**, the liability list, alongside U1–U5. The old
  table's "Total claims audited 69" was explicitly "68 rows + 1 UNVERIFIED", i.e. it added a
  §7 item into a §§1–6 row count. That is a category error independent of the miscounts, and
  it is why the two lines are now printed below the total rather than inside it.

### Movement against the old printed table

| Bucket | Printed (pre-T34) | Row-derived (T34) | Where the difference comes from |
|---|---|---|---|
| Unchanged | 24 | 20 | 1.6 and 1.10 re-read as *Corrected*; the remaining gap cannot be attributed row-by-row because 24 was never row-derived |
| Corrected | 17 | 21 | Not attributable row-by-row either — 17 was an incremented prose figure (14→15→16→17), not a count. The 21 is derived: 1.13 and 4.8 leave for *Struck*, 1.6 and 1.10 join |
| Struck | 6 | 9 | +1.13, +4.4, +4.8, +5.4 under the precedence rule |
| Replaced by results | — | 5 | new bucket |
| HOLD → resolved | — | 3 | new bucket |
| Newly added | 21 | 22 | +3.9 (§5.2) |
| Bookkeeping / not used | — | 2 | new bucket |
| Total | 69 | 82 | +11 previously-unbucketed rows, +4.18a (§5.1), −1 UNVERIFIED moved out of the total (69 = 68+1) |

## 7. The decay mechanism, named

Added at the head of the Tally in `CHANGES.md`:

> **Derivation rule (T34).** *This table is derived from the numbered rows of §§1–6 and from
> nothing else. Whenever a row is added, removed, or its Status cell changes, re-derive every
> bucket from the rows — do not increment the table in prose.*

The four "Changes made by T*n*" paragraphs beneath the tally are now explicitly labelled as a
historical record rather than as the tally, since each of them is an instance of the
prose-increment pattern the rule forbids. They are kept — the audit trail of how the counts
moved is worth having — but they are no longer the source of truth.

## 8. Escalated rather than fixed

Per the brief, row-level defects are **reported, not repaired**. Nothing found rises to
"a claim mislabelled" — no row's status contradicts its own Evidence or New-wording cells —
but three items are recorded for whoever next edits the rows:

1. **Row 1.17's status reads `**struck (pending T6)**`, and T6 has since landed.** The claim
   ("tau2 confirms the rule: lightest operator wins on the strongest model, heaviest on the
   weakest") is correctly struck and stays struck — §12.3 makes that permanent, and the
   parallel row 4.4 was updated at T28 to say "the struck half is now permanent (T28)".
   1.17's parenthetical was not updated in the same pass, so it still reads as *provisionally*
   struck pending an audit that has finished. **Bucket is unaffected** (Struck either way),
   which is why T34 did not touch it — editing it would change a row's status text, and the
   brief forbids that. Recommend a one-word fix by whoever next has row-edit authority:
   "(pending T6)" → "(T6 landed; permanent — §12.3)".
2. **Rows 4.24 and 5.10 are not claims.** 4.24 audits a framing that was never written into a
   reply; 5.10 audits the placement of an internal note. They are legitimately in the table as
   provenance, but any future statement of the form "we audited N claims" should quote **80**
   (82 − 2), not 82. The Tally prints them in a bucket that says exactly this rather than
   silently excluding them.
3. **Row 1.24 audits a v5 preamble caveat, not a v4 claim.** "Every LiC figure is provisional
   pending T14" was written by T15 into v5 and lifted by T19; it never appeared in v4. It sits
   in a table headed "Claim as written in v4". Harmless as provenance, and it does not affect
   the total, but it is the same category as the two above.

Also noted, not acted on: the "Of the 17 corrections, 8 move against us, 3 in our favour"
paragraph. Its 17 no longer matches the row-derived Corrected count of 21. T34 **did not
rewrite it** — the eight/three/wording split enumerates *named* corrections and re-deriving it
means deciding, claim by claim, which of the newly-bucketed rows move against us, which is a
claim decision and outside a bookkeeping task. It is annotated in place, in the same bracketed
style the file already uses for T30's annotations, stating that the 17 is the pre-T34 figure
and pointing at the row-derived 21. **No reviewer-facing file quotes either number**; the
reviewer-facing self-correction count is the separate "eight in total" (§14.2), which is
independently correct.

## 9. Files changed

* `neurips_review/replies/v5/CHANGES.md` — Tally table replaced and made row-derived; bucket
  scheme, assignment rule, precedence order, per-bucket row lists and the T34 bookkeeping note
  added; historical-record label added above the "Changes made by T*n*" paragraphs; the
  "17 corrections" paragraph annotated in place; §13.3's superseded 17/69 annotated; §14.4
  rewritten from "escalated, not fixed" to the resolution, retaining T33's original table as
  the record of what was found.
* `neurips_review/replies/v5/README.md` — item (4) of the T33 change list said J4 was
  escalated; a T34 paragraph records the closure and the reconciled counts.

**Verified: no numbered row line in `CHANGES.md` was added, removed or altered.**
`git diff -U0 -- neurips_review/replies/v5/CHANGES.md | grep -E '^[-+]\| *[0-9]+\.[0-9]+[a-z]? '`
returns nothing. `git diff --stat -- neurips_review/replies/v5/` touches only `CHANGES.md`
and `README.md`; the six reply files are untouched.

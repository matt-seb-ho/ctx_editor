# T35 — Close the three row-level items T34 reported but was not authorised to fix

**Date:** 2026-07-29 (overnight autonomous session)
**Scope:** two row edits in `neurips_review/replies/v5/CHANGES.md` plus their bookkeeping
notes. Zero API calls, zero experiments, no `git checkout`, `writing/overleaf_repo/`
untouched (not read, not written). No claim, number or reviewer-facing sentence changed
beyond what the two row fixes require.

**Inputs:** `AR/tasks/T34/worklog.md` §8 (items 1–3); `AR/WORKLOG.md` F91 items 2–4;
`AR/WORKLOG.md` F78–F81 (D21, the T6 tau2 outcome); `CHANGES.md` §12.3.

---

## 0. Counts verified before editing, per the brief

The brief's own figures were re-derived rather than trusted, since T34 found T33's
escalation carried an off-by-one.

* **Row count = 82.** Mechanically extracted from lines 89–213 of `CHANGES.md` (§§1–6) with
  a regex on table rows whose first cell is an ID `\d+\.\d+[a-z]?`. IDs 1.1–5.10 including
  **4.18a**; no gaps, no duplicates. Matches T34, not T33's 81.
* **Bucket sums unchanged by this task**: Unchanged 20, Corrected 21, Struck 9, Replaced by
  results 5, HOLD → resolved 3, Newly added 22, Bookkeeping / not used 2 = **82**. Re-derived
  after the edits with the same script; the only row where a keyword rule and the printed
  scheme differ is **1.10** ("unchanged in substance, wording fixed"), which the scheme
  documents as a judgement call booked to *Corrected* — so the printed 20/21 split stands.
* **`*(new)*` markers**: 21 before this task, **22** after, matching the *Newly added* bucket.

---

## 1. Row 1.17 — stale "pending T6"

**Before** (`CHANGES.md` §1, row 1.17):

> | 1.17 | tau2 "confirms the rule: lightest operator wins on the strongest model, heaviest on
> the weakest" | `**struck (pending T6)**` | derived from the same N=1 cells T6 is
> re-measuring | removed; replaced by the analyzer-sweep evidence (F21/F22) as the CW1
> generality argument |

Two cells were stale, not one: the Status parenthetical *and* the Evidence cell's present
tense ("T6 **is** re-measuring").

**Reference row read first, as instructed.** Row 4.4 is the parallel row T28 updated:

> Status `**half struck; the struck half is now permanent (T28)**`; Evidence "…the AC3 half
> depended on the contested cells and **T6 refuted it**"; New wording "…is **gone for good**,
> not pending (§12.3)".

**After:**

> | 1.17 | *(claim cell unchanged)* | `**struck; the strike is now permanent (T28)**` |
> derived from the same N=1 cells **T6 re-measured at N=3, and T6 refuted them** (F78/F79):
> two of three published baselines did not replicate, and on all three models the re-measured
> baseline is at or above every AC3 arm. The positive controls reproduced, so this is "the
> published baselines were wrong", not "not comparable" | removed; **gone for good**, not
> pending (§12.3); replaced by the analyzer-sweep evidence (F21/F22) as the CW1 generality
> argument |

1.17 is a whole-claim strike where 4.4 is a half-strike, so the wording is 4.4's with "the
struck half" → "the strike"; "gone for good, not pending (§12.3)" is 4.4's phrase verbatim.

**Outcome description checked against F78–F81 / §12.3.** All four elements the brief lists
are correct as stated there, and the row now asserts the first three:

| Element | Source | In the row? |
|---|---|---|
| Two of three published baselines did not replicate (DSV4F 31.6 → 70.2 ± 11.0; Kimi 26.3 → 78.9 ± 0.0) | F78, §12.3 table | yes, without re-printing the numbers — they are already in rows 1.13 / 1.15 and §12.3 |
| Re-measured baseline at or above every AC3 arm on all three models | F78 | yes |
| Positive control reproduced ⇒ "published baselines were wrong", not "not comparable" | F79 | yes |
| AO = 0.0 across 9 cells / 171 rollouts survives | F79, §12.3 | **deliberately not added** — see below |

**Why AO is not mentioned in 1.17.** 1.17's claim is the *operator-ordering rule* (lightest
operator wins on the strongest model). AO = 0.0 is a different claim and is carried by rows
**1.14** ("Assistant omission collapses to 0% on every model — unchanged, and strengthened")
and **4.4**, both of which already state that it survives. Adding it to 1.17 would attach a
surviving result to a struck claim it does not support. The survival of AO was verified as
still recorded (1.14, 4.4, §12.3, README Blocker 2) rather than re-asserted here.

**Numbers added: none.** The row cites F78/F79 and characterises the outcome; every figure
behind it is already printed in 1.13, 1.15 and §12.3, so no figure is duplicated into a new
place where it could later drift.

**Bucket: unchanged.** Status still leads with "struck" → *Struck* under the precedence rule,
before and after. Tally unaffected.

## 2. Row 3.9 — missing `*(new)*` marker

**Before:** `| 3.9 | Q3 analyzer-model sensitivity — **v4 never answered this half of the question** | **newly added** | …`

**After:** `| 3.9 | *(new)* Q3 analyzer-model sensitivity — **v4 never answered this half of the question** | **newly added** | …`

Status, evidence and new-wording cells untouched. Marker placed leading, as in every other
row that carries it. `*(new)*` count 21 → **22**, matching the *Newly added* bucket of 22 —
which was T34's whole point in §5.2: the bucket believed to reconcile only agreed with a
differently-defined set.

**Consequential prose fix in the same file.** The Tally's paragraph "The one status where the
Claim column overrides the Status cell: none" asserted that 3.9 *lacks* the marker. That
sentence became false the moment the marker was added, so it is rewritten to say the
disagreement existed and is now closed (T35), keeping the same explanation of *why* 3.9 is
newly added. The bucket count in that paragraph (22) is unchanged.

**Bucket: unchanged.** *Newly added*, before and after.

## 3. The "we audited N claims" figure — nothing to correct, and the number is not 83

Searched for the figure rather than assuming it exists:

* `grep -rn '\b83\b'` across `replies/v5/*.md` — **no match** outside decimal figures
  (83.0% code baseline, 0.79–0.83 PABAK, 82.5%). No file states 83 of anything countable.
* `grep -rnE '\b(6[0-9]|7[0-9]|8[0-9]) (claims|assertions|rows)'` across the whole repo
  (excluding `writing/overleaf_repo/`, untouched) — the only live hits are the Tally's own
  "**Total numbered rows, §§1–6** = 82", correctly labelled *rows*, and two historical
  records of the tally as it stood at T15: "64 claims" in `AR/tasks/T15/worklog.md:8` and in
  `PROVENANCE.md:50`. Both describe a past state of the table and are correct as history.
* `grep -rniE 'we audited|audited (all|every|[0-9]+)'` — the only hits are T34's own
  recommendation (`AR/tasks/T34/worklog.md:338`), the orchestrator's restatement of it
  (`AR/WORKLOG.md:754`), and unrelated prose ("we audited the judge", "audited every trace").

**So no reviewer-facing file, and no file at all, quotes an audited-claims total.** Item 3
required no edit. **83 corresponds to nothing that was ever printed** — it appears only in the
orchestrator's phrasing of the recommendation at `WORKLOG.md:754`, which is a note about what
a future statement should say, not a statement. Nothing was changed there: `WORKLOG.md` is the
session record, and rewriting a logged recommendation would falsify the log.

### 3.1 Escalated: the recommended figure is under-specified, and the two derivations disagree

Reported rather than acted on, per "if closing one reveals a further problem, report it".

1. **80 = 82 − 2 and 82 − 3 = 79 are both in the record.** T34's worklog §8 item 2 derives
   **80** by excluding the two *Bookkeeping / not used* rows (4.24, 5.10), and separately
   notes at item 3 that **1.24** is "the same category" but "does not affect the total".
   `WORKLOG.md:754` and this task's brief fold all three together — "rows 4.24, 5.10 and 1.24
   audit no v4 claim" — which yields **79**, not 80. Both cannot be right.
2. **The criterion, applied consistently, gives neither.** "Audits no v4 claim" is true of all
   **22** *Newly added* rows as well: their Claim cells read `*(new)*` precisely because there
   is no v4 text behind them — this is the reasoning `CHANGES.md` already uses to keep 3.11
   and 4.16 out of *Corrected* ("*Corrected* means a **v4** claim changed"). Applied without
   exception, "v4 claims audited" = 82 − 22 (new) − 2 (bookkeeping) − 1 (1.24) = **57**.
3. **Therefore the question is definitional, not arithmetical.** "82 numbered rows", "80 rows
   that audit a reviewer-facing assertion", "79 rows that concern v4 text", and "57 v4 claims
   re-checked" are four different true statements about the same table. Choosing which one a
   sentence should quote is a decision about how we characterise our own audit — the same
   class of decision T34 declined for the "17 corrections" split — and it is a decision with
   no consumer right now, since nothing quotes any of them.

**Recommendation, for whoever has claim-edit authority:** if such a sentence is ever written,
quote the row count with its label ("82 rows, of which 2 record no reviewer-facing claim")
rather than a bare "we audited N claims", which cannot be made unambiguous. Do **not** print
80 without stating the exclusion rule that produces it.

---

## 4. Files changed

* `neurips_review/replies/v5/CHANGES.md` — rows **1.17** and **3.9**; the Tally paragraph that
  asserted 3.9 lacked its marker; a **T35 bookkeeping note** below T34's; one clause added to
  the revision history at the head of the file.
* `neurips_review/replies/v5/README.md` — a **T35's changes** paragraph after T34's, since
  T34's paragraph records 3.9's missing marker as an open finding.
* `neurips_review/autoresearch/tasks/T35/worklog.md` — this file.

**Verified after editing:**

* Row count still **82**; buckets still 20 / 21 / 9 / 5 / 3 / 22 / 2 = 82. The printed tally
  needed no change and was not changed.
* `git diff -U0 -- neurips_review/replies/v5/CHANGES.md | grep -E '^[-+]\| *[0-9]+\.[0-9]+[a-z]? '`
  returns exactly **two** row pairs — 1.17 and 3.9 — and no others.
* The six reviewer-facing reply files (`00`–`05`) are **untouched**; `git diff --stat` over
  `replies/v5/` lists only `CHANGES.md` and `README.md`.
* `writing/overleaf_repo/` neither read nor written by this task.

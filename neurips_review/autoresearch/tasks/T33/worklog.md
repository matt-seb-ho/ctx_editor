# T33 — final cleanup sweep before handoff

**2026-07-29, autonomous overnight session.** Operator asleep; no questions asked.
**Cost: zero API calls, zero experiments, zero rollouts.** No `git checkout`.
`writing/overleaf_repo/` neither read nor written (T31 owns it read-only).

**Task.** Three loose ends left by earlier agents: (1) T30's judgement calls **J3** and **J4**,
scoped as "internal count wording only"; (2) the mislabelled Table 2 caption T32 found in
`tasks/T2c/`, to be fixed at the generator and regenerated; (3) the "six documents" tone leak T30
flagged in reviewer-facing text.

**Verdict (one line): three of the four items were exactly as described and are fixed; J4 is
bigger than "count wording" — the tally in `CHANGES.md` does not reconcile with its own rows, so
it is escalated rather than edited.**

---

## 1. Item 3 — the "six documents" tone leak (reviewer-facing)

T30 §5.2: two reviewer-facing sentences described the reply set by its internal file count. A
reviewer sees a discussion thread, not our directory.

| file | before | after |
|---|---|---|
| `replies/v5/00_general_response.md` (CW2, ln 105) | "…so we would rather assemble the whole picture here than leave a reader to **do it from six documents**." | "…than leave a reader to **piece it together from our separate replies**." |
| `replies/v5/04_response_to_AC.md` (lead-in, ln 48) | "…in **Common Weakness 2**, rather than leave it **distributed across six documents**." | "…rather than leave it **distributed across our separate replies**." |

Wording only — no claim, number, emphasis or section reference moves. Verified afterwards that
`grep -rn "six documents" replies/v5/*.md` returns only the two before/after lines in the new
`CHANGES.md` §14.1. The two surviving "six files" mentions are in `README.md:9` and `CHANGES.md`
§11, both internal documents, and were left alone.

**T30's other two register notes were deliberately not touched.** The clustered bolded
self-narrating lead-ins in `00` CW2/CW5 have no local fix (removing one of three is arbitrary; the
sentences are individually good), and `03` W5's length is a structural note whose suggested remedy
— "consider a two-sentence summary at its head" — is new drafting, not a cleanup. The brief said
fix only if obvious and local, and no style pass.

---

## 2. Item 1a — J3 (`README`'s dangling ordinal): verified, then fixed

**T30's description.** `README`'s tractability paragraph reads "seven of our own numbers moved, six
of them against us … and **an eighth** correction raises a *competitor's* number". The counts are
right, but the ordinal "eighth" points at ERGO, which is item **7** in `05` and item **5** in `04`,
so it resolves to nothing.

**Verified before editing** (the counts, not just the ordinal), against
`replies/v5/05_final_remarks.md` §"Corrections We Are Making to Our Own Reported Numbers":

| # in `05` | correction | ours? |
|---|---|---|
| 1 | CollabLLM MATH-Hard tie at N=3 (+ AO column, BigCodeBench) | ours |
| 2 | False-negative-adjusted accuracy → raw accuracy | ours |
| 3 | Selective-editing claim retracted for both operators | ours |
| 4 | WildChat headline 89.8/92.1 → 87.8/91.2 | ours |
| 5 | Memory gains below the noise floor | ours |
| 6 | BigCodeBench scoring (executable tests *are* available) | ours |
| **7** | **ERGO denominators — raises a competitor** | **not ours** |
| 8 | tau2 improvement claim withdrawn | ours |

Seven ours + ERGO = eight ✅, so "seven of our own numbers moved" and "we surface all eight
ourselves" are both correct and the fix really is wording. Applied to
`replies/v5/README.md:52`:

* **Before:** "…and **an eighth correction** raises a *competitor's* number."
* **After:** "…and **the ERGO correction** raises a *competitor's* number."

The following clause ("We surface all eight ourselves … the six most consequential in `04`, all
eight in `05`") is unaffected and was re-read for consistency.

---

## 3. Item 1b — J4: **escalated, not fixed** (it is not count wording)

**T30's description.** The `CHANGES.md` tally prose reads "Of the 17 corrections, **8 move against
us** …, **3 move in our favour** …, and the remainder are wording-only". T30 flagged that the split
of the 17 was partly inherited — the T25 increment (15 → 16) was recorded in prose without a
row-level attribution — and said closing it "needs one pass over the rows with a status column,
not an inference".

**I did that pass.** `CHANGES.md` §§1–6 carry **81** numbered claim rows (`1.1`–`5.10`, no gaps, no
duplicates), each with a status column. Bucketing the status strings mechanically:

| Tally table says | rows actually carrying that status |
|---|---|
| Newly added **21** | **21** ✅ exact |
| Unchanged **24** | 20 "unchanged" + 1 "unchanged in substance" = **21** |
| Corrected **17** | 20 "corrected" + 1 "struck / corrected against us" = **21** |
| Struck **6** | 5 "struck" + 2 "half struck…" = **7** |
| Total **69** (= 68 rows + 1 UNVERIFIED in §7) | **81 rows** |

A further **11** rows carry statuses that map to no bucket at all: "replaced by results" (×4),
"HOLD → resolved" (×2), "resolved (T19)", "qualified by T25", "promise fulfilled", "not used",
"bookkeeping (T19)".

**Why this is an escalation rather than an edit.** Only one bucket (Newly added) reconciles. The
tally's own bookkeeping note asserts "*The counts above are the sum of the rows*" (T28), and that
statement is not true of the current rows. Fixing J4 therefore is not rewording a sentence: it
requires deciding which of eleven unmapped statuses count as corrections, whether "half struck" is
a strike, and then re-deriving every bucket and the total — i.e. changing the headline number the
document uses to characterise its own audit. That is a bookkeeping decision the operator should
make visibly, and it is outside a bounded cleanup.

**Blast radius, checked:** the **17 is internal-only**. `grep` over `replies/v5/0*.md` finds no
reviewer-facing quotation of the tally counts. The reviewer-facing self-correction count is the
separate "seven of our own numbers moved … eight in total", which is re-verified correct in §2
above. So nothing that goes in front of a reviewer depends on this.

Recorded in `CHANGES.md` §14.4 with the table above so the next reader does not have to re-derive
it.

---

## 4. Item 2 — the mislabelled caption, fixed at the generator

**What T32 found** (`tasks/T32/worklog.md` §§2.2, 3): `final_tables.py:116` passes the **union**
label `leak_final` (answer-verification pass ∪ math-only model-free numeric probe, defined at
`:37`) into Table 2's split, but captions that table *"strict: analyzer output verified to contain
the correct answer"* — which describes only the first arm. That mislabel is the proximate cause of
the J2 confusion T32 spent a pass resolving. T32 correctly declined to hand-patch the generated
`RESULTS.md`, since regeneration would reproduce the caption.

**Verification before touching anything.** Ran `final_tables.py` unmodified and diffed its stdout
against `RESULTS.md` from line 18 (the file's first 17 lines are hand-written header prose):

```
diff <(tail -n +18 RESULTS.md) <(python3 final_tables.py)   →  IDENTICAL
```

So the committed file was an unmodified generator dump and could be safely regenerated. Also
backed up `leak_labels_final.jsonl`, which the script rewrites as a side effect, and confirmed it
comes back byte-identical (`cmp` clean, both before and after the edit).

**The fix** — `tasks/T2c/final_tables.py:116`:

* **Before:** `table_paired("leak_final", "strict: analyzer output verified to contain the correct answer")`
* **After:** `table_paired("leak_final", "primary — union: analyzer output verified to contain the correct answer OR the math-only model-free numeric probe fires")`

**Regenerated `tasks/T2c/RESULTS.md`** (17-line header preserved verbatim + fresh generator
output). Diff against the previous file:

```
31c31
< ### Table 2 — … split by leakage (strict: analyzer output verified to contain the correct answer)
---
> ### Table 2 — … split by leakage (primary — union: analyzer output verified to contain the correct answer OR the math-only model-free numeric probe fires)
```

**One line, and nothing else moved.** Every rate, `n`, Δ, CI, W/L and p-value in both Table 2s and
in Table 1 is byte-identical, as is `leak_labels_final.jsonl`. The brief asked for this to be
confirmed explicitly and it is confirmed: no finding here.

**Left alone deliberately:** Table 1's column head "answer verified correct (**strict leak rate**)"
and the second `table_paired(...)` caption ("conservative: LLM judge's 3-way label"). Table 1's
column is computed at `:64` from `answer_verdict` alone, so "strict" is accurate there — that
column is the *reason* 54/144 and 58/547 exist, and relabelling it would break the single-detector
reference rates `03` W1 now quotes after T32. The judge caption describes `leak_judge` correctly.

`RESULTS.md`'s hand-written header (lines 1–17) was preserved unchanged. Noted but **not edited**,
as out of scope and pre-existing: its one-line answer says math is "38-40%" (the two single
detectors, accurate as stated, though the union rate `03` now reports is 47%) and quotes database
"+26.5pp" (the all-147 row, where the no-leak row is +26.0). Neither is wrong as written; both are
looser than the reply text and are flagged here only so a later reader is not surprised.

---

## 5. Files changed

| file | change | reviewer-facing? |
|---|---|---|
| `replies/v5/00_general_response.md` | "six documents" → "our separate replies" | **yes** (wording) |
| `replies/v5/04_response_to_AC.md` | "six documents" → "our separate replies" | **yes** (wording) |
| `replies/v5/README.md` | J3 ordinal → "the ERGO correction"; new T33 revision paragraph | no |
| `replies/v5/CHANGES.md` | new **§14** (T33 record, incl. the J4 escalation table); revision-history line extended; §13.2 notes the caption is now fixed | no |
| `tasks/T2c/final_tables.py` | line 116 caption corrected to the union label | no |
| `tasks/T2c/RESULTS.md` | regenerated; caption line only | no |
| `tasks/T33/worklog.md` | this file | no |

`leak_labels_final.jsonl` was rewritten by the regeneration run and verified byte-identical to its
pre-run backup, so it is not listed as a change.

---

## 6. What remains open after T33

* **J4** — the `CHANGES.md` tally does not reconcile with its own 81 rows (§3). Internal-only;
  needs an operator decision on bucket definitions, not an inference.
* Everything else T30 and T32 left is closed. T30's J1 and J2 were settled by T32; J3 is settled
  here; the T2c caption is settled at its source.
* Unchanged from earlier passes and still the only posting blocker: **PAPER-7**, the ERGO
  denominator fix in `writing/overleaf_repo/` (`README` blocker 7), which no autoresearch agent may
  make.

---

## 7. Provenance

Read: `tasks/T30/worklog.md` (whole), `tasks/T32/worklog.md` (whole),
`tasks/T2c/{final_tables.py,paired_split.py,RESULTS.md}`, `replies/v5/{00,04,05}*.md`,
`replies/v5/{README.md,CHANGES.md}`. Executed: `python3 final_tables.py` twice (pure local
recomputation over `leak_labels_v3.jsonl`, `answer_check.jsonl`, `math_numeric_probe.json` and the
recovered phase-1 `results.json` files) — no model call of any kind.

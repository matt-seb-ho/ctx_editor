# T30 — final end-to-end coherence audit of `replies/v5/`

**Task.** Read `neurips_review/replies/v5/` as one document after eight editing passes (T15, T19,
T21, T25, T28 plus routed fixes from T20, T24, T27) and find internal inconsistency and leftover
staleness. Not a red team — the adversarial read already happened (`tasks/T23/RED_TEAM.md`). Zero
API calls; no experiments run.

**Verdict (one line): `replies/v5/` is internally coherent and ready for the operator's review,
with one open numeric conflict that the operator must resolve before posting (the MT-OSC w=4
engagement rate, judgement call J1 below) — everything else found was fixed in place.**

---

## 1. What was read

All eight files end to end: `00_general_response.md` (241 ln), `01_reviewer_iNYK.md` (97),
`02_reviewer_Vg97.md` (155), `03_reviewer_5YHP.md` (162), `04_response_to_AC.md` (75),
`05_final_remarks.md` (50), `CHANGES.md` (590), `README.md` (144). Cross-checked against
`autoresearch/WORKLOG.md` (F1–F83, D1–D22) and, where a number needed adjudication, against the
source task logs: `T1`, `T2B/RESULTS.md`, `T2c/RESULTS.md`, `T20`, `T21`, `T24`, `T27`, `T6`.

`HANDOFF.md` was not read and not edited (T29 owns it concurrently).

---

## 2. Numeric consistency — checks that PASSED

Recorded because a null result is the point of this pass. Every figure below was re-derived and
agrees in every file it appears in.

| Family | Check | Result |
|---|---|---|
| Paired matrix | +15.9 / 33-2-1; Augment +15.2 / 31-1-4; Gated +17.0 / 11-1-0; Rewrite −0.3 / 6-6-0; AO +13.3 / 31-4-1 | identical in `00`, `01`, `02`; W/L/T sum to 36 (and to 12 for the daggered rows) ✅ |
| Item-level | +15.4 [+11.5, +19.4], 350/93, n=1,668, 191 problems | identical in `00`, `01`, `02`, `04`, `05` ✅ |
| AC3 vs AO | cell-level +2.6pp on 15/17/4; item-level +2.8pp [−0.3, +5.9]; database +18.7pp (8/1) and +18.6pp [+10.7, +26.6] | consistent in `00`, `01`, `02`, `04`, `05`. **Arithmetic re-derived:** database 8/1 + math 1/7/1 + code 2/6/1 + actions 4/3/2 = 15/17/4 exactly; (18.7×9 + (−3.1−3.8−1.3)×9)/36 = +2.6; 15.9−13.3 = 2.6; 15.4−12.6 = 2.8 ✅ |
| **The p = 0.010 near-miss** | matrix-wide AC3-vs-AO item-level McNemar | appears **nowhere** in `00`–`05`; only in `README` and `CHANGES` §8 rule 6b as a guardrail. F82's near-miss stayed caught ✅ |
| tau2 | 68.4 ± 13.9 / 70.2 ± 11.0 / 78.9 ± 0.0; AO 0.0 in 9 cells / 171 rollouts; 855 rollouts; Gated −10.5pp p = 0.238; Augment 84.2 → 47.4; fork bug +2.3pp | `00` CW4 table is cell-for-cell identical to `CHANGES` §12.3 and to T6; `01` W3, `02` W2, `04` #6, `05` #8 all agree ✅ |
| tau2 claim scope | no improvement claim survives anywhere; "entire spectrum" replaced by the "viable" fallback | grepped: the strong sentence survives only in `README`/`CHANGES` as history ✅ |
| CollabLLM | MATH-Hard 91.7 ± 5.8 / 88.3 ± 2.9 / 91.7 ± 7.6; BCB 6.7 / 18.3 / 21.7 ± 5.8 | **every cell re-derived from the printed per-replicate counts** (19/19/17, 18/17/18, 20/17/18; 2/2/0, 3/3/5, 5/5/3): means and sds all reproduce; +3.3pp = 13/60 − 11/60 = 2 instances; "+15pp in 3 of 3" = 15/15/15 ✅ |
| ERGO | math 16/23 = 69.6 → 16/20 = 80.0; code ≈44.0; database 12.0; actions interval [43.5, 52.2] = 10/23–12/23; AC3-Reset 75.0 = 15/20, Gated 80.0 = 16/20 | consistent in `00` CW5, `01` W1, `02` W1, `04` #5, `05` #7; T17's 57.9 appears nowhere ✅ |
| WildChat | 87.8 ± 2.1 / 91.2 ± 2.1 (submitted 89.8 / 92.1); 22 cells = 13 vs AO + 9 vs FC; 72–92% never in the same sentence as the pooled headline; top cell 91.5 (Kimi/Rewrite, n=59) inside the envelope | consistent across `00`, `02`, `03`, `04`, `05` ✅ |
| Three-way baseline | 4.0/15.8 vs 19.0–22.4 vs 56.1/83.0; restriction 56.1 → 32.0, 83.0 → 48.0; 29.9% vs 4.0% | `00` CW5, `01` W1, `02` Q1, `04`, `05` agree ✅ |
| Condensation | 56.1 / 53.3 / 47.7 / 60.7 / 47.7 / 75.7 / 73.8 and code 83.0 / 79.0 / 80.0 / 92.0; every Δ re-derived; neutral prompt 51.4 with +24.3 / +22.4; 336+341+340 = 1,017 summaries | all internally exact ✅ |
| Latency | 578 / 587 / 781 / 835 / 1,051 / 1,214 s; per-turn ratios; 6.2 vs 2.6 calls = 0.41× | seconds-per-turn column reproduces from wall-clock ÷ (107 × turns) to the printed 2 s.f. ✅ |
| Detector / spans | 97.6% (123/126), 4.0% (5/126), 50.4% (123/244), 78.6% (99/126); natural 5/66, 0/66, 7/7, 0/4, 63.6% = 7/11 base rate; 3,357 turns = T2B; 111 × 0.6 ≈ 66 admissible | all reproduce ✅ |
| Gate | 539/554 = 97.3%, 539/547 = 98.5%, 628/659 = 95.3% | ✅ |
| Leak | code 0/106 +30.2 (32.1→62.3); database 1/147 +26.0 (22.6→48.6, n=146); pooled n = 106+146+77 = 329 | arithmetic consistent; **but see J2** ✅/⚠ |
| Counts | `04` = 6 numbered corrections (tau2 = 6, ERGO = 5); `05` = 8 (ERGO = 7, tau2 = 8); every "correction N" cross-reference in `README` and `05` resolves | ✅ after fix F1 |
| Scaffolding | `grep -rn "⚠ INTERNAL"` over `replies/v5/*.md` returns **only** `00`'s orientation preamble; no `TODO`, `[pending]`, `_(pending X)_`, `TBD`, `FIXME`, placeholder or HOLD block anywhere in the reply files | ✅ |
| `CHANGES` §7 | tally says UNVERIFIED = 1; §7 has U1 and U3 struck-through (retired), U2/U4/U5 resolved, U6 live in prose | matches ✅ |
| Tally table | 24 + 17 + 6 + 21 + 0 + 1 = 69 = printed total | ✅ (the sum was already fixed by T28; the prose beneath it was not — see F8) |

---

## 3. Fixes applied

All edits are inside `neurips_review/replies/v5/`. Nothing under `writing/overleaf_repo/` was
touched; no `git checkout`.

### F1 — `04_response_to_AC.md`: an ordinal that resolved to the wrong correction

The lead-in to the six numbered corrections used "the sixth" to mean "the remaining one", but item
6 of the list is the tau2 withdrawal, which does *not* raise a baseline. ERGO is item 5.

* **Before:** "…and **the sixth** moves against us by raising a baseline we compare against."
* **After:** "…and **the remaining one (item 5)** moves against us by raising a baseline we compare against."

### F2 — `03_reviewer_5YHP.md`: dangling "the same 32 conversations"

The natural-span study is introduced as "111 spans in **30** conversations"; the accuracy sentence
then referred to "the same **32** conversations", a number never previously mentioned. Both are
correct (T2B/RESULTS.md §"32 conversations were selected and run; 2 code conversations produced no
admissible span … the control arms and §5 use all 32"), but the reference dangled.

* **Before:** "On the same 32 conversations, raw accuracy is Baseline **39.3%**…"
* **After:** "On the 32 conversations this study ran (the 30 above, plus 2 in which no span met the ablation's admissibility check), raw accuracy is Baseline **39.3%**…"

### F3 — `00` CW5 and `04`: "the fraction … differs by four" contradicted its own sentence

The sentence prints gap-closure of **51%** (database) and **60%** (code) against **50%** on Table
1's subset, then claims the fraction "differs by four". The largest gap between those printed
numbers is **ten** (60 vs 50); the smallest is one. The "four" is real but comes from a different
quantity — T24 §5.4's *database-only* spread across three pools (47–51%) — which the reviewer-facing
sentence does not print. As written it is checkable-with-a-calculator wrong, which is the exact
failure mode this reply set is built to avoid.

* **Before (`00`):** "…**the fraction of the multi-turn gap our method closes differs by four.**"
* **After (`00`):** "…**the fraction of the multi-turn gap our method closes moves by ten points at most.**"
* **Before (`04`):** "…the fraction of the gap we close **moves four**."
* **After (`04`):** "…the fraction of the gap we close **moves by ten points at most**."
* Same wording propagated to `README` blocker 6 and `CHANGES` §11.3b, each with a note recording
  where "four" came from, so the operator can restore a tighter line by quoting the measured
  per-task envelopes (database 47–51%, code 50–60%, T24 §5.3) instead of a single figure.

**Flagged for the operator** as the one fix here that touches rhetoric: the argument is unchanged
and still strong (52 points vs ten), but the punchline is weaker than the version that shipped.

### F4 — `04`: dangling "(below)" in the baseline-reconciliation table

Row 3 was labelled "Condensation experiment (below)"; nothing about the condensation experiment
appears below that point in `04` — it is above (the additions table) and in `00` CW5.

* **Before:** `| Condensation experiment (below) | 56.1 / 83.0 | …`
* **After:** `| Condensation experiment (**Common Weakness 5**) | 56.1 / 83.0 | …`

### F5 — `README`: PAPER-7 added to the numbered blocker list

WORKLOG F73(ii) flags this precisely: the numbered list carried six blockers, five now resolved,
while **PAPER-7 — the ERGO denominator fix — is the item that actually gates posting** (WORKLOG:505,
"the rebuttal cannot go out before it") and appeared only in the "Before posting" bullets. Added as
**Blocker 7**, marked OPEN, with the values the paper must carry (math 80.0, code ≈44.0, database
12.0, actions as an interval, never T17's 57.9) and the note that it is a `writing/overleaf_repo/`
edit no autoresearch agent may make.

### F6 — `README`: stale finding/decision range in the header

"findings F1–F70, decisions D1–D14" → **"F1–F81, D1–D21"**. The document's own body already cites
F73–F77 and D20; F78–F81 (T6) and D21 are what T28 applied.

### F7 — `README`: "a single list in `04` and `05`" implied identical lists

`04` carries six corrections, `05` eight. Reworded to say so, and to name what `04` omits (memory
noise floor, BigCodeBench scoring — both made in the body of `03` W4/W6, so nothing is lost).

### F8 — `CHANGES.md`: four stale statements that contradicted the document's own tally

1. **Header:** "findings F1–F49, decisions D1–D11" → **F1–F81 / D1–D21**.
2. **Revision history:** "**The T6 (tau2) holds are untouched and remain live.**" — false since T28.
   Rewritten to "were untouched and still live *at that point* — discharged later, by T28; see §12.3".
3. **Tally prose:** "Of the **15** corrections, 7 move against us … and 5 are wording-only" survived
   T25's 15→16 and T28's 16→17. Rewritten to **17 / 8 against us / 3 in our favour / remainder
   wording-only**, naming the two later additions (the T2B selectivity retraction and the tau2
   withdrawal). *The exact split of the 17 into against/favour/wording is partly inherited — the
   two increments were recorded in prose without a row-level attribution — so the new sentence
   enumerates the against-us items explicitly and leaves the remainder unenumerated rather than
   inventing a breakdown.*
4. **Rows still labelled HOLD** while the tally reads "On HOLD | **0**": rows **2.4**, **3.2**,
   **4.4**, **5.4**, **5.10** and the `05` section header/T19 note. Each updated to
   "HOLD → resolved (T28)" with what actually happened. Two were more than a label:
   * **5.4** said the tau2 row was "removed from the table pending T6" — `04`'s additions table now
     *has* a tau2 row (the "Against us" re-run row). Corrected.
   * **4.4** said "drops 'AC3 beats full context on all three' **pending T6**" — T6 refuted it, so
     the drop is permanent, not pending. Corrected.
5. **Row 5.6** described the corrections list as "4 items posted, 2 more in `05`" (T15's state).
   Updated to the current 6 / 8 with the history retained.

---

## 4. Judgement calls left for the operator

These are **not** fixed. Each is a conflict where picking a side means asserting something about
what we measured or what we claim.

### J1 — ⚠ **The MT-OSC w=4 engagement rate is quoted as two different numbers, twice in the same paragraph.** (highest priority; reviewer-facing)

`00` CW5 and `02` Q1 both say, within three sentences:

> "…it fired **30 times across 107 conversations, 0.3 times per conversation**…"
> "…**5.7 compaction events per conversation against 0.6 at w = 4**, a nine-fold increase…"

Both numbers describe the **same published w=4 run**. They come from different counters:

| Source | Counter | w=4 | w=2 |
|---|---|---|---|
| `tasks/T1/worklog.md:354, :577` | condenser **calls** | 30 calls / 107 conv = **0.28** | (no valid run) |
| `tasks/T27/worklog.md:448` | MT-OSC **log events / conversation** | **0.62** | **5.67** |

The "nine-fold increase" is only true against 0.62 (5.67/0.62 = 9.1). Against 0.3 it is a
nineteen-fold increase. `04`'s additions table and `05`'s condensation bullet quote **0.3 *and*
"nine times more often"** together, which is the same contradiction with the reconciling number
removed.

I did not reconcile these because doing so asserts which counter is the engagement rate — a claim
about our own instrumentation that I cannot settle without re-reading the MT-OSC run logs, and
possibly not without a re-run. **Options:**

* **(a) Standardise on T27's counter (0.6 → 5.7, "nine-fold").** Delete "30 times across 107
  conversations, 0.3 times per conversation" from `00` and `02`, and change `04`/`05` to 0.6.
  Cheapest, keeps the nine-fold claim, but drops the concrete "30 times" that reads well.
* **(b) Standardise on T1's counter (0.3 → 5.7, "nineteen-fold").** Requires confirming that
  T27's 5.67 is measured on the same counter as T1's 30, which is exactly the unverified step.
* **(c) Print both, labelled** — "0.3 compaction calls and 0.6 logged compaction events per
  conversation at w=4, against 5.7 events at w=2". Honest, and awkward in a rebuttal.

A reviewer who reads CW5 carefully will see the conflict; this is the one item in the set I would
not post without resolving.

### J2 — The math leak rate and the math no-leak `n` do not reconcile in `03` W1's table

The table prints, for math, leak rate **38% (54/144)** and a no-leak subset of **n = 77**.
144 − 54 = 90, not 77. Both figures are correctly transcribed from `T2c/RESULTS.md` — but from
**two different leak labels**: Table 1's "answer verified correct" gives 54, while the split in
Table 2 uses a broader label (verified-correct ∪ the model-free numeric probe) with LEAK = 67, and
144 − 67 = 77. The pooled cell has the same issue: it reads "**11% overall**", which is the strict
rate over **all four tasks** (58/547); over the three pooled tasks it is 55/397 = 14% strict, or
68/397 = 17% under the label the split actually uses.

Nothing here is wrong, but the printed column and the printed `n` cannot both be derived from the
same definition, and a reviewer checking the table will notice. **Options:** (a) print the split's
own label for math (**47%, 67/144**) and relabel the column; (b) keep 54/144 and footnote that the
split uses the union label; (c) change the pooled cell to "14% over these three tasks" or "11%
across all four tasks", whichever matches the label chosen in (a)/(b). Fixing this means choosing
which leak definition we stand behind, so I left it.

### J3 — `README`'s "seven of our own numbers moved, six of them against us … and an eighth"

This reconciles with `05`'s list of eight (seven ours + ERGO), but the ordinal "eighth" refers to
ERGO, which is item **7** in `05` and item **5** in `04`. It is internal-only and the counts are
right, so I left the sentence alone; if the operator wants it airtight, replace "an eighth
correction" with "the ERGO correction".

### J4 — `CHANGES` tally: the against/favour/wording split of the 17 corrections

See F8.3. The T25 increment (15 → 16) was never attributed to a row, so the new breakdown
enumerates the eight against-us items and leaves the remainder unenumerated. If the operator wants
the full split, it needs one pass over the rows with a status column, not an inference.

---

## 5. Tone and register — flagged, not rewritten

Eight passes, and it mostly reads as one voice: concession-first paragraphs, "we would rather say
this than have it found", numbers before adjectives. Three places where the register moves:

1. **Bolded self-narrating lead-ins cluster in the T25/T28 layers.** "**We should be precise about
   the blast radius…**", "**So we ran the obvious follow-up to our own scoping argument rather than
   leave it to be asked.**", "**Nor is the unselected pool an easy setting**, which is the
   reservation this experiment has to survive." These are effective individually; three in one
   section (`00` CW5) starts to sound like a document arguing with an imagined critic rather than
   answering a reviewer. `00` CW2 and CW5 carry most of them.
2. **"…rather than leave it distributed across six documents" (`04`) and "…than leave a reader to
   do it from six documents" (`00` CW2)** leak our own file structure into reviewer-facing text.
   No reviewer sees six documents; they see a thread.
3. **`03` W5 is markedly longer and more technical than the other answers** (design → three results
   → retraction → "what this does not withdraw" → eight limits). It is the best section in the set,
   and it is also the one a tired reviewer is most likely to skim past the retraction in. Consider
   a two-sentence summary at its head. No change made.

---

## 6. Provenance

Sources consulted for adjudication: `autoresearch/WORKLOG.md` F68–F83, D20–D22;
`tasks/T1/worklog.md` §8.2, §"Is MT-OSC reportable"; `tasks/T2B/RESULTS.md` §§1, 3, 8;
`tasks/T2c/RESULTS.md` Tables 1–2; `tasks/T20/worklog.md` §§U2–U5; `tasks/T21/worklog.md`;
`tasks/T24/worklog.md` §§5.3–5.4, §7; `tasks/T27/worklog.md` §§4, 7.1–7.3; `tasks/T6/worklog.md`
(via WORKLOG F78–F81). Zero API calls, no experiments, no runs.

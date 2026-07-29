# T32 — resolving T30's two factual open items (J1, J2) in `replies/v5/`

**2026-07-29, autonomous overnight session.** Operator asleep; no questions asked.

**Task.** T30's end-to-end coherence audit (`tasks/T30/worklog.md` §4) left four open items. J3/J4
are internal wording and bookkeeping. J1 and J2 are factual questions with determinate answers, so
they get settled from evidence rather than handed to the operator as a menu of options.

**Verdict (one line): both resolved from code and run artifacts. J1 — the engagement rate is
condenser calls (0.3 at w=4, 2.2 at w=2), the composite "log events" counter was never an
engagement rate, and the ratio is ~8×, not nine-fold. J2 — the leak table's subsets were always cut
on the union label, so the printed rates were the ones that had to move: math 38% → 47%, pooled
11% → 17%; no headline number changes.**

**Cost: zero API calls, zero experiments, zero rollouts.** Everything came from reading
`src/ctx_editor/strategies/mtosc.py`, `tasks/T2c/final_tables.py`, and recounting two artifact sets
already on disk. No `git checkout`. `writing/overleaf_repo/` not read and not touched (T31 owns it).

---

## 1. J1 — what does "MT-OSC engaged" mean operationally?

### 1.1 The conflict as T30 found it

`00` CW5 and `02` Q1 each printed, within three sentences, MT-OSC's w=4 engagement as **0.3 per
conversation** (T1's counter) and **0.6 per conversation** (T27's counter). Compounding it, the
"nine-fold" w=2/w=4 ratio reconciles only against 0.6, while `04` and `05` printed 0.3 *together
with* "nine times more often". Every arrangement of those sentences contained at least one false
statement.

### 1.2 The code that settles it

`src/ctx_editor/strategies/mtosc.py` emits **three structurally different log records**, and they
do not stand in 1:1 correspondence with anything:

| record | emitted at | line | fires when |
|---|---|---|---|
| `mtosc_decider` | every scheduled trigger turn | `mtosc.py:336` | the schedule reaches `T_j = (w−1)j + 2` **and** at least one pair exists — logged whether or not condensation follows |
| `mtosc_condensation` | after a successful condenser call | `mtosc.py:345` | the Decider did **not** withhold *and* the condenser returned parseable JSON (`_condense` returns `None` on unparseable output, `:281–283`) |
| `mtosc_applied` | when a pending condensation is spliced in | `mtosc.py:327` | a condensation computed at turn `T_j` is used at `T_j + 1` — i.e. **only if the conversation reaches another turn** |

So the answer to the brief's question is explicit in the code. A `mtosc_decider` record is *a check
that may decline* — it is logged before the withhold test at `:334–337`. A `mtosc_condensation`
record is *a condensation actually performed*. And a single condensation emits up to **three**
records across two turns. Summing them is not a rate of anything a reader would name.

T27's table (`tasks/T27/worklog.md:446–450`) is explicitly headed **"MT-OSC log events /
conversation"** and sits under the heading *"Positive control that the fix is live and the schedule
engages"*. It was doing its job correctly — demonstrating that the post-`c1dd523` w=2 cell was no
longer silently dropping pairs (`raw_pairs_carried` 133 vs the archived buggy run's 0). It was
never proposed as a reviewer-facing engagement statistic; it migrated into one.

T1's counter (`tasks/T1/worklog.md:354`, restated at `:577`) counted condenser calls: "MT-OSC w=4
fired only 30 times across 107 conversations (0.3 calls/conv)".

### 1.3 Recount from the artifacts

Counted directly over `outputs/T1/main/db_mtosc_w4/traces/database/mtosc_w4/*.json` and
`outputs/T27/db_mtosc_w2/traces/database/mtosc_w2/*.json` (107 trace files each; records live at
`trace.logs`, not the top level):

| counter | w=4 | per conv | w=2 | per conv | w2/w4 |
|---|---|---|---|---|---|
| `mtosc_decider` | 30 | 0.280 | 237 | 2.215 | 7.90× |
| **`mtosc_condensation`** | **30** | **0.280** | **237** | **2.215** | **7.90×** |
| `mtosc_applied` | 6 | 0.056 | 133 | 1.243 | 22.2× |
| all `mtosc_*` (T27's composite) | 66 | 0.617 | 607 | 5.673 | 9.20× |
| Decider **withheld** | 0 | — | 0 | — | — |
| Σ `raw_pairs_carried` | 6 | — | 133 | — | — |

Three cross-checks that this reproduces the sources rather than a new measurement:
`mtosc_condensation` = 30 reproduces T1's 30 exactly; the composite 0.617 / 5.673 round to T27's
printed 0.62 / 5.67 exactly; and Σ`raw_pairs_carried` = 6 / 133 reproduces T27's positive-control
column.

### 1.4 Why decider and condensation counts are identical

0 withholds in both runs, so every scheduled trigger produced a condensation. This is not luck —
`mtosc.py`'s module docstring (¶ "NOT FULLY DETERMINED BY THE PAPER", item 1) predicts it: the
Decider requires `user_tokens > tau` with τ = 1000, and `_decider` (`:213`) counts whitespace tokens
over LiC's short sharded user messages, which never approach 1000. The docstring says the polarity
ambiguity "is inert on LiC … That is measured and logged per run, not assumed." It is, and it is:
0/30 and 0/237.

**Consequence for the resolution:** the decider-vs-condensation distinction that could in principle
have separated "a check that declines" from "a condensation performed" is empirically vacuous here.
The composite counter's 9.2× is therefore driven entirely by the *third* record type — the
`mtosc_applied`/`decider` mix differing between windows — which is precisely why it is not a rate.

### 1.5 Decision

**Adopted: `mtosc_condensation` — condensations actually performed — as the engagement rate.**
It is what a reader assumes "fires per conversation" means, it is the counter T1 published, and it
is the counter that makes "fired **30 times** across 107 conversations" a true sentence with a
concrete integer in it.

**Ratio recomputed on the adopted counter: 237 / 30 = 7.90×, i.e. roughly eightfold.** "Nine-fold"
is retired. It was never eight-vs-nine rounding — 9.2× is a different quantity computed on a
composite of three log types.

The composite counter is **not** stated in a parenthetical in the reviewer-facing text, contrary to
the brief's fallback provision, because it is not a defensible alternative definition — it is a sum
over heterogeneous record types with no interpretation. It is instead documented as a
do-not-quote in `README` and in `CHANGES` §13.1 so it cannot migrate back.

### 1.6 One fact added, not merely corrected

Only **6 of the 30** w=4 condensations were ever applied to a context (`mtosc_applied` = 6). The
mechanism is in the code: the paper's one-turn lag (`mtosc.py:300–310`, faithful to Appendix B.3)
means `C_j` computed at turn `T_j` is usable only from `T_j + 1`, and at w=4 the first trigger is
turn 5 — so a conversation must reach turn 6 for any condensation to take effect, while LiC
conversations average 4.1 turns. Added to `00` CW5 because it is measured and it is exactly the
paragraph's point.

**0.3 is kept as the headline rather than 0.06** because 0.3 is the *conservative* choice: a higher
engagement figure is the one least favourable to our own "it is nearly a no-op" argument. Quoting
0.06 as the headline would be arguing our case with the weakest defensible number.

### 1.7 Before/after

| file | before | after |
|---|---|---|
| `00` ¶4 | "engages nine times more often" | "engages roughly eight times as often" |
| `00` CW5 | "fired **30 times across 107 conversations, 0.3 times per conversation**" | "…, **0.3 condensations per conversation**" + "only **6 of those 30 condensations were ever applied** to a context before the conversation ended" |
| `00` CW5 | "**5.7 compaction events per conversation against 0.6 at w = 4**, a nine-fold increase" | "**2.2 condensations per conversation against 0.3 at w = 4**, roughly an eightfold increase (237 condensations against 30, over the same 107 conversations)" |
| `02` Q1 | "0.3 per conversation" … "(**5.7 compaction events per conversation against 0.6 at w = 4**)" | "0.3 condensations per conversation" … "(**2.2 condensations per conversation against 0.3 at w = 4**, roughly eightfold)" |
| `04` additions table | "engage **nine times more often**" | "engage **roughly eight times as often** (2.2 condensations per conversation against 0.3)" |
| `05` condensation bullet | "engage **nine times more often and score worse**" | "engage **roughly eight times as often (2.2 condensations per conversation against 0.3) and score worse**" |
| `README` ¶T28 | "engages 9× more and scores worse (M12)" | "engages ~8× more … (M12; the ratio was 9× until T32 corrected the counter)" |
| `README` guidance | "engages 9× more (5.7 events/conversation vs 0.6)" | "engages ~8× more (**2.2 condensations/conversation vs 0.3**; 237 vs 30 …)" + explicit do-not-quote for the retired figures |
| `CHANGES` §12 M12 | "engages **9× more** — 5.7 compaction events per conversation against 0.6" | "engages **~8× more** — 2.2 condensations per conversation against 0.3 (237 vs 30 …)" |

Verified clean: `grep -rn "nine-fold\|nine times\|9×\|5\.7 event\|0\.6 at w\|compaction event" replies/v5/*.md`
returns only the intentional do-not-quote note and the intentional historical note.

---

## 2. J2 — which leak label produced which figure

### 2.1 The conflict

`03` W1 printed math leak **38% (54/144)** beside a no-leak subset **n = 77**. 144 − 54 = 90 ≠ 77.
The pooled cell read **"11% overall"** — a rate over all four tasks — inside a row covering three.

### 2.2 The code that settles it

`tasks/T2c/final_tables.py` builds **two** labels per record:

```
:37   r["leak_final"] = "LEAK" if (verdict == "CORRECT_ANSWER_STATED" or pderived) else "NO_LEAK"
:38   r["leak_judge"] = "NO_LEAK" if r["label"] == "NO_LEAK" else "LEAK"
```

`leak_final` is a **union** of the answer-verification pass and the math-only model-free numeric
probe — the module docstring states this outright: *"A record is LEAK if either fires. This is
deliberately a union (high recall for leakage), so the NO_LEAK stratum is a conservative,
high-precision set."*

Then:

* `:64` — Table 1's rate column counts `answer_verdict == "CORRECT_ANSWER_STATED"` **only**. This
  is where 54/144 and 58/547 (11%) come from.
* `:116` — `table_paired("leak_final", …)` passes the **union** to every split. This is where
  n = 77 and n = 329 come from.

So the two printed quantities came from two different partitions, exactly as T30 suspected. Note
also that `:116`'s caption calls `leak_final` *"strict: analyzer output verified to contain the
correct answer"*, which describes only the **first arm** of the union — a mislabel inside T2c's own
`RESULTS.md` that is the proximate cause of the whole confusion, and worth recording.

### 2.3 The headline check the brief asked for

**Is the strict (verification-only) label the one backing the +20.7 pp headline? No.** The
+20.7 pp / n=329 row is emitted by `table_paired("leak_final", …)` at `:116`, so the **union** label
is the one backing the headline. Confirmed arithmetically below: the union's NO_LEAK stratum over
math+code+database is exactly 329.

### 2.4 Recount from `leak_labels_final.jsonl`

Arm `context_edit_v2_no_gate` (`…_accumulate` for actions), matching `final_tables.py`:

| task | n | judge LEAK | verification-only LEAK | **union LEAK** | **union NO_LEAK** |
|---|---|---|---|---|---|
| math | 144 | 110 | 54 (38%) | **67 (47%)** | **77** |
| code | 106 | 33 | 0 | **0 (0%)** | **106** |
| database | 147 | 25 | 1 | **1 (1%)** | **146** |
| actions | 150 | 14 | 3 | **3 (2%)** | **147** |
| **math+code+database** | **397** | 168 | 55 (14%) | **68 (17%)** | **329** |
| all four | 547 | 182 | 58 (11%) | 71 (13%) | 476 |

Everything reconciles under the union: 144 − 67 = **77** ✓, 397 − 68 = **329** ✓,
77 + 106 + 146 = **329** ✓, 67 + 0 + 1 = **68** ✓. Code, database and actions are identical under
both labels because the numeric probe is math-only — which is why only the math row and the pooled
row move.

### 2.5 Decision

**Use `leak_final` (the union) throughout, as T2c itself designates it primary.** The verification
detector alone and the probe alone are reported once, as reference values, explicitly not used to
cut subsets. The judge label stays exactly where it already was in `03` — a robustness note
(no-leak gain +24.5 vs leak +17.3, so both definitions agree in direction).

**Direction: against us.** Math's admitted leak rate rises 38% → 47% and the pooled rate 11% → 17%.
**No headline number moves**: +30.2 (code), +26.0 (database), +20.7 [+14.8, +25.3] (pooled), −2.6
(math), +19.6 (Gated-Reset on 311) and every printed `n` were already computed on this label.

### 2.6 Before/after

| file | before | after |
|---|---|---|
| `03` W1 lead-in | "checked … whether the analyzer's text contains the **verified correct answer**" | states the union of the two detectors explicitly, and why the no-leak stratum is conservative |
| `03` W1 column head | "Leak rate (analyzer output verified to contain the correct answer)" | "Leak rate (either detector fires)" |
| `03` W1 math row | "**38%** (54/144)" | "**47%** (67/144)" |
| `03` W1 pooled row | "11% overall" | "17% (68/397)" |
| `03` W1 (new sentence) | — | reconciliation note (144 − 67 = 77) + single-detector reference rates (verification 38% math / 14% pooled; probe 40% math) |
| `04` #13 | "where the analyzer verifiably never states the correct answer" | "…verifiably neither states the correct answer nor reveals the gold value" |
| `05` mechanism bullet | "how often the analyzer's own output contains the verified correct answer" | "…hands over the answer — under a high-recall union of an answer-verification pass and a model-free numeric probe" |
| `CHANGES` row 4.2 | "math 38%" | "**math 47%**, pooled 17%", with the correction and its cause recorded |

### 2.7 Knock-on correction found while verifying (not in T30's list)

`03`'s caveat sentence read: *"On math we validated the detector by hand — the precision of the
no-leak label is 29/32…"*. `tasks/T2c/worklog.md:238–251` shows that adjudication was drawn from
records the **v3 LLM judge** labelled `NO_LEAK` (round 3, 24 records at seed 555, pooled with 8 from
round 2), **not** from the `leak_final` stratum the table uses. The two strata are not nested — the
judge calls 34 math records NO_LEAK where the union calls 77 — so 91% precision measured on the
judge's set does not transfer to the union's set, and quoting it as validation of "the no-leak
label" was optimistic in our own favour.

Reworded to attribute it to the judge label and to state what it actually supports: all three errors
were on math, against 24/24 correct elsewhere, which is *why* the primary label adds the model-free
probe rather than trusting a judge.

**Deliberately not asserted:** that the numeric probe catches the two specific hand-validation
misses. Checked — `math_numeric_probe.json` has `derived` = False for `sharded-GSM8K/117` at
`conv=0` and True at `conv=1`/`conv=2`, and the mirror pattern for `GSM8K/420`. The probe catches
them in some conversation prefixes and not others, so the tidy narrative "the probe fixes exactly
those two" is not true and is not written.

---

## 3. What I could not settle

* **J3 and J4 remain open**, as scoped. Both are internal-only: J3 is `README`'s "an eighth
  correction" ordinal (the counts are right; only the ordinal dangles), J4 is the against/favour/
  wording split of the 17 corrections, which needs a row-level status pass rather than an inference.
* **T2c's `RESULTS.md` Table 2 caption is wrong** (it labels the union split "strict: analyzer
  output verified to contain the correct answer"). I did not edit `tasks/T2c/RESULTS.md` — it is a
  completed task's output artifact and rewriting a prior task's results file to match a later
  reading is the kind of edit that should be visible, not silent. It is recorded here and in
  `CHANGES` §13.2. Anyone regenerating that file from `final_tables.py:116` will reproduce the same
  caption, so the fix belongs in the script, not the output.
* **Whether the `mtosc_applied` count should become the headline engagement rate** is a
  presentational judgement I resolved conservatively (keep 0.3, state the 6-of-30 alongside). An
  operator who wants the strongest honest version of the "no-op" argument could lead with 0.06; I
  did not, because leading with the number most favourable to us is the failure mode this reply set
  exists to avoid.

---

## 4. Provenance

Code read: `src/ctx_editor/strategies/mtosc.py` (whole file),
`src/ctx_editor/config/experiment/mtosc_w{2,4}.yaml`, `tasks/T2c/final_tables.py`,
`tasks/T2c/paired_split.py`. Artifacts recounted:
`outputs/T1/main/db_mtosc_w4/traces/database/mtosc_w4/` (107 files),
`outputs/T27/db_mtosc_w2/traces/database/mtosc_w2/` (107 files),
`tasks/T2c/leak_labels_final.jsonl`, `tasks/T2c/math_numeric_probe.json`. Worklogs consulted:
`tasks/T30/worklog.md` §4, `tasks/T1/worklog.md` §8.2 and §"Is MT-OSC reportable",
`tasks/T27/worklog.md` §7.2 and §8, `tasks/T2c/worklog.md` §§ round-3 / D6 / limits,
`tasks/T2c/RESULTS.md` Tables 1–2.

Files modified: `replies/v5/{00,02,03,04,05}*.md`, `replies/v5/README.md`,
`replies/v5/CHANGES.md` (rows 4.2 and M12, revision history, new §13). Nothing outside
`replies/v5/` and this worklog was written.

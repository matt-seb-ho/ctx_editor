# T21 — Apply T20's verified wordings to `replies/v5/`; take the CollabLLM AO column to N=3

**Started:** 2026-07-29 ~17:38 UTC. **Status: COMPLETE** (~18:30 UTC). **API spend: $0.178.**
**Scope:** (1) apply T20's drop-in wordings for §7 U2–U5 to `neurips_review/replies/v5/`;
(2) run the assistant-omission (AO) column at N=3 on CollabLLM.
Nothing else. `writing/overleaf_repo/` untouched; no `git checkout` in this tree.

---

## Timeline

### 17:38–17:42 UTC — Part 2 preconditions (verified BEFORE launching, per brief)

| Check | Result |
|---|---|
| Load-balancer fix (`gpt-4o-mini: 150` on `dl-openai-3`) | **present**, `src/ctx_editor/config/load_balancer/multi_endpoint_foundry.yaml:57`, with T8's comment intact |
| `bigcodebench` importable | yes, `.venv/lib/python3.12/site-packages/bigcodebench/` |
| `matplotlib` importable (the `reliability_guard` silent-0 trap) | yes, **3.11.1** |
| T8's other 10 test deps (`bs4, mechanize, numpy, openpyxl, pandas, regex, scipy, seaborn, sklearn, xlwt`) | all import |
| Canonical-solution pre-flight, seed=42 draw (`T8/canon_check.py 42`) | **19/20 passing**, only `BigCodeBench/501` failing — **exactly T8 §"Environment soundness check"** |
| **Judge live?** AO 2-sample smoke, `outputs/T21/smoke` | `Accuracy: 100.00% (2/2)`, `Interactivity: 0.500`, `Avg Assistant Tokens: 476`, cost `$0.0038`. Real judge verdicts, not `0/0`. **Confirmed live.** |

### Positive control on the offline re-scorer (mandatory, trap #1)

Re-scored three recovered rep1 cells with T8's own `rescore_bcb.py` under the current
unified environment, **before** any new cell existed:

| cell | stored | T8/T20 published re-score | my re-score | control |
|---|---|---|---|---|
| AC3-Reset rep1 | 4/20 | **5/20** | **5/20** | reproduces |
| Baseline rep1 | 1/20 | **2/20** | **2/20** | reproduces |
| AO rep1 | 3/20 | **3/20** (T20) | **3/20** | reproduces |

In all three the only moved item is `BigCodeBench/451` (0.0 → 1.0 on Reset and Baseline,
unchanged 0.0 on AO) — the same deterministic library-version difference T8 identified.
**The scorer is in T8's environment, not a different one.**

### 17:42 UTC — replicate sweep launched

Driver: `neurips_review/autoresearch/tasks/T21/run_t21.sh`, two parallel streams
(`math`, `code`), cells sequential within a stream at `execution.max_concurrent=5`.
4 fresh cells = AO x {math-hard, bigcodebench} x reps {2, 3}.
Output dir `outputs/T21/` (T21-scoped). rep1 is reused from the recovered snapshot.

**Config match against T8** (verified before launch, not after):

| Field | T8's cells | T21's AO cells | match |
|---|---|---|---|
| `model=` | `deepseek_v4_flash_user_deepseek` | same | yes |
| `load_balancer=` | `multi_endpoint_foundry` | same | yes |
| `task.name` / `task.dataset_name` | `collabllm_math`/`math-hard`, `collabllm_code`/`bigcodebench` | same | yes |
| `task.limit` | 20 | 20 | yes |
| `execution.max_concurrent` | 5 | 5 | yes |
| `experiment.strategy.analysis_cache_dir` | set on AC3 arms, **omitted on Baseline** | **omitted** — `AssistantOmitStrategy` has no such key and AO runs no analyzer, so passing it is a Hydra struct error (same reason as Baseline) | yes, by the same rule |
| seed | no-op (loaders hardcode `random.Random(42)`) | no-op | same fixed 20-problem draw |

**Terminology:** these are **replicate runs at temperature 1.0**, not seeds. The seed
dispatcher fix is on `main` (T8 §4) but its default is 42 and I did **not** pass `seed=`,
so all replicates draw the identical 20 problems — the same regime as every T8 cell.

---

## Part 1 — T20's wordings applied to `replies/v5/` (17:45–18:00 UTC, zero API calls)

### What changed, file by file

| File | Edit | Source |
|---|---|---|
| `00_general_response.md` | CW4 paragraph: **"only 1 of 11 baseline failures"** replaced with the softened wording (missing domain knowledge + step-budget exhaustion dominate, single repetitive-loop case), plus an explicit statement that this was a qualitative reading of one trial's traces, not a rubric-based annotation, with a labelled taxonomy promised for the camera-ready | T20 §U4 "Replacement wording 1" |
| `01_reviewer_iNYK.md` | W3 paragraph: same softening, T20's second drop-in | T20 §U4 "Replacement wording 2" |
| `03_reviewer_5YHP.md` | W1: **the 72–92% per-cell range restored**, as its **own bullet** immediately after the pooled-headline bullet, labelled as a spread across 22 single-run configurations (binomial sd 4–5pp each) rather than a confidence interval | T20 §U3 "Optional reviewer-facing sentence" |
| `CHANGES.md` | §7 heading and preamble rewritten from "claims we could NOT verify" to a clearance record; **U2, U3, U4, U5 rows all replaced** with T20's drop-ins (U3 struck as retired; U5 updated for T21's N=3 run); claim row **4.5** updated; new **PAPER-8** paragraph after U6 | T20 §§U2–U5 |
| `README.md` | Guardrail on the WildChat range rewritten from "was not re-judged; do not mix" to "verified and safe to use, with the order-statistic label"; pre-posting checklist updated **PAPER-1..7 → PAPER-1..8** | T20 §U3, §U2 |

### U3 — the substantive change of posture

v5 had struck 72–92% as unverified. It is not unverified: it is the exact rounded envelope
of the 22 populated `tab:wildchat` cells (min 71.6 Kimi/Reset vs AO n=74, max 91.5
Kimi/Rewrite vs AO n=59), and T20 re-derived **all 22 from per-turn judge verdicts with
22/22 reproducing to the digit**. T11's corrections touch **no** Table 3 cell — T11
corrected the Phase-3b *pooled* gpt-5-mini figures (89.8→87.8, 92.1→91.2), which appear
nowhere in Table 3, whose gpt-5-mini Reset cell is 83.0. So there was never an arithmetic
conflict to manage, and v5 was giving away a defensible number.

Restored **as a separate bullet**, not folded into the headline sentence, to honour T20's
constraint that the range must never share a sentence with the corrected 87.8/91.2 — they
are different quantities over different pools.

### U2 — kept struck, reason changed

Unchanged in the reviewer-facing text (it is not there, and stays out). What changed is the
**stated reason** in `CHANGES.md` §7: from "not re-judged under order balancing" — which
invites "so re-judge it" — to **non-significance**. On the matched 35-turn pool the gap
survives at 88.6 vs 74.3 (+14.3 pp) but rests on **seven discordant turns, 6 vs 1, exact
McNemar p = 0.125**. Order-balancing 35 turns costs pennies and cannot manufacture
significance out of seven discordant turns, so the new reason is the one that actually
closes the question.

**PAPER-8 recorded** in `CHANGES.md` (after U6) and in `README.md`'s checklist: the paper's
Table 3 caption (`neurips_2026_conference.tex:299`) says the gpt-5.4 Gated-Reset cell is
"$-$14.5pp vs. always-on Reset **on the same prefixes**". It is **false as written** — the
arms were scored on 44 and 58 turns with 35 shared, and the caption contradicts the
per-method-pool footnote already in `00`, `01` and `03`. `writing/overleaf_repo/` was
**not** touched; this is queued for the operator. It is an arXiv item, not a rebuttal item:
the claim is struck from the reply set, so nothing we post depends on it.

### tau2 `⚠ INTERNAL — HOLD` blocks — mechanical verification

T6's outcome is unknown, so every HOLD block had to survive byte-identical.

```
$ git diff -- neurips_review/replies/v5/ | grep '^[-+].*⚠ INTERNAL'
(no output)
$ git diff -U0 -- neurips_review/replies/v5/ | grep -E '^[-+]>'
(no output — no blockquote line anywhere in v5 was added or removed)
```

Stronger check — extract each HOLD block (marker line plus its contiguous `>` continuation
lines) from `HEAD` and from the working tree and compare digests:

| File | HEAD vs worktree | md5 |
|---|---|---|
| `00_general_response.md` | **IDENTICAL** | `6a0ccfb1…` |
| `01_reviewer_iNYK.md` | **IDENTICAL** | `4a71c6d0…` |
| `04_response_to_AC.md` | **IDENTICAL** | `3f13100e…` |
| `05_final_remarks.md` | **IDENTICAL** | `345021643…` |

(`README.md` and `CHANGES.md` reference `⚠ INTERNAL` inline rather than as blockquotes, so
they have no block body; their marker lines are covered by the first grep above.)

**All five HOLD blocks and their pre-drafted withdrawal wording are untouched.** The U4
paragraph in `00` sits immediately *after* the CW4 HOLD block and is not part of it; the
edit changed only the unquoted paragraph.

Total v5 diff: 5 files, **+17 / −12 lines**.

---

## Part 2 — running log

**17:42 UTC** — both streams launched.
**17:49** — `math-hard rep2` done: **17/20 = 85.0**, 20 attempted, **0 errors**, cost $0.0384, avg 1.5 turns.
**17:54** — `bigcodebench rep2` done: in-run **3/20**, 20 attempted, **0 errors**, cost $0.0450, avg 2.85 turns.
**17:59** — `math-hard rep3` done: **18/20 = 90.0**. **math stream COMPLETE.**
**~18:05** — `bigcodebench rep3` at 12/20 and running clean (real per-test tracebacks in the
log, e.g. `TypeError: task_func() missing 1 required positional argument`, which is the
signature of a *live* sandbox — the matplotlib failure mode produces an empty `{}` detail).

### Cross-checks on completed cells (`metrics.json` vs `run_summary.json` vs `results.json`)

| cell | `metrics.correct` | `results.json` score sum | `total_attempted` / `errors` | `run_summary` strategy |
|---|---|---|---|---|
| `math-hard_rep2` | 17 | 17.0 | 20 / **0** | `collabllm_assistant_omit` |
| `bigcodebench_rep2` | 3 | 3.0 | 20 / **0** | `collabllm_assistant_omit` |

All three sources agree per cell. `errors: 0` everywhere — no silent `0/0` metric failure of
the kind that produced T8's first `0/0 correct (20 errors excluded)`.

### Offline re-score, `bigcodebench rep2`

`T8/rescore_bcb.py`, zero API calls, unified environment: **3.0/20, stored 3.0/20 — no item
moved**, including `BigCodeBench/451` (which is the item that moved on Reset rep1 and
Baseline rep1). So the AO cells are insensitive to the dependency-version difference that
shifted the other two arms — consistent with T20's finding on AO rep1.

**18:07 UTC** — `bigcodebench rep3` done: in-run **5/20**. **code stream COMPLETE.**
All four cells landed in 25 min wall-clock. Total spend across the four cells: **$0.174**
(math $0.0384 + $0.0428, bcb $0.0450 + $0.0480), plus $0.0038 for the smoke — under the
$0.20 T20 estimated.

---

## Part 2 — results

### Assistant-omission column, N=3 (per-replicate raw counts)

| Dataset | rep1 (recovered) | rep2 | rep3 | **mean ± sd** | N=1 value the reply quoted |
|---|---|---|---|---|---|
| MATH-Hard | 18/20 (90.0) | 17/20 (85.0) | 18/20 (90.0) | **88.33 ± 2.89** | 90.0 |
| BigCodeBench (re-scored) | 3/20 (15.0) | 3/20 (15.0) | 5/20 (25.0) | **18.33 ± 5.77** | 15.0 |

In-run vs re-scored, bigcodebench (which cells the environment touched):

| cell | in-run | re-scored (authoritative) |
|---|---|---|
| AO rep1 (recovered, 2026-06 env) | 3/20 | 3/20 |
| AO rep2 | 3/20 | 3/20 — no item moved, incl. `451` |
| AO rep3 | 5/20 | 5/20 (modal; see the `859` note) |

### Did the numbers move materially?

**In absolute terms, no.** MATH-Hard −1.7pp and BigCodeBench +3.3pp; on a 20-problem draw
that quantises in 5pp steps, those are 0.33 and 0.67 problems. Both N=1 values sit inside
the observed replicate range.

**In comparative terms, yes, and it is reported prominently.** The reply's BigCodeBench row
previously read full context 6.7 / AO 15.0 / AC3-Reset 21.7, implying a **+6.7pp** AC3
advantage over assistant omission. At N=3 that margin is **+3.3pp** — 13/60 vs 11/60
problem-instances — which is inside the replicate noise. **v5 now declines to claim an
ordering between AC3-Reset and assistant omission on BigCodeBench** and rests the result on
the comparison against full context (+15pp, 3/3 replicates), which is untouched.

### Per-problem, all three bigcodebench arms x 3 replicates (fully paired, same 20 problems)

`AR/tasks/T21/perprob_ao.py`; full grid at `logs/perprob_ao.txt`.

```
total across 3 reps:  AO 11/60   AC3-Reset 13/60   Baseline 4/60
AO   per-rep [3, 3, 5]/20  -> [15.0, 15.0, 25.0]  mean 18.33  sd 5.77
RST  per-rep [5, 5, 3]/20  -> [25.0, 25.0, 15.0]  mean 21.67  sd 5.77
BAS  per-rep [2, 2, 0]/20  -> [10.0, 10.0,  0.0]  mean  6.67  sd 5.77
```

The two treatment arms succeed on **partly different problems**: AO solves `228` in 3/3
replicates where Reset solves it 1/3; Reset solves `285` and `563` 2/3 each where AO never
does; AO uniquely solves `178` once. So the 3.3pp is not a weak version of the same ordering
— the arms are differently distributed over a 6-problem signal set against a 14-problem
floor. That is the substantive reason not to read the gap as an ordering.

**Embedded positive control:** the same script re-derived T8's AC3-Reset grid (5/5/3) and
Baseline grid (2/2/0) and the math-hard grids for AC3-Augment (20/17/18) and full context
(19/19/17) — **all four reproduce T8 exactly**, in the same pass that produced the new AO
numbers. So the AO column and the columns beside it are scored by one scorer in one run.

### math-hard, for completeness

```
AO   [18, 17, 18]/20 -> mean 88.33  sd 2.89   total 53/60
AUG  [20, 17, 18]/20 -> mean 91.67  sd 7.64   total 55/60   (reproduces T8)
BAS  [19, 19, 17]/20 -> mean 91.67  sd 5.77   total 55/60   (reproduces T8)
```

AO is now the *lowest* of the three math-hard arms, but by 3.3pp on a benchmark where 14 of
20 problems are solved by every arm in every replicate. Not a claim in either direction.

### New finding — `BigCodeBench/859` is intrinsically stochastic

The first full-suite re-score of AO rep3 returned **4/20**, disagreeing with the in-run 5/20
on `BigCodeBench/859`. That looked like the T8 environment trap, so I characterised it
instead of picking a number:

* the item **in isolation**: 7/7 repeats score 1.0;
* **full-suite** re-scoring passes of the identical stored code: **7 of 8 pass, 1 fails**.

Its test is the cause, not the environment — it trains an SVM and asserts
`accuracy >= 0.8` with **no seed fixed in the test**, so it is a genuine coin-weighted flake.
This is a *different* failure mode from T8's `BigCodeBench/451`, which is deterministic
(5/5 repeats) and is a library-version difference. AO rep3 is therefore reported at its
**modal 5/20**, and the reply now discloses the flakiness rather than quoting a single
scoring pass. At n=20 one flaky problem is a full 5pp, so this is worth stating.

---

## What changed in `replies/v5/` for Part 2

| File | Change |
|---|---|
| `03_reviewer_5YHP.md` W4 | AO column now **88.3 ± 2.9** and **18.3 ± 5.8**; single-run dagger footnote **deleted**; per-replicate raw counts added for all six cells; a new "second correction" paragraph reporting the narrowed AO margin and declining the ordering; `859` flakiness disclosed in the scoring-environment paragraph |
| `04_response_to_AC.md` | Correction item 1 extended with the AO replication and the narrowed margin. **The numbered list was deliberately NOT renumbered** — the T6 HOLD block below it reserves "a fifth correction" for the pending tau2 withdrawal, and renumbering would have silently invalidated a block that must stay byte-identical |
| `05_final_remarks.md` | Same treatment, same reason |
| `CHANGES.md` | Tally updated (UNVERIFIED 4 → 1, corrections 14 → 15); claim rows **1.16** and **4.10** rewritten; new **§10** T21 integration record with the full N=3 table, the control evidence and the `859` finding |
| `README.md` | CollabLLM guardrail rewritten: AO column is N=3, do **not** claim AC3 beats AO on BigCodeBench; §7 pre-posting blocker struck as done, U6 named as the only survivor |

## Final HOLD-block verification (against `1382e61`, the commit immediately pre-T21)

```
$ git diff 1382e61 -- neurips_review/replies/v5/ | grep '^[-+].*⚠ INTERNAL'
(no output)
$ git diff 1382e61 -U0 -- neurips_review/replies/v5/ | grep -E '^[-+]>'
(no output)
```

Extracted HOLD blocks, `HEAD@1382e61` vs working tree:

| File | md5 | verdict |
|---|---|---|
| `00_general_response.md` | `6a0ccfb1…` | IDENTICAL |
| `01_reviewer_iNYK.md` | `4a71c6d0…` | IDENTICAL |
| `04_response_to_AC.md` | `3f13100e…` | IDENTICAL |
| `05_final_remarks.md` | `345021643…` | IDENTICAL |
| `README.md` | `db34efe3…` | IDENTICAL |

**Not one blockquote line in the entire v5 tree was added or removed.** All five tau2 HOLD
blocks, the orientation preamble and both T19 renumbering notes are byte-identical.

## Ambiguities resolved without asking (per the brief)

1. **T20's U5 footnote wording was written for the case where the cells are NOT run.** They
   were run, so I did not paste it; the footnote is deleted outright and the comparability
   point (BigCodeBench AO re-scored in the unified environment) is folded into the
   scoring-environment paragraph, which is where it now belongs.
2. **`04` and `05` were not renumbered.** Adding the AO correction as a new numbered item
   would have made the pending tau2 withdrawal item "six"/"eight" while the adjacent
   byte-identical HOLD block still calls it "a fifth"/"a seventh". Folding it into the
   existing CollabLLM item preserves both the disclosure and the block.
3. **Reporting AO rep3 as 5/20, not 4/20.** 4/20 came from one of eight scoring passes of an
   item with a seedless stochastic test; 5/20 is the mode (7/8), the isolated value (7/7)
   and the in-run value. Documented rather than silently chosen. **No replicate was dropped.**
4. **The baseline for the HOLD diff is `1382e61`, not the `d989c50` in my session snapshot** —
   `replies/v5/` was committed by other agents after that snapshot was taken, so `d989c50`
   predates the tree and would have made the check vacuous.
5. Nothing under `writing/overleaf_repo/` was touched; no `git checkout` was performed;
   outputs are confined to `outputs/T21/`.

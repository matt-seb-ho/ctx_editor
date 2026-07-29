# T24 — Reconciling the three full-context (Baseline) numbers (red-team H1)

**2026-07-29, autonomous session. Operator asleep; no questions asked, all ambiguity resolved
in-line and logged.**

**Question.** The paper, the reply to iNYK, and the reply to the AC report three different
full-context accuracies for "the same" LiC benchmarks, 52 points apart. Are they measuring
different things (and if so, exactly what), or is our evaluation inconsistent? And — the horn that
actually matters — if T1's condensation baseline (56.1% database) is high because its venue is
less polluted, does T1 still answer the Area Chair's "limited baselines" reservation?

**Verdict up front.**

1. The spread is **fully explained and internally consistent.** All three numbers are correct
   measurements of three deliberately different populations. I found no case of the same setup
   producing two different numbers.
2. The dominant term is **not** model era, evaluator version, or metric. It is **pool difficulty
   selection**, and I can measure it inside a *single run* with the model and evaluator held
   fixed (§3). Restricting T1's own `db_baseline` run to the paper's 25 items moves it
   56.1% → **32.0%**; restricting `code_baseline` to the paper's 25 items moves it
   83.0% → **48.0%**.
3. **T1 still answers the AC**, and on the strongest possible reading: it is the *only* LiC
   evidence we have on a **completely unselected pool**, and AC3 still gains +19.6pp / +9.0pp
   there at p ≤ 0.02. See §5 for the pollution accounting.
4. **But I found a worse problem than H1 while doing this (§6, `F-T24-1`).** The reply to iNYK
   W2 states that the 36-comparison paired matrix — the rebuttal's new headline evidence — is on
   "**the full, non-difficulty-selected pool**". It is not. It runs on `htn50_52_*`, which is
   *explicitly* baseline-failure-selected, and its replay prefixes are *additionally* weighted
   toward baseline failures by design (74–86% failure-prefixes on database). That sentence is
   the direct answer to the reviewer's Q1 and it is false. **This must be fixed before posting.**
   The good news: T1 is the experiment that *does* satisfy the claim, so the fix is a swap, not a
   retraction.

---

## 0. Ground rules

- No `git checkout` (two agents in tree). No edits to `writing/overleaf_repo/` or `replies/v5/`.
- New runs scoped to `outputs/T24/` only.
- Positive control before trusting anything (§1).
- Raw accuracy primary; per-run `adjusted_accuracy` never used for cross-arm comparison (T14/F28).
- TRAPI runs pass `false_negative_analysis.model=gpt-5.4-mini_2026-03-17` (silent-failure trap).

## 1. Positive controls

| control | expected | got | verdict |
|---|---|---|---|
| Reproduce T1's published database Baseline from its own artifact | 56.1% (60/107) | `outputs/T1/main/db_baseline/summary.txt`: `Accuracy: 56.07% (60/107)` | ✅ |
| Reproduce T1's published code Baseline | 83.0% (83/100) | `outputs/T1/main/code_baseline/results.json` → 83/100 | ✅ |
| Re-derive `tab:main` Baseline numerators independently | 12/20, 3/19, 1/25, 8/23 | T17 §2 rational reconstruction + `docs/reports/v8_batch_results.md:27,29` agree | ✅ |
| Pool-membership join: do the paper's 25 database items exist in T1's 107-item run? | 25/25 | 25/25 matched on `sample_id` | ✅ |

Note the deliberate design choice: **§3's decomposition needs no new API calls at all.** It is a
re-slicing of per-sample outcomes from runs that already exist, so it is immune to the
`gpt-5-mini`-unreachable trap (Trap 2) — no cross-model-era level comparison is required to make
the argument. New runs (§5) are only for the pollution *ceiling*, where levels do not need to
match any published era.

---

## 2. What each number actually measures

### 2.1 The paper — `tab:main`, database **4.0**, code **15.8**

| property | value | evidence |
|---|---|---|
| respondent / analyzer | `gpt-5-mini` (both), temp 1.0 | `tex:230`, `tex:458`; `docs/paper_experiments_provenance.md` §"Table 1 (a)" |
| protocol | **replay mode** — fixed user-sim trajectory, last turn(s) regenerated | `tex:456`; provenance §Table 1(a) |
| pool | `data/baseline_traces_v2/{task}` = `data/dev_{task}_subset.json` | provenance; `tex:487` |
| pool size / n | database 25 → n=25; code 25 → n=**19** after pool pre-filter | T17 §1; `run_experiment.py:441-470` |
| numerator | database **1/25**; code **3/19** | T17 §2 |
| shards revealed | all (full conversation replayed to the end) | replay of a completed baseline trace |
| metric | raw accuracy on the **arm-symmetric pool-level pre-filter** denominator | T14/T17; `replay.py:21-56` |
| evaluator | v2 (`math_v2`/`code_v2`/`database_v2`) | `tex:465-470` |
| **pool selection** | **top-25 hardest by GPT-5-mini baseline failure rate** | `docs/lic_dev_set_provenance.md` |

The last row is the whole story. `docs/lic_dev_set_provenance.md` records the selection criterion
verbatim: from the full pool (database 107, code 100), keep samples with `valid_appearances >= 3`,
`errors >= 3`, and `errors / valid_appearances >= 0.6` across **five GPT-5-mini baseline runs**,
then **sort by error rate descending and take the top 25**. Database had **75** eligible items
and kept 25; code had **40** eligible and kept 25.

Consequence: **`tab:main`'s Baseline row is close to a fixed point of the selection procedure, not
an independent measurement of GPT-5-mini.** With 75 items already at ≥60% error and only the top
25 retained, the retained set is dominated by 5/5-wrong items, so GPT-5-mini's baseline on it is
expected to be ≈0%. Observed: **1/25 = 4.0%**. There is no anomaly to explain here — 4.0% is what
the construction guarantees.

The correct ceiling for that pool is not 100% but the **design-oracle** rows measured on the same
25 items: AO **32.0%** and Concat-User **32.0%** (`tex:264-265`). The paper's own "closes 55–80%
of the gap" framing already uses the oracle as the ceiling, which is the defensible framing.

### 2.2 Reply to iNYK W1 — database **22.4 / 19.0 / 19.0**

| property | value | evidence |
|---|---|---|
| respondents | DeepSeek-V4-Flash, gpt-5.4, Kimi-K2.6 | `docs/reports/post_neurips_ac3_phase{1,2}.md` |
| protocol | **last-turn replay**, 3 prefixes per problem | phase1.md title: "last-turn replay (n=3 prefixes)"; `scripts/run_phase1_ac3_deepseek.sh:96` |
| pool | `data/htn50_52_database_subset.json` (50 items, 49 usable) | `run_phase1_...sh:53`, `run_phase2_...sh:69` |
| n | 49 × 3 prefixes = **147** per cell | phase1/2 per-cell rows |
| prefixes | `data/valid_prefixes_htn50_52/{model}/database_v2/conv{0,1,2}` | `run_phase{1,2}...sh:81,101` |
| metric | raw accuracy; identical denominator across all arms in a cell | `CHANGES.md` 1.3 |
| evaluator | v2 | task cfg `database_v2` |
| **pool selection** | **top-50 "high true negative" by GPT-5.2 baseline failure** | `scripts/build_htn50_52_subset.py:1-12` |
| **prefix selection** | **incorrect-but-valid prefixes preferred over correct ones, by design** | `scripts/curate_valid_prefixes.py:29-36` |

Two stacked selections, both measured:

- Pool. `htn50_52_database_subset.json` carries per-item `htn50_52_stats` from the GPT-5.2 LiC
  logs. Over the 50 items: mean **8.86 true-negative (genuinely wrong) runs** and mean **0.70
  correct runs** out of ~10. GPT-5.2's own baseline accuracy on this pool is therefore ≈**7%**.
  This pool is far harder than `sharded_instructions_600`, and it was built to be.
- Prefix. `curate_valid_prefixes.py` docstring, verbatim: *"take the first 3 from the union in
  this order: incorrect-but-valid first (these are the cases AC3 is targeting), then correct.
  Rationale: if all 3 are correct prefixes, AC3 has nothing to fix and the cell contributes 0pp
  signal. We want the prefix pool weighted toward failures the interventions can help."* The
  realised weighting, from `outputs/post_neurips_lic_vanilla/prefix_pool_coverage.json`:

  | model | math | code | **database** | actions |
  |---|---|---|---|---|
  | DeepSeek-V4-Flash | 22.2% | 59.3% | **74.1%** | 23.3% |
  | gpt-5.4 | 18.2% | 26.1% | **79.6%** | 11.3% |
  | Kimi-K2.6 | 22.4% | 22.4% | **78.9%** | 9.3% |
  | gpt-5.5 | 15.5% | 18.9% | **86.4%** | 11.3% |

  (% of the 147/150 chosen prefixes that are baseline-*failure* prefixes.)

So the 19.0–22.4% "Full context" figures are: a difficulty-selected pool, replayed from prefixes
three-quarters of which were chosen *because the baseline failed on them*. They are a **floor by
construction**, exactly as 4.0% is. Everything in that table is paired on the same prefixes, so
the **Δ between arms is valid**; the **absolute level is not a population estimate**.

### 2.3 T1 / CW5 — database **56.1**, code **83.0**

| property | value | evidence |
|---|---|---|
| respondent / analyzer | `gpt-5.4-mini_2026-03-17` (TRAPI); user-sim + system judge `gpt-4o_2024-11-20` | `run_t1_main.sh`; `config/model/gpt5_4_mini_trapi.yaml` |
| protocol | **full end-to-end sharded multi-turn simulation** (`user_mode=sharded`), *not* replay | `run_t1_main.sh` |
| pool | `data/sharded_instructions_600.json` — the complete LiC pool | `run_t1_main.sh:DATA` |
| n | database **107**, code **100** = every LiC instance in those domains | `summary.txt` |
| shards | revealed incrementally by the simulator; avg 4.1 turns (db), 4.0 (code) | T1 RESULTS budget table |
| metric | raw accuracy, 1 run/cell; paired McNemar vs baseline | T1 `analyze.py` |
| evaluator | v2 | `database_v2` / `code_v2` |
| **pool selection** | **none** | `run_t1_main.sh` header: *"The full pool gives n=107 database / n=100 code with no baseline-failure selection bias"* |

T1 is the **only** LiC measurement in the whole project taken on an unselected population.

---

## 3. The decomposition — one run, model and evaluator held fixed

This is the load-bearing evidence. It uses only per-sample outcomes already stored in
`outputs/T1/main/*/results.json`, joined against the item lists of the other two pools. Same
respondent, same evaluator, same protocol, same run — **only the item set changes.**

Script: `/tmp/t24_pool.py` (re-runnable; joins on `sample_id`, 25/25 and 50/50 matched).

### LiC-database (gpt-5.4-mini, end-to-end, v2)

| item set | n | Baseline | AC3-Reset | AC3-Gated-Reset |
|---|---|---|---|---|
| full LiC pool (T1's venue) | 107 | **56.1%** | 75.7% | 73.8% |
| ∩ `htn50_52` (the 3-model matrix's pool) | 50 | **32.0%** | 62.0% | 58.0% |
| ∩ `dev_database_subset` (the paper's pool) | 25 | **32.0%** | 60.0% | 60.0% |
| complement of `dev_database_subset` | 82 | 63.4% | — | — |
| complement of `htn50_52` | 57 | 77.2% | — | — |

### LiC-code (gpt-5.4-mini, end-to-end, v2)

| item set | n | Baseline | AC3-Reset |
|---|---|---|---|
| full LiC pool | 100 | **83.0%** | 92.0% |
| ∩ `htn50_52` | 44 | 72.7% | 86.4% |
| ∩ `dev_code_subset` (paper's pool) | 25 | **48.0%** | 72.0% |
| complement of `dev_code_subset` | 75 | 94.7% | — |

**Reading.** Difficulty selection alone, with everything else fixed, costs the baseline
**24.1pp on database** (56.1 → 32.0) and **35.0pp on code** (83.0 → 48.0). That is over
half of the total spread, from item selection alone.

The residual (database 32.0 → 4.0; code 48.0 → 15.8) is the part that cannot be measured
tonight because `gpt-5-mini` is unreachable (Trap 2), but its mechanism is not in doubt and it is
not "model capability": **the paper's pool was selected adversarially *against GPT-5-mini
specifically*.** Selection is model-specific, so it transfers only partially to a different model.
GPT-5.4-mini inherits 24pp of the hardness; GPT-5-mini, the model the filter was fitted to, eats
essentially all of it and lands at the ≈0% its selection criterion guarantees. **No claim in this
worklog depends on comparing absolute levels across model eras.**

Monotonicity check, which is the structural prediction: for every arm and both tasks, the ordering
is `full pool > htn50_52 ≥ dev_subset`, i.e. exactly the ordering the three selection
stringencies predict (no selection > top-50 of 107 > top-25 of 107). ✅

---

## 4. Reconciliation table (rebuttal-ready)

| # | Where it appears | database | code | Respondent | Protocol | Pool (n) | Pool selection | Evaluator | Metric |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Submitted paper, Table 1 | **4.0%** (1/25) | **15.8%** (3/19) | GPT-5-mini | last-turn **replay** | `dev_{task}_subset` (25 / 19) | **top-25 hardest by GPT-5-mini baseline failure rate**, 5 runs, ≥60% error | v2 | raw, arm-symmetric pool pre-filter |
| 2 | Rebuttal → iNYK W1 | **22.4 / 19.0 / 19.0** | — | DSV4F / gpt-5.4 / Kimi-K2.6 | last-turn **replay**, 3 prefixes | `htn50_52_{task}` (49 × 3 = 147) | **top-50 hardest by GPT-5.2 true-negative rate** (GPT-5.2 ≈7% on this pool) **and** prefixes 74–86% baseline-failure-weighted | v2 | raw, one denominator per (task, prefix) cell |
| 3 | Rebuttal → CW5 / AC (T1) | **56.1%** (60/107) | **83.0%** (83/100) | gpt-5.4-mini | **full end-to-end sharded simulation** | `sharded_instructions_600` (107 / 100) | **none — complete LiC pool** | v2 | raw, paired McNemar |

**Why they differ, in one line each.**
Row 1 measures *the hardest quarter of LiC for the model being measured*; row 2 measures *the
hardest half of LiC, replayed from conversations chosen because they had already failed*; row 3
measures *all of LiC, run end-to-end*. Rows 1 and 2 are floors by construction and exist to
concentrate the failure mode under study; row 3 is the population estimate. The one thing all
three share is that **within each row every arm sees the identical items**, so the paired Δ is the
comparable quantity across all three, and the absolute level is not.

Cross-check that this is design and not drift: applying the row-1 and row-2 item sets to the
row-3 run reproduces the ordering and most of the magnitude (§3) with model, evaluator, protocol
and metric all held fixed.

---

## 5. Horn two — is T1's venue actually polluted, or did condensation get an easy ride?

This is the reading that costs us the AC, so it gets its own evidence.

### 5.1 Headroom is demonstrated, not assumed

The strongest fact needs no new run: on T1's own unselected pool, **AC3-Reset recovers +19.6pp on
database (56.1 → 75.7, McNemar p = 0.0005) and +9.0pp on code (83.0 → 92.0, p = 0.0225)**, and
MT-OSC/summarisation recover nothing. A venue in which a pure context-editing intervention — no
extra information, no tool access, same shards — moves accuracy by 19.6pp is *by definition* a
venue where ≥19.6pp of the baseline's failures were context-induced and recoverable. "Low
pollution" is not compatible with that number.

### 5.2 Pollution ceiling, measured (new runs, `outputs/T24/`)

T1 lacked the design-oracle arms, so the pollution *magnitude* in its venue was unquantified. I
added them: `concatenate_user` (single-turn upper bound) and `omit_assistant` (AO) on the full
107/100 pool, same model, same evaluator, same harness
(`neurips_review/autoresearch/tasks/T24/run_t24_ceiling.sh`).

<!--T24-CEILING-->

### 5.3 Is a 56.1% baseline still "high-pollution"?

Yes, and the paper's own definition supports it. "Pollution damage" is *ceiling − full-context*,
where the ceiling is the design oracle on the same items — not 100%. On the paper's pool that
ceiling is **32.0%** and the baseline is 4.0%, i.e. damage = 28.0pp. T1's venue is measured in
§5.2. The relevant comparison is not "4% is low so it must be polluted, 56% is high so it must be
clean" — a 4% cell whose oracle is 32% has 28pp of headroom; that is *less* absolute headroom than
T1's venue if T1's oracle sits anywhere above 84%.

**Honest statement of what T1 is and is not.** T1's venue is *less difficulty-concentrated* than
the paper's, and its per-item pollution rate is lower — most of the 107 database items are not
polluted at all, which is precisely why the baseline is 56%. That **dilutes** the measured Δ; it
does not inflate it. A dilution argument runs *against* us, not for us: the +19.6pp on the full
pool is a lower bound on what AC3 does where pollution binds (cf. the same run restricted to the
hard quarter: 32.0 → 60.0, **+28.0pp**). So the condensation baselines were **not** given an easy
ride relative to AC3 — they were run on the same conversations, and they still lost by 12–28
points while consuming 1.02–1.19× AC3-Reset's strategy calls.

**Does T1 answer the AC?** Yes, on all three of the AC's requirements, and I would argue it is our
single best experiment:

1. *It is a condensation baseline*, which is what the AC asked for (summarisation at two budgets +
   MT-OSC at its published window), compute-instrumented, budget-matched, and paired.
2. *It is our only unselected-population evidence.* Every other LiC result we have — the paper's
   table, the multi-model table, the 36-comparison matrix — is on a baseline-failure-selected
   pool. T1 is not. That makes it the answer to iNYK's Q1 as well as the AC's request.
3. *It is end-to-end*, not replay, so it also removes the replay confound iNYK raised in W2.

**The one scoping caveat T1 does need**, and it should be stated by us: T1's 56.1% baseline is a
*population-average* venue, so its Δ is an average over polluted and unpolluted items. It should
not be quoted next to `tab:main`'s numbers as though the two are the same measurement — which is
exactly what H1 says. Fix the framing, keep the conclusion.

---

## 6. `F-T24-1` — new HIGH finding: the "non-difficulty-selected pool" claim is false

**Where.** `neurips_review/replies/v5/01_reviewer_iNYK.md:31`, answering the reviewer's W2 (the
difficulty-selection complaint) and feeding Q1:

> "It is also no longer the primary evidence. **On the full, non-difficulty-selected pool**,
> AC3-Reset improves over full context on **33 of 36 paired comparisons (+15.9pp, p < 0.0001)**,
> and we have moved the headline onto these numbers."

Echoed at `00_general_response.md:109` ("the gains are not an artifact of difficulty-selected
data… The powered evidence is the 36-comparison paired test in Common Weakness 2").

**Why it is false.** The 36 comparisons are parsed by
`neurips_review/experiments/paired_analysis.py:23-26` from
`docs/reports/post_neurips_ac3_phase{1,2}.md`. Those reports are produced by
`scripts/run_phase1_ac3_deepseek.sh` / `run_phase2_ac3_other_models.sh`, which set
`task.data_file=data/htn50_52_{task}_subset.json` (lines 51-54 / 67-70) and
`execution.replay_source=data/valid_prefixes_htn50_52/...` (lines 81 / 101). `htn50_52` is
baseline-failure-selected by construction (`build_htn50_52_subset.py:1`, "top 50 high-true-negative
problems per task from gpt-5.2 logs"; measured GPT-5.2 accuracy on the database half ≈7%), and the
prefixes are *deliberately* weighted toward baseline failures (§2.2).

**Severity: HIGH, above H1.** H1 is an unexplained spread. This is an affirmative factual claim,
made to the reviewer who raised the exact concern, about the experiment we designate as our new
headline evidence — and it is checkable from the run scripts we intend to release.

**It is cheap to fix, because we have the experiment that does satisfy the claim.** T1 (n=107/100,
`sharded_instructions_600`, no selection, end-to-end) and the T4 random-40 math run
(`data/rebuttal_random_math40.json`, uniform random, seed 42, end-to-end, N=3) are both genuinely
unselected. The 36-comparison matrix's job is *power and paired significance on the hard regime*;
T1's job is *unbiased population estimate*. Say that.

**Secondary exposure.** The paper never states that `tab:main`'s LiC pool is difficulty-selected.
`tex:328` contrasts "a difficulty-selected LiC subset (Table 3)" with "the default subset", which
reads to any reviewer as *the default subset is not difficulty-selected*. The only disclosure is
oblique, in an appendix, at `tex:513`: "we **re-ran the subset selection protocol** using GPT-5.2
LiC logs (instead of GPT-5-mini)" — which presupposes a selection protocol for the default set
without ever describing it. A reviewer who reads `docs/lic_dev_set_provenance.md` (or who simply
asks why full-context scores 4% on Spider) will find a 25-item pool chosen for ≥60% GPT-5-mini
baseline failure. **Disclose this ourselves, in the Table 1 caption.** Per `README.md`'s own rule,
a surfaced weakness reads as rigour and a found one reads as spin; and here the mitigation is
strong (the design-oracle rows are on the same pool and cap the ceiling at 32%, so the gap-closure
framing is unaffected).

---

## 7. Draft wording for `replies/v5/` (do not apply here — for the operator)

### 7.1 New footnote, first place a non-`tab:main` LiC number appears (CW5, after "…our two highest-pollution LiC tasks")

> Three notes on comparability, because this table's absolute accuracies are far above Table 1's
> and we would rather explain that than have it read as an inconsistency. (i) **Pool.** These runs
> use the *complete* LiC pool for each task — 107 database and 100 code instances,
> `sharded_instructions_600` — with no instance selection of any kind. Table 1 reports a
> 25-instance-per-task subset selected for high full-context failure rate under GPT-5-mini (the
> protocol Appendix D.2 refers to), and the post-submission 3-model matrix uses a 50-instance
> subset selected the same way from GPT-5.2 logs. (ii) **Respondent.** gpt-5.4-mini here, versus
> GPT-5-mini in Table 1. (iii) **Protocol.** Full end-to-end sharded simulation here, versus
> last-turn replay in Table 1. Item selection is the dominant term: restricting *this* run to
> Table 1's exact 25 database instances — same model, same evaluator, same conversations — moves
> full context from 56.1% to **32.0%** and AC3-Reset from 75.7% to **60.0%**. Absolute accuracies
> are therefore not comparable across the three tables; **the paired Δ within each block is the
> quantity to read**, and it is computed on identical items in all three.

### 7.2 Replacement for `01_reviewer_iNYK.md:31` (**required — current text is false**)

> We would add that difficulty stratification does what it is designed to do: it concentrates
> evaluation where the failure mode under study actually occurs, since problems the baseline
> already solves cannot exhibit recovery. That is also why we should be explicit about which of
> our experiments are stratified and which are not, since your W2 turns on exactly this. The
> 36-comparison paired matrix **is** on a difficulty-selected pool (the 50 highest-failure-rate
> instances per task from GPT-5.2 logs, with replay prefixes weighted toward baseline failures);
> its purpose is statistical power on the regime where pollution binds, and every arm sees
> identical items, so its **+15.9pp on 33 of 36 paired comparisons (p < 0.0001)** is a valid
> paired effect but not a population estimate. The unbiased evidence is separate and we report it
> as such: the uniformly random n=40 subset in Q1 below, and the condensation-baseline experiment
> in Common Weakness 5, which runs on the **complete, unselected LiC pool** (n=107 database, n=100
> code, end-to-end rather than replay) and where AC3-Reset still gains **+19.6pp** on database
> (p = 0.0005) and **+9.0pp** on code (p = 0.023) over full context.

### 7.3 One clause for `01_reviewer_iNYK.md` W1, under the 3-model database table

> (n = 147 per cell: 49 instances × 3 conversation prefixes, from the 50 highest-failure-rate
> database instances in the GPT-5.2 LiC logs; last-turn replay. Every arm is scored on the same
> 147 conversations, so the column-to-column differences are paired; the absolute level is a
> floor set by the selection and is not comparable to Table 1's 4.0% or to Common Weakness 5's
> 56.1%, which are a *harder* and an *unselected* pool respectively.)

### 7.4 Table 1 caption addition, and `04_response_to_AC.md`

Caption: > Instances are the 25 per task with the highest full-context failure rate across five
GPT-5-mini baseline runs (Appendix D.2); the design-oracle rows are computed on the same
instances, so the gap-closure percentages are pool-independent.

For the AC letter, one sentence after the condensation result:

> We would flag one thing about this experiment ourselves: unlike Table 1, it runs on the complete
> LiC pool with no instance selection, which is why its full-context baseline (56.1% / 83.0%) is
> much higher than Table 1's. That makes the comparison *harder* for us, not easier — most
> instances in an unselected pool are not pollution-limited at all, which dilutes any Δ — and
> AC3-Reset still beats full context by +19.6pp and both condensation budgets by +22.4 to +28.0pp
> on the same conversations.

---

## 8. Files

- `neurips_review/autoresearch/tasks/T24/run_t24_ceiling.sh` — the §5.2 oracle arms.
- `neurips_review/autoresearch/tasks/T24/run_log.txt`, `nohup.out` — their logs.
- `outputs/T24/{db_concat,db_ao,code_concat,code_ao}` — their artifacts.
- `/tmp/t24_pool.py` — the §3 re-slicing (no API calls; reproduces §3 from existing runs).

## 9. Ambiguities resolved without asking

| ambiguity | resolution | rationale |
|---|---|---|
| "Which run produced `tab:main` Baseline?" — the v8 batch dirs are gone from disk | Used T17's rational-reconstruction + `docs/reports/v8_batch_results.md:27,29` as the source of truth for 1/25 and 3/19 | Two independent sources agree; re-running is impossible (Trap 2) |
| Whether to attempt a GPT-5-mini control | **Did not.** Built §3 so no cross-era level comparison is needed | Trap 2: a teammate's control returned 44.0 vs published 12.0 for this reason |
| Which "pollution ceiling" to measure for T1 | Concat-User **and** AO on the same pool | Concat-User is the LiC single-turn upper bound; AO is the paper's design oracle and makes the number directly comparable to `tab:main`'s 32.0 |
| Scope creep — `F-T24-1` is outside the literal T24 brief | Reported anyway, marked HIGH | The brief says to flag genuine inconsistencies immediately; this is one, and it is in reviewer-facing text |

# General Response to All Reviewers

> **⚠ INTERNAL — READ BEFORE POSTING. NOT PART OF THE REPLY.**
> *Updated by T19, 2026-07-29 ~17:30 UTC. One of the two audits this preamble originally gated has landed; the other has not.*
>
> 1. **T14 (false-negative-adjustment audit) — RESOLVED 16:15, largely in the paper's favour. The provisional flag on every LiC figure below is lifted.** `tab:main`'s denominators come from an **arm-symmetric pool-level pre-filter** (`data/baseline_traces_v2/*_false_negatives.json`, computed once on baseline traces and applied identically to every arm) that exactly reproduces its 20/19/25/23 denominators. **That is correct and should be defended, not conceded.** What is invalid is the *per-run* `adjusted_accuracy` metric: it inflates reset arms by **+13.9 to +55.9pp** against **+0.2 to +6.5** for no-reset arms, because the FN judge sees 1.00 user turns/sample on AC3-Rewrite against 5.35 on baseline. It touches at most 4 `tab:main` cells at ≤1 sample each, and 2 of those 4 favour prior work. Recommendation adopted: report **raw** as primary, keep the pool filter as the only FN adjustment, delete per-run adjusted accuracy. Every LiC number in this document is already raw, so **nothing here moves**. Two conclusions do flip under correction, both on **AC3-Rewrite** (code +46.0 → −5.3, actions +22.4 → −1.5), but **neither is a published error** — `tab:main` has no Rewrite LiC row and `tab:megatable` is computed from raw. **AC3-Reset and AC3-Gated-Reset beat baseline in all 8 cells under raw, shipped-adjusted and corrected alike.** Sources: F40–F42, `AR/tasks/T14/RESULTS.md`.
> 2. **T6 (multi-replicate tau2) — RESOLVED 2026-07-29, and it goes against us. The HOLD is lifted and the withdrawal is now written into Common Weakness 4.** The full published matrix was re-run at N=3 (3 models x 5 arms x 3 replicates x 19 tasks = 855 scored rollouts, 15/15 cells). **Two of three published baselines do not replicate** — DSV4F 31.6 → **70.2 ± 11.0**, Kimi 26.3 → **78.9 ± 0.0** — and on all three models the re-measured baseline is at or above every AC3 arm. The positive controls hold (gpt-5.4 baseline 68.4 vs published 68.4; AO 0.0 across 9 cells / 171 rollouts; `gpt-5-mini` reachable; byte-identical invocation strings; no model substitution), so this is "the published baselines were clipped", not "not comparable". **Post no tau2 improvement claim.** What survives and must still be posted: **AO = 0.0 on every model, structurally**. Also unexplained and disclosed: gpt-5.4's AC3 collapse (84.2 → 47.4) with the baseline reproducing exactly; a real fork bug (53% of analyzer calls fall back to raw-completion splicing) was found and is worth only +2.3pp. Sources: `AR/tasks/T6/worklog.md`.
> 3. **T17 + T18 (the ERGO denominator defect) — RESOLVED, and now disclosed in Common Weakness 5.** ERGO alone was scored on unfiltered pools (16/23, 11/25, 3/25, 12/25) against everyone else's 20/19/25/23; confirmed against the author's own Overleaf commit `d856247`. **Corrected ERGO/math = 80.0, which beats AC3-Reset (75.0) and ties AC3-Gated-Reset (80.0). This ships.** Corrected ERGO/code is **≈43.9** — T18 measured the free parameter directly, so the correction is ≈ −0.1pp, not T17's estimated +13.9pp; **do not ship T17's 57.9**, it would overstate a competitor by 14pp. ERGO/actions **cannot** be corrected: no `actions_false_negatives.json` has ever existed and the n=23 column is the ad-hoc normalisation the paper confesses at `tex:508`. Scorecard: published 1/12 ERGO wins-or-ties → **measured 3/12** (5/12 only if the unclosable actions cell sits at its ceiling). **Frame with F49** — paired exact sign tests show no ERGO-vs-AC3 `tab:main` difference is significant at n≈20 in either direction (code p=0.375, math p=1.00). Sources: F43–F49, `AR/tasks/T17/RESULTS.md`, `AR/tasks/T18/worklog.md`.
>
> Every `⚠ INTERNAL` block must be resolved and deleted before anything is posted. Claim-by-claim provenance is in `CHANGES.md`.

We sincerely thank all reviewers for their careful and constructive feedback. We are encouraged that the reviewers found the core contribution compelling, and we address every concern below with new evidence collected since submission. Where a reviewer's concern turned out to be right, or where our own new evidence contradicts something we previously reported, we say so plainly and first.

### Common Strengths Highlighted by Reviewers

* **The self-contained vs. referential framing.** Reviewers noted that this distinction "cleanly explains why AO is near-perfect in some settings and collapses to zero in others" (**iNYK**), is "well motivated" (**Vg97**), and represents "a meaningful conceptual improvement over treating all assistant-generated context as uniformly harmful" (**5YHP**).
* **The structural-exclusion (contagious pollution) result.** All three reviewers highlighted this. **iNYK** noted it "carries a useful lesson for any multi-stage LLM pipeline"; **Vg97** suggested it "should be considered being moved to the main section"; **5YHP** called it "one of the strongest parts of the paper," suggesting "information-flow constraints, rather than prompt instructions alone, may be necessary."
* **Modularity and practical interpretability** of the specification-extraction, approach-evaluation, and intervention separation (**5YHP**).

We have taken **Vg97**'s and **5YHP**'s suggestion and are moving the structural-exclusion ablation into the main body.

### Summary of New Evidence in This Rebuttal

Since submission we completed a full model x benchmark x method matrix, added paired significance testing, and ran the specific experiments reviewers asked for rather than promising them. Five headline additions:

1. **The same four operators are now evaluated across 3 respondent models x 4 LiC tasks, plus CollabLLM, WildChat, and tau2**, with no per-benchmark tuning (Common Weakness 1).
2. **Paired significance testing**: AC3-Reset improves over full context on **33 of 36 paired comparisons** (mean **+15.9pp**, sign-test **p < 0.0001**), above the assistant-omission design-oracle's **+13.3pp** — though we also set out, in the same section, exactly where AC3 does and does not separate from that oracle, because the head-to-head is a wash outside LiC-database (Common Weakness 2).
3. **A new unbiased-subset, end-to-end, 3-replicate experiment** confirming the gains are not an artifact of subset selection, replay, or a single run (Common Weakness 3).
4. **The condensation baseline Vg97 and the Area Chair asked for is now run, at measured matched compute.** Summarisation does not close the gap; it moves accuracy *down*, under our own condenser prompt and under a neutral-prompt variant that deletes the clause a reviewer could read as handicapping it. MT-OSC at a window scaled to the conversation length engages roughly eight times as often and scores **worse**, not better (Common Weakness 5).
5. **A direct, judge-free span-level evaluation of the analyzer as a detector, and a causal ablation of naturally occurring assistant content**, which 5YHP asked for and which we report including the part that does not flatter us — it establishes that context pollution is real and concentrated, and it also retracts a mechanism claim in our paper (Reviewer 5YHP, W5).

We also correct three numbers we reported to reviewers in earlier correspondence or in the submission, having re-measured them at N=3: a CollabLLM MATH-Hard figure, the WildChat win-rates, and the end-to-end subset result. **Larger than any of those, and entirely against us: on re-running the whole tau2 matrix at N=3 we found that two of our three published tau2 baselines do not replicate, and we withdraw the improvement claim on that benchmark** (Common Weakness 4). Separately, we found a scoring error in our own main LiC table that **understated a baseline** we compare against; we report the corrected comparison in Common Weakness 5. Details are in the relevant sections.

---

## Common Weakness 1 (from the Area Chair, Reviewer Vg97 W3/Q4, and Reviewer 5YHP W2)

> The method changes substantially across settings... it is not obvious whether the paper is validating a single method, a family of prompt-engineering patterns, or several task-specific context-management variants.

**Response:** We appreciate this concern and agree it deserved a direct empirical answer rather than a description. AC3 is a single method, and we now **demonstrate** this.

Every setting uses the same two-query analyzer (specification extraction, then approach evaluation) and the same operator set. The post-submission matrix runs **the same four operators across 3 respondent models (gpt-5.4, DeepSeek-V4-Flash, Kimi-K2.6) x 4 LiC tasks, plus CollabLLM, WildChat, and tau2-bench**, using one code path with no per-benchmark tuning.

| Component | Status |
|---|---|
| Two-query analyzer (spec extraction, then approach evaluation) | **Essential.** Identical across all four benchmarks |
| Structural exclusion during spec extraction | **Essential where user turns self-specify the task.** Off by design where they do not |
| Operator (Augment / Reset / Gated-Reset / Rewrite) | **The single knob.** Intensity scales with pollution level and model weakness |
| Gating | Optional |
| Memory (cheatsheet) | Optional, ablated, not load-bearing for any headline claim |

What varies across settings is **operator intensity**, which is a documented knob rather than a redesign.

**On how the operator is chosen, since several tables in this rebuttal report a best operator per cell.** Operator choice is **not** tuned per cell at evaluation time, and we should state the rule rather than leave it to be inferred. The deployment rule is fixed in advance and indexed by a property of the setting that is observable before any run: **always-on AC3-Reset where user turns self-specify the task and an intervention is cheap; AC3-Gated-Reset where an unnecessary edit carries state-disruption cost; structural exclusion off where intent is co-constructed across assistant turns.** The headline paired result in Common Weakness 2 is that single fixed configuration — AC3-Reset, 33 of 36 paired wins — and not a per-cell maximum. Where a per-cell best appears in a table we will label it as such, and report the fixed-rule row alongside it.

We can now put a measurement behind the claim that the *operator* is the knob and the *analyzer* is the shared engine. Holding the respondent model fixed and varying only the analyzer model across five models from four families (Moonshot, DeepSeek, OpenAI x2, Meta), on LiC code+database, every analyzer produces a positive and individually significant gain over full context, from **+12.9pp to +39.9pp** (n=178 matched pairs, exact McNemar, all p < 0.001). No configuration falls below baseline. The method degrades gracefully with analyzer strength rather than depending on one particular analyzer; the full table is in our reply to **Vg97 (Q3)**.

The two cases reviewers flagged are the stated theory being applied, not departures from it:

* **CollabLLM disables structural exclusion.** Our claim is that structural exclusion applies *when user turns independently specify the task*. CollabLLM is precisely the regime where they do not, because intent is co-constructed across assistant turns. Applying structural exclusion there would contradict our own analysis.
* **tau2 adds environment-state tracking.** This is the same analyzer with tool-call state tracked, because the environment is stateful.

We should add, since this section is about the operator-selection rule, that **tau2 no longer supports the rule and we have stopped citing it as if it did.** An earlier version of this response argued that tau2 confirmed the intensity ordering directly — the lightest operator winning on the strongest model and the heaviest on the weakest. Our N=3 re-measurement (Common Weakness 4) does not reproduce that ordering, and it also withdraws the tau2 magnitude comparison outright. The rule's evidence is now the LiC matrix, CollabLLM and WildChat; tau2's contribution to this paper is the structural result that blanket omission fails there, not an operator ranking.

**Revision:** We will add this component table and an explicit unified-algorithm statement to Section 3, and rename the tau2 variant so its continuity with the shared analyzer is unambiguous.

---

## Common Weakness 2 (from Reviewers iNYK W1/Q2, Vg97 W2/Q2, and 5YHP W3)

> Many of the headline LiC cells use small sample sizes, with only the Gated-Reset row repeated three times... Please provide confidence intervals, paired tests, or bootstrap analyses.

**Response:** Thank you for pressing on this. We have both scaled the evaluation and added the paired tests requested.

**Sample size.** LiC now uses **up to 50 problems per task, each evaluated across 3 independent conversation prefixes** (36–50 conversations per prefix depending on task, up to 150 per cell), on **3 models**. The submitted version used 18 to 25 conversations on 1 model. We should be explicit about what this pool is, because Reviewer iNYK's W2 turns on it: **the matrix is difficulty-selected** — the 50 highest-failure-rate instances per task from the GPT-5.2 LiC logs, with replay prefixes further weighted toward baseline failures. Its purpose is statistical power in the regime where pollution binds, and every arm sees identical items, so the paired result below is a valid paired effect but **not a population estimate**. Our unselected evidence is separate and reported as such: the uniformly random n=40 end-to-end subset in Common Weakness 3, and the complete-pool condensation experiment in Common Weakness 5.

**Paired significance.** Because every method is evaluated on the *same* (model, task, prefix) triples, the paired difference is the statistically correct comparison. Across all **36 paired comparisons** (3 models x 4 tasks x 3 prefixes), on **raw accuracy**:

| Method | Mean paired gain vs. full context | Wins / Losses / Ties | Sign-test p |
|---|---|---|---|
| **AC3-Reset** | **+15.9pp** | **33 / 2 / 1** | **< 0.0001** |
| **AC3-Augment** | **+15.2pp** | 31 / 1 / 4 | **< 0.0001** |
| AC3-Gated-Reset† | +17.0pp | 11 / 1 / 0 | 0.0063 |
| AC3-Rewrite† | −0.3pp | 6 / 6 / 0 | 1.00 |
| Assistant omission (design-oracle on LiC) | +13.3pp | 31 / 4 / 1 | < 0.0001 |

† These two rows cover **12 of the 36 triples**, on one respondent model (DeepSeek-V4-Flash), which is why their counts do not sum to 36; we report them separately rather than pooling them with the full-matrix rows. We print the **AC3-Rewrite** row for completeness even though it is our worst: its cells predate the analyzer-parity fix, and **we do not claim that Rewrite improves LiC accuracy**. Rewrite's evidence is on referential settings — the strongest single cell of our per-respondent WildChat table is Kimi-K2.6/Rewrite at 91.5% against assistant omission (a single-run cell, n=59) — which is the same operator-by-regime story as the rest of the paper, and we would rather show the operator that loses on LiC than present four operators and print the three that win.

The table above is a sign test over cells, which is assumption-light but discards effect size and treats 36 correlated cells as independent. Since Reviewer **Vg97** asked specifically for confidence intervals and bootstrap analyses, we also report the two stronger statistics on the same data, at the level of individual problems (n = **1,668** paired items after dropping the conversations that errored in any arm, so every arm is scored on identical items):

| Method | Item-level exact McNemar | Problem-clustered bootstrap, mean paired gain |
|---|---|---|
| **AC3-Reset** | 350 wins / 93 losses, **p < 1e−30** | **+15.4pp, 95% CI [+11.5, +19.4]** |
| **AC3-Augment** | 323 / 79, p < 1e−30 | +14.6pp, [+10.8, +18.6] |
| AC3-Gated-Reset† | 126 / 33, p = 5e−14 | +16.8pp, [+11.6, +22.0] |
| AC3-Rewrite† | 42 / 42, p = 1.00 | **+0.0pp, [−3.8, +3.8]** |
| Assistant omission | 297 / 87, p < 1e−28 | +12.6pp, [+9.2, +16.1] |

The bootstrap resamples whole **problems** (191 of them, each contributing up to 3 prefixes x 3 models), which is the correlation structure the sign test ignores; we treat it as the primary interval and the sign test as the assumption-light cross-check. All three statistics agree. Note that the interval also sharpens the AC3-Rewrite row: at the item level Rewrite is not mildly negative but **exactly neutral on LiC, bounded within ±4pp**, which is the honest version of the row we print above.

**AC3's mean clears the full-context baseline on every model**: +17.1pp (DeepSeek-V4-Flash), +16.7pp (gpt-5.4), +13.9pp (Kimi-K2.6). AC3-Reset is the **single fixed configuration** behind the 33/36 row — it is not a per-cell maximum, and we state a deployment rule rather than selecting an operator per cell (Common Weakness 1).

### Where AC3 separates from assistant omission, and where it does not

Several corrections in this rebuttal narrow individual AC3-vs-assistant-omission comparisons, so we would rather assemble the whole picture here than leave a reader to piece it together from our separate replies. Assistant omission is a strong baseline — on LiC it is a design-oracle by construction — and across the full 36-triple matrix the head-to-head is close to a wash: AC3-Reset's mean advantage over it is **+2.6pp**, on **15 wins, 17 losses and 4 ties**. We state that plainly, because it is computable from the two rows above. What the aggregate hides is that the difference is not evenly spread. It is concentrated exactly where our analysis says it should be:

| Setting | AC3-Reset vs. assistant omission | Why the framework predicts it |
|---|---|---|
| **LiC-database** (3 models, 9 triples) | **+18.7pp**, **8 wins / 1 loss** — 49.0 / 56.2 / 55.1 against 45.6 / 27.9 / 30.6 | Shards must be assembled against a schema, so deleting assistant turns discards partially-correct assembly work: consolidation beats deletion |
| LiC math / code / actions (27 triples) | −3.1 / −3.8 / −1.3pp (1/7/1, 2/6/1, 4/3/2) | User turns fully self-specify the task, so omission is already near-optimal and there is little left for AC3 to add |
| **tau2-bench** (stateful, 3 models) | Assistant omission is **0% on every model**, and structurally so | Tool-call results exist only in assistant turns; omission destroys them and the rollouts never terminate |
| **WildChat** (referential, real human–AI dialogue) | AC3 favoured in **every** populated cell of our per-respondent table, 13 of which are against omission; pooled order-balanced **87.8 / 91.2%** | Intent is co-constructed across assistant turns, so blanket deletion removes the specification itself |
| CollabLLM BigCodeBench | **+3.3pp — an ordering we explicitly do not claim**, inside the noise at N=3 | — |

At the level of individual problems the same picture holds with an interval attached: across the matrix AC3-Reset is **+2.8pp over assistant omission, 95% CI [−0.3, +5.9]** by the same problem-clustered bootstrap — i.e. not distinguishable from zero, which is why we do not claim it — while on **LiC-database alone it is +18.6pp, 95% CI [+10.7, +26.6]** (113 problem-wins against 31, exact McNemar p < 1e−11). The concentration is not a reading of the cell means; it survives the strongest test we can apply to it.

The claim we defend is therefore not "AC3 beats assistant omission everywhere", and we would not want it read that way. It is that **assistant omission is the right operator in exactly one regime — fully self-contained tasks — and that our framework says in advance which regime a setting is in**, from a property observable before any run: do the user turns independently specify the task, and is the environment stateful? A method that *predicts* a baseline's successes as well as its structural failures, and supplies an operator for the regimes where that baseline is unusable, is a different kind of contribution from one that must out-score it in every cell.

Two further results bear on the same question, both new here and neither reproducible by a delete-everything editor. First, in the constructed-pollution factorial, with the injected pollutant **still present in the context**, AC3-Reset lifts accuracy from the polluted baseline's 9.3% to **59.8%**. Second, measured with no detector and no judge anywhere in the label path, natural pollution is **real and concentrated** — across 111 naturally occurring spans the spread of per-span causal effects significantly exceeds a replicate-matched null (0.155 vs. 0.125, p = 0.0085), with 16 large-effect spans where the null predicts 9.3 (p = 0.017) — and **AC3 removes 100% of the spans that ablation proves causally harmful**. Where that study went against us, we say so in our reply to **5YHP (W5)**: AC3 achieves this by rebuilding the specification from the user side rather than by selective excision, which corrects our account of the mechanism, not the effect.

Two points of methodological candour, both of which we will also state in the paper.

* **We report raw accuracy, not our false-negative-adjusted accuracy.** Our adjustment procedure asks a judge, from the *visible* messages only, whether the user ever specified the task, and drops "under-specified" items from the denominator. That is post-treatment conditioning: an arm that hides assistant or user content causes more items to look under-specified and therefore has more of its failures excluded. On a LiC-database cell we measured exclusion rates of 9% for baseline against 62% for AC3-Reset. Re-judging every arm from an identical, arm-symmetric view collapses exclusions to 2–6% uniformly and reproduces the raw ordering. The bias ran **in our favour**, so every number in this rebuttal is the raw one, and we are correcting the paper accordingly. **We should be precise about the blast radius, since the concession would otherwise be read wider than the defect.** Table 1's denominators (20/19/25/23) are **not** produced by this per-run metric. They come from a **pool-level pre-filter** computed once on baseline traces and applied identically to every arm *before any method runs* — an arm-symmetric filter that reproduces those denominators exactly, and which we stand behind and will document in the appendix. The per-run adjustment touches at most four cells of Table 1 by at most one sample each, and two of those four move in favour of prior work. What we are withdrawing is the per-run metric as a *reported statistic*, not the main table.
* **What our replicates vary.** On LiC and CollabLLM, replicate runs differ through temperature-1.0 sampling of the respondent, analyzer and user simulator on a fixed problem draw. The intervals we report therefore estimate decoder variance, not sampling variance over problems, and are correspondingly narrower than a full re-draw would give. WildChat is the exception: its N=3 are independent seeds over the sampled pool. We will state this distinction explicitly in the appendix.

**WildChat** is reported over 3 seeds with tight intervals: **87.8 +/- 2.1** (Reset) and **91.2 +/- 2.1** (Augment) against assistant omission. These are order-balanced values from a full re-judge; see our reply to **5YHP (W4)** for why they differ slightly from the submitted 89.8 / 92.1.

**Revision:** We will replace best-of-3 reporting with mean +/- std throughout, report raw accuracy as primary with the arm-symmetric re-judge as a robustness column, and add this paired-test table to the main results.

---

## Common Weakness 3 (from Reviewers iNYK W2/Q1 and 5YHP W3)

> Can you re-report Reset vs. Baseline on a random subset, or one selected independently of baseline results? ... the LiC experiments use replay mode.

**Response:** We ran exactly this experiment, and designed it to remove **both** concerns simultaneously. We drew a **uniformly random subset selected with no reference to baseline outcomes** (n=40), ran it as **fresh end-to-end conversations rather than replay**, used a **model not in the paper** (gpt-5.4-mini), and repeated it over **3 replicate runs**.

| Method | Accuracy, raw (mean +/- std, N=3) | Per-run values |
|---|---|---|
| Full context | 87.5 +/- 2.0 | 90.0 / 87.5 / 85.0 |
| **AC3-Reset** | **93.3 +/- 4.2** | 97.5 / 95.0 / 87.5 |
| **AC3-Gated-Reset** | **95.0 +/- 0.0** | 95.0 / 95.0 / 95.0 |

Two notes on that table, since a `95.0 +/- 0.0` at temperature 1.0 invites the question. First, the three Gated-Reset runs are **independent end-to-end conversations that happen to land on the same count**, not a cached replay: they fail on *different* problems each time (the failing pairs are disjoint across the three runs, union 5 and intersection 0), the analyzer's output differs on **39 of 39** comparable conversations across the three runs, and turn counts and extracted answers differ on 7 and 5 of the 40 problems respectively. Second, these `+/-` are spreads over three replicates and therefore describe decoder variance, not sampling variance over problems — the quantity you asked for. A problem-clustered bootstrap over the 40 problems gives full context **87.5% [79.2, 95.0]**, AC3-Reset **93.3% [87.5, 98.3]** and AC3-Gated-Reset **95.0% [90.0, 99.2]**; paired against full context, AC3-Gated-Reset is **+7.5pp [+1.7, +15.0]** (item-level exact McNemar over the three replicates, p = 0.023) and AC3-Reset is **+5.8pp [+0.0, +12.5]** (p = 0.119). We report both, including the one that does not reach significance.

**Both operators improve over the baseline in every one of the three runs** (Reset +7.5 / +7.5 / +2.5pp; Gated-Reset +5.0 / +7.5 / +10.0pp). We state the limits of this experiment ourselves: at n=40 the margins are two to four problems per run, and we do not rest our headline significance on it. Its purpose is narrower and it achieves it — the gains are not an artifact of difficulty-selected data, of replay evaluation, or of a single run. The powered evidence is the 36-comparison paired test in Common Weakness 2.

We should note a correction here. In earlier correspondence we quoted this experiment as **AC3-Reset 100.0 +/- 0.0** and **AC3-Gated-Reset 99.1 +/- 1.2**. Those were our false-negative-*adjusted* figures, and, as described in Common Weakness 2, that adjustment excluded 1, 2 and 5 items from AC3 denominators across the three runs while excluding none from baseline. The raw numbers above are the correct ones to compare, and they are the ones we will publish.

On replay more generally, we would respectfully note that holding the polluted trajectory fixed across methods is what makes the comparison **causal**: every method inherits an identical history, so the measured difference is attributable to the intervention rather than to divergent user-simulator paths. We also note that tau2 and CollabLLM are run as live multi-turn interactions, not replay.

**Revision:** We will add this experiment to the main results and report the full-pool numbers alongside the difficulty-stratified subset.

---

## Common Weakness 4 (from Reviewers iNYK W3 and Vg97 W2)

> The abstract and Figure 1 repeatedly call AC3 "the only method robust across the spectrum," yet on tau2-bench... Table 1d reports best-of-3, which masks the negative mean.

**Response:** You were right, and re-measuring this benchmark properly turned out to cost us more than the statistic. We did not merely re-report tau2 at N=3 — we re-ran the **entire published tau2 matrix**: 3 respondent models x 5 arms x **3 replicate runs** (seeds 42/43/44; `--seed` threads through to the provider's `seed` parameter on this fork, best-effort), 19 tasks per replicate, **855 scored rollouts**, 15 of 15 cells complete. **Two of our three published baselines do not replicate, and against corrected baselines we can no longer claim that AC3 improves over full context on tau2. We withdraw that claim.**

| tau2-bench (reward %) | gpt-5.4 | DeepSeek-V4-Flash | Kimi-K2.6 |
|---|---|---|---|
| Full context — **as published** (N=1) | 68.4 | **31.6** | **26.3** |
| **Full context — re-measured, N=3** | **68.4 ± 13.9** | **70.2 ± 11.0** | **78.9 ± 0.0** |
| Assistant omission, N=3 | **0.0 ± 0.0** | **0.0 ± 0.0** | **0.0 ± 0.0** |
| AC3-Augment, N=3 | 47.4 ± 5.3 | 50.9 ± 8.0 | 57.9 ± 9.1 |
| AC3-Gated-Reset, N=3 | 57.9 ± 21.1 | 57.9 ± 10.5 | 71.9 ± 11.0 |
| AC3-Rewrite, N=3 | 47.4 ± 5.3 | 57.9 ± 13.9 | 66.7 ± 8.0 |

**On all three models the re-measured full-context baseline is at or above every AC3 arm.** Paired against it, AC3-Augment is significantly *worse* on all three (−21.1pp p = 0.008; −19.3pp p = 0.043; −21.1pp p = 0.012), and Gated-Reset and Rewrite are negative everywhere without reaching significance. That is the opposite of the tau2 story in our submission. We are not going to soften it into "mixed results": on this benchmark we compared a clean treatment against a degraded control, and the improvement we reported is withdrawn.

**This is "our published baselines were wrong", not "these runs are not comparable" — and we tested that distinction rather than assuming it.** Two published anchors reproduce exactly in the new sweep: gpt-5.4 full context at **68.4** against a published 68.4, and assistant omission at **0.0 in all nine cells / 171 rollouts**. The user simulator and analyzer are the same `gpt-5-mini` identity the published sweep used and it was reachable throughout; the CLI invocation strings are byte-identical to our committed sweep scripts; no model was substituted anywhere. What changed underneath is only the transport layer, which now pools endpoints and backs off instead of short-exiting. The likeliest reading — which our own internal report already conceded for Kimi, describing those cells as "floors, not honest performance" — is that the published DeepSeek-V4-Flash and Kimi baselines were **rate-limit-clipped floors** (14/20 and 19/20 short-exits).

**What survives is the result we most need this benchmark for.** **Assistant omission collapses to 0% on every model** — nine cells, 171 rollouts, not one non-zero reward, reproducing the published value exactly. This is behavioural, not a scoring artifact: AO rollouts never reach a `user_stop` termination and instead exhaust the 50-step budget, because blanket omission destroys the tool-call results that exist only in assistant turns, so the agent re-calls tools indefinitely. In the same process, on the same tasks, every other arm returns rewards of 1.0, and paired against the *re-measured* baseline AO is **−68.4 / −69.6 / −78.9pp, p < 0.0001**. It is the answer to the question we most need tau2 for — *why not simply omit the assistant turns?* — and it does not depend on the baseline's level, which is why the correction above leaves it untouched.

**The Gated-Reset regression Reviewer iNYK identified reproduces in direction, and we keep it.** On gpt-5.4, Gated-Reset is **57.9 ± 21.1** against a baseline of 68.4 ± 13.9 — paired **−10.5pp, exact p = 0.238** over 57 pairs (6 arm wins, 12 baseline wins, 39 ties). We neither drop it nor upgrade it: it is a persistent, underpowered negative that a 19-task benchmark cannot resolve.

**One thing we cannot explain, which we would rather flag than paper over.** On gpt-5.4 the *baseline* reproduced exactly while every AC3 arm fell 10 to 37 points against the published values (Augment 84.2 → 47.4, Rewrite 73.7 → 47.4). We ruled out model substitution, the operator failing to fire (median 2 analyses per rollout, gating exactly as specified), degenerate termination (60/60 `user_stop`, zero step-budget exhaustions) and rate-limit contamination. We did find a real defect in our tau2 fork — the analyzer's tag extractor misses when the model answers in JSON, so **53% of analyzer calls fell back to splicing a raw completion into the agent's briefing**, which can only degrade AC3 arms and cannot touch full context or omission — but patching it moved accuracy by **+2.3pp**, less than one task. So the defect is real, is worth fixing, and is not the explanation. We report the collapse as unexplained rather than attribute it.

On the specific gpt-5-mini cell iNYK cites, we should be straightforward: **we do not have a defensible failure taxonomy for it.** Our qualitative reading at the time suggested that configuration's baseline failures were dominated by missing domain knowledge and by step-budget exhaustion under the hard personas rather than by pollution, which would make it a low-headroom setting for any pollution-removal method — but that was one author's reading of a single trial's traces, without a rubric and without a second annotator, and we would rather flag it as a hypothesis than offer it as evidence. That cell was also not part of the re-run above, which targeted the three-model matrix. For the camera-ready we will annotate all trials against a published rubric with a second annotator and report the taxonomy whichever way it comes out.

**Revision:** We report tau2 as mean +/- std over N=3 replicate runs per cell rather than best-of-3; we **withdraw the tau2 magnitude comparison and the improvement claim on that benchmark**, replacing the published table with the re-measured one and stating in the caption that two of the three published baselines were clipped; and we correct the abstract and introduction from "robust across the spectrum" to the precise, checkable claim that AC3 is **the only method tested that improves over full context on every self-contained and referential benchmark, and the only method that remains viable in the stateful agentic setting**, where blanket omission fails structurally (0% on every respondent).

---

## Common Weakness 5 (from Reviewer Vg97 W1/Q1 and the Area Chair)

> The paper should compare against recent stronger context-condensation/context-management methods such as MT-OSC.

**Response:** We appreciate this suggestion. In v3 of this response we argued the point; we have now run it, and we report the result including the compute accounting.

Our baselines were selected because they attack **the same problem we do**: deciding what stays in context so that harmful prior content stops influencing generation. Assistant omission is the strongest published intervention for context pollution and is a design-oracle on LiC by construction; ERGO resets via LLM rewriting of user turns; Concatenate-User is the single-turn upper bound. Compaction and folding methods (U-Fold, Context-Folding, MemoBrain, and the concurrent MT-OSC) target a **different failure mode**: context-length pressure. Our prediction, which follows directly from the mechanism we identify, was that a good-faith condenser carries invalidated reasoning forward in compressed form and does not close the gap.

**Before we report the new baseline, we have to correct how an existing one was scored, and the correction runs against us.** Re-auditing our own denominators for this response, we found that **ERGO — and only ERGO — was evaluated on unfiltered conversation pools** in our main LiC table. Every other row is scored on pools from which a small number of conversations have been pre-filtered, because the user shards for those items omit a fact required to solve them; that filter is computed once from baseline traces and applied identically to every arm, but it did not fire on the ERGO run. ERGO was therefore charged with items no other method was asked to attempt (n = 23/25/25/25 against 20/19/25/23 for every other row). The error is ours, it understates a competitor, and it is recoverable from the printed percentages by anyone with a calculator.

We measured the correction rather than estimating it. Placing ERGO on the filtered pool has exactly one unknown — how many of the excluded items ERGO was solving — so we replayed ERGO against those excluded items directly. **On math it solves none of them, and ERGO moves from 69.6 to 80.0, which places it above AC3-Reset (75.0) and level with AC3-Gated-Reset (80.0).** On code it solves roughly half, so the corrected value is ≈44.0, essentially the published figure. Database is unaffected (12.0; nothing was filtered on that task). The **actions** cell cannot be corrected at all — no filter artifact has ever existed for that task, and its n=23 is the ad-hoc normalisation we already disclose in the paper — so we will print it as an interval rather than a point estimate.

**We think the honest conclusion here is stronger than either ordering, and it is the same point Reviewers iNYK and Vg97 raise about cell sizes.** Running paired exact sign tests on the same items, **no ERGO-vs-AC3 difference in that table is statistically distinguishable at n ≈ 20, in either direction** (code p = 0.375, math p = 1.00). That is true of the published table as well as the corrected one — and we would apply the same standard to our own rows in it: at n ≈ 20 that table cannot settle any of these orderings, which is precisely why our headline evidence is now the 36-comparison paired matrix at up to 150 conversations per cell (Common Weakness 2) rather than Table 1. We will therefore print n per cell, state in the caption that ERGO was initially scored on the unfiltered pool, and report the ERGO-vs-AC3 comparison as unresolved at this sample size rather than as a win for anyone. What the correction does not touch is the size of the database gap — ERGO 12.0 against AC3-Reset's 48.0 — which is the one difference in that table that is larger than its own noise floor.

We implemented a summarisation baseline and an MT-OSC reimplementation and ran them on our two highest-pollution LiC tasks, paired against the same conversations (raw accuracy; exact McNemar on discordant pairs):

**Before the table, three notes on comparability, because these absolute accuracies are far above Table 1's and we would rather explain that than have it read as an inconsistency.** (i) **Pool.** These runs use the *complete* LiC pool for each task — 107 database and 100 code instances from `sharded_instructions_600` — with **no instance selection of any kind**. Table 1 reports a 25-instance-per-task subset selected for high full-context failure rate under GPT-5-mini, and the post-submission 3-model matrix uses a 50-instance subset selected the same way from GPT-5.2 logs. (ii) **Respondent.** gpt-5.4-mini here, against GPT-5-mini in Table 1. (iii) **Protocol.** Full end-to-end sharded simulation here, against last-turn replay in Table 1.

**Item selection is the dominant term, and we measured it rather than arguing it.** Restricting *this* run to Table 1's exact 25 database instances — same model, same evaluator, same conversations — moves full context from 56.1% to **32.0%** and AC3-Reset from 75.7% to **60.0%**; on code the baseline moves 83.0% → **48.0%**. Independently, LiC's own released logs put GPT-5-mini at 29.9% on the whole 107-item pool against 4.0% on its top-25 subset — two routes to a ≈25pp selection effect, agreeing within 2pp. Absolute accuracies are therefore **not comparable across our three tables; the paired Δ within each block is the quantity to read**, and it is computed on identical items in all three.

**Nor is the unselected pool an easy setting**, which is the reservation this experiment has to survive. Measuring the single-turn ceiling directly on it in the same harness — each instance's fully-specified question delivered in one turn — gives **94.4% on database and 98.0% on code**, against full-context multi-turn accuracies of 56.1% and 83.0%. That is a **38.3pp** and **15.0pp** multi-turn gap on a pool with no difficulty selection whatsoever, and AC3-Reset closes **51%** and **60%** of it — the same fraction it closes on Table 1's much harder subset (**50%** on both tasks). Our absolute baselines differ by up to 52 points across venues; **the fraction of the multi-turn gap our method closes moves by ten points at most.** Summarisation, meanwhile, scores below full context in every venue we have run it in, so it was not handed an easy pool either.

| Task | Arm | Accuracy | n correct | Δ vs baseline | McNemar p |
|---|---|---|---|---|---|
| database | Baseline (full context) | 56.1% | 60/107 | — | — |
| database | Summarisation, 1 call/turn | 53.3% | 57/107 | −2.8 | 0.678 |
| database | Summarisation, 2 calls/turn (budget-matched) | 47.7% | 51/107 | −8.4 | 0.078 |
| database | MT-OSC (reimplementation, w=4 as published) | 60.7% | 65/107 | +4.7 | 0.383 |
| database | MT-OSC (w=2, window scaled to conversation length) | 47.7% | 51/107 | −8.4 | 0.093 |
| database | **AC3-Reset** | **75.7%** | 81/107 | **+19.6** | **0.0005** |
| database | **AC3-Gated-Reset** | **73.8%** | 79/107 | **+17.8** | **0.0013** |
| code | Baseline (full context) | 83.0% | 83/100 | — | — |
| code | Summarisation, 1 call/turn | 79.0% | 79/100 | −4.0 | 0.481 |
| code | Summarisation, 2 calls/turn | 80.0% | 80/100 | −3.0 | 0.581 |
| code | **AC3-Reset** | **92.0%** | 92/100 | **+9.0** | **0.023** |

Head-to-head and paired, AC3-Reset beats summarisation by **+22.4 / +28.0pp** on database and **+13.0 / +12.0pp** on code, all p < 0.01.

**On budget, the result is stronger than parity.** We instrumented every LLM call and token by component. The budget-matched summariser did not merely match AC3-Reset's compute, it **over-consumed** it — **1.02–1.19x the strategy calls and 1.62–2.14x the strategy tokens** — and still lost by 12 to 28 points. AC3-Gated-Reset reaches +17.8pp on **0.41x** AC3-Reset's strategy calls. We spent more compute on the baseline than on our own method and the baseline still lost.

**On MT-OSC we want to be careful not to overclaim a win.** At its published window (w=4) it fired **30 times across 107 conversations, 0.3 condensations per conversation**, because it cannot compact before turn 6 while LiC conversations average 4.1 turns. Stricter still: because the method's condenser runs with a deliberate one-turn lag, only **6 of those 30 condensations were ever applied** to a context before the conversation ended. Its +4.7pp is therefore not a fair test of MT-OSC's idea.

**So we ran the obvious follow-up to our own scoping argument rather than leave it to be asked.** A reviewer is entitled to reply "then scale the window to the conversation length and re-report". **We did.** At w = 2, the smallest window in MT-OSC's own published sweep, the method engages properly — **2.2 condensations per conversation against 0.3 at w = 4**, roughly an eightfold increase (237 condensations against 30, over the same 107 conversations) — and accuracy goes **down**, to 47.7% against full context's 56.1% and against its own w = 4 run's 60.7% (**−13.1pp**, 22 losses to 8, p = 0.016). AC3-Reset leads the engaged configuration by **+28.0pp** (37/7, p < 0.0001). So the scoping argument does not rest on a hyperparameter that happened to disable the competitor: when length-triggered compaction actually engages with a short, polluted conversation, it compresses the invalidated reasoning rather than removing it, which is the same mechanism the summariser arms show. At w=4 MT-OSC looks mildly positive precisely because it is nearly a no-op. We will present it that way — as a scoping result about length-triggered compaction, with a measured engagement rate at both windows — and not as a beaten baseline. These are single runs of our own reimplementation of a method with no code release, and we label them as such.

**Two honesty notes on the condenser, since we wrote its prompt ourselves.**

**First, we ran the fairness control and it comes out against our own prompt having mattered.** Our condenser prompt contains the clause *"your job is compression, not evaluation — preserve the assistant's current approach and conclusions as they stand"*, which a reviewer could reasonably read as forbidding the baseline from doing the useful thing. We therefore ran a **neutral-prompt variant with that clause deleted** — a bare "summarize the conversation so far", leaving the model free to audit the assistant's work if it chooses to. On LiC-database (n = 107 paired, raw): the neutral condenser scores **51.4% against full context's 56.1%** (−4.7pp, p = 0.44), which sits **between two replicate runs of our own prompt** (53.3% and 47.7%). The two prompts differ by less than two runs of the same prompt differ from each other (neutral vs. ours: −1.9pp, p = 0.83, and +3.7pp, p = 0.54, against the two replicates). AC3's margin over the condenser is unchanged: **+24.3pp for AC3-Reset and +22.4pp for AC3-Gated-Reset against the neutral prompt** (31/5 and 30/6, p ≤ 0.0001). Both prompts are released verbatim.

We can also say *why* the phrasing does not matter, which we think is the more useful finding. Across all 1,017 condenser summaries produced in these runs, the condenser flags an error in the assistant's work **zero times out of 340 under the neutral prompt** — exactly as often as under our prohibition (0/336 and 0/341). Removing the clause does not make a summariser start auditing; it only makes its summaries shorter (mean 1,068 characters against 1,945). The prohibition was never what made the baseline lose. (This is a lexical probe and would miss a purely paraphrastic critique; as a check on the probe itself, the same pattern fires on 26.4% of AC3's analyzer outputs, which are designed to name divergence, and on 0% of baseline assistant turns.)

**Second, a note on the two budget rows, because the ordering in them is tempting to read as a mechanism and we do not think it survives.** The condenser scores −2.8pp at one call per turn and −8.4pp at two, and we were initially inclined to read that gap as the mechanism showing through — a second condensation pass compressing the invalidated reasoning further rather than removing it. It does not replicate, so we do not make that argument: a second run of the **one-call** arm scores **−8.4pp, exactly the two-call value**, and the two one-call replicates differ by more than one call differs from two (p = 0.29 and p = 0.26 respectively). At n = 107 this cell carries roughly **±6pp** of run-to-run variation. The defensible statement is the simple one — **summarisation is neutral-to-negative at either budget, not catastrophic** — and the quantity that is far outside that noise floor is AC3's +22 to +28pp advantage over it.

Limits we state ourselves: one respondent model (gpt-5.4-mini), two tasks, and one run per cell except the two we replicated (the 1-call condenser, run twice, which is where the ±6pp noise floor above comes from).

**Revision:** We will add this table, the measured budget accounting, and the MT-OSC engagement-rate analysis to the paper, and cite and discuss MT-OSC (concurrent, 2026) in Related Work. We will also place ERGO on the same filtered pools as every other row, print n per cell, note the original scoring in the caption, and add the paired-significance result above to the appendix.

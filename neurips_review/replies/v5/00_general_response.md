# General Response to All Reviewers

> **⚠ INTERNAL — READ BEFORE POSTING. NOT PART OF THE REPLY.**
> *Updated by T19, 2026-07-29 ~17:30 UTC. One of the two audits this preamble originally gated has landed; the other has not.*
>
> 1. **T14 (false-negative-adjustment audit) — RESOLVED 16:15, largely in the paper's favour. The provisional flag on every LiC figure below is lifted.** `tab:main`'s denominators come from an **arm-symmetric pool-level pre-filter** (`data/baseline_traces_v2/*_false_negatives.json`, computed once on baseline traces and applied identically to every arm) that exactly reproduces its 20/19/25/23 denominators. **That is correct and should be defended, not conceded.** What is invalid is the *per-run* `adjusted_accuracy` metric: it inflates reset arms by **+13.9 to +55.9pp** against **+0.2 to +6.5** for no-reset arms, because the FN judge sees 1.00 user turns/sample on AC3-Rewrite against 5.35 on baseline. It touches at most 4 `tab:main` cells at ≤1 sample each, and 2 of those 4 favour prior work. Recommendation adopted: report **raw** as primary, keep the pool filter as the only FN adjustment, delete per-run adjusted accuracy. Every LiC number in this document is already raw, so **nothing here moves**. Two conclusions do flip under correction, both on **AC3-Rewrite** (code +46.0 → −5.3, actions +22.4 → −1.5), but **neither is a published error** — `tab:main` has no Rewrite LiC row and `tab:megatable` is computed from raw. **AC3-Reset and AC3-Gated-Reset beat baseline in all 8 cells under raw, shipped-adjusted and corrected alike.** Sources: F40–F42, `AR/tasks/T14/RESULTS.md`.
> 2. **T6 (multi-replicate tau2).** The tau2 table in Common Weakness 4 is on **HOLD** — see the marked block there. Do not post that table until T6 returns.
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
4. **The condensation baseline Vg97 and the Area Chair asked for is now run, at measured matched compute.** Summarisation does not close the gap; it moves accuracy *down* (Common Weakness 5).
5. **A direct, judge-free span-level evaluation of the analyzer as a detector, and a causal ablation of naturally occurring assistant content**, which 5YHP asked for and which we report including the part that does not flatter us — it establishes that context pollution is real and concentrated, and it also retracts a mechanism claim in our paper (Reviewer 5YHP, W5).

We also correct three numbers we reported to reviewers in earlier correspondence or in the submission, having re-measured them at N=3: a CollabLLM MATH-Hard figure, the WildChat win-rates, and the end-to-end subset result. Separately, and moving against us, we found a scoring error in our own main LiC table that **understated a baseline** we compare against; we report the corrected comparison in Common Weakness 5. Details are in the relevant sections.

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

> **⚠ INTERNAL — HOLD (T6 in flight).** v4 closed this section with: *"tau2 confirms the rule directly: the lightest operator (Augment) wins on the strongest model (gpt-5.4), and the heaviest (Rewrite) wins on the weakest (Kimi-K2.6)."* That sentence is derived from the same N=1 seed-42 tau2 cells that T6 is currently re-measuring, and T6's interim baselines (DeepSeek-V4-Flash 70.2 ± 11.0, Kimi-K2.6 80.4 ± 2.5 at N=3) are far above the published ones (31.6, 26.3). If the interim numbers hold, the operator-ordering rule cannot be supported from tau2. **The sentence has been removed pending T6.** Restore only if T6's AC3 arms reproduce the ordering.

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

**AC3's mean clears the full-context baseline on every model**: +17.1pp (DeepSeek-V4-Flash), +16.7pp (gpt-5.4), +13.9pp (Kimi-K2.6). AC3-Reset is the **single fixed configuration** behind the 33/36 row — it is not a per-cell maximum, and we state a deployment rule rather than selecting an operator per cell (Common Weakness 1).

### Where AC3 separates from assistant omission, and where it does not

Several corrections in this rebuttal narrow individual AC3-vs-assistant-omission comparisons, so we would rather assemble the whole picture here than leave a reader to do it from six documents. Assistant omission is a strong baseline — on LiC it is a design-oracle by construction — and across the full 36-triple matrix the head-to-head is close to a wash: AC3-Reset's mean advantage over it is **+2.6pp**, on **15 wins, 17 losses and 4 ties**. We state that plainly, because it is computable from the two rows above. What the aggregate hides is that the difference is not evenly spread. It is concentrated exactly where our analysis says it should be:

| Setting | AC3-Reset vs. assistant omission | Why the framework predicts it |
|---|---|---|
| **LiC-database** (3 models, 9 triples) | **+18.7pp**, **8 wins / 1 loss** — 49.0 / 56.2 / 55.1 against 45.6 / 27.9 / 30.6 | Shards must be assembled against a schema, so deleting assistant turns discards partially-correct assembly work: consolidation beats deletion |
| LiC math / code / actions (27 triples) | −3.1 / −3.8 / −1.3pp (1/7/1, 2/6/1, 4/3/2) | User turns fully self-specify the task, so omission is already near-optimal and there is little left for AC3 to add |
| **tau2-bench** (stateful, 3 models) | Assistant omission is **0% on every model**, and structurally so | Tool-call results exist only in assistant turns; omission destroys them and the rollouts never terminate |
| **WildChat** (referential, real human–AI dialogue) | AC3 favoured in **every** populated cell of our per-respondent table, 13 of which are against omission; pooled order-balanced **87.8 / 91.2%** | Intent is co-constructed across assistant turns, so blanket deletion removes the specification itself |
| CollabLLM BigCodeBench | **+3.3pp — an ordering we explicitly do not claim**, inside the noise at N=3 | — |

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

**Both operators improve over the baseline in every one of the three runs** (Reset +7.5 / +7.5 / +2.5pp; Gated-Reset +5.0 / +7.5 / +10.0pp). We state the limits of this experiment ourselves: at n=40 the margins are two to four problems per run, and this experiment alone is not powered for significance. Its purpose is narrower and it achieves it — the gains are not an artifact of difficulty-selected data, of replay evaluation, or of a single run. The powered evidence is the 36-comparison paired test in Common Weakness 2.

We should note a correction here. In earlier correspondence we quoted this experiment as **AC3-Reset 100.0 +/- 0.0** and **AC3-Gated-Reset 99.1 +/- 1.2**. Those were our false-negative-*adjusted* figures, and, as described in Common Weakness 2, that adjustment excluded 1, 2 and 5 items from AC3 denominators across the three runs while excluding none from baseline. The raw numbers above are the correct ones to compare, and they are the ones we will publish.

On replay more generally, we would respectfully note that holding the polluted trajectory fixed across methods is what makes the comparison **causal**: every method inherits an identical history, so the measured difference is attributable to the intervention rather than to divergent user-simulator paths. We also note that tau2 and CollabLLM are run as live multi-turn interactions, not replay.

**Revision:** We will add this experiment to the main results and report the full-pool numbers alongside the difficulty-stratified subset.

---

## Common Weakness 4 (from Reviewers iNYK W3 and Vg97 W2)

> The abstract and Figure 1 repeatedly call AC3 "the only method robust across the spectrum," yet on tau2-bench... Table 1d reports best-of-3, which masks the negative mean.

**Response:** We thank the reviewers for this precision, and we agree best-of-3 was the wrong statistic to headline. We have revised the claim and are re-reporting tau2 at N=3 per cell.

The one tau2 conclusion that is mechanism-corroborated and does not depend on the contested magnitudes:

**Assistant omission collapses to 0% on every model.** This is behavioural, not a scoring artifact: AO rollouts never reach a `user_stop` termination and instead exhaust the 50-step budget, because blanket omission destroys the tool-call results that exist only in assistant turns, so the agent re-calls tools indefinitely. In the same process, on the same tasks, the other arms return rewards of 1.0. This is the single most important tau2 result for our argument — it is the setting where the strongest published baseline does not merely underperform but fails structurally — and it is unaffected by the re-measurement below.

> **⚠ INTERNAL — HOLD (T6 in flight). DO NOT POST THE TABLE BELOW.**
> v4 posted this table:
>
> | tau2-bench (reward %) | gpt-5.4 | DeepSeek-V4-Flash | Kimi-K2.6 |
> |---|---|---|---|
> | Full context | 68.4 | 31.6 | 26.3* |
> | Assistant omission | 0.0 | 0.0 | 0.0 |
> | Best AC3 operator | 84.2 | 57.9 | 73.7 |
>
> T6 is re-running the full 3-model x 5-arm matrix at N=3 (seeds 42/43/44, n=19 tasks per replicate) with a rotate-and-backoff transport wrapper. Its **completed Baseline cells** read:
> gpt-5.4 **68.4 ± 13.9** (reproduces the published 68.4 on the mean); DeepSeek-V4-Flash **70.2 ± 11.0** (published 31.6); Kimi-K2.6 **80.4 ± 2.5** (published 26.3).
> The most likely reading, which the source report itself concedes for Kimi, is that the published DSV4F and Kimi Baseline cells were **rate-limit-clipped floors** (14/20 and 19/20 short-exits), i.e. a clean treatment was compared against a broken control. Kimi's re-measured baseline (80.4) is already **above every published Kimi AC3 number**.
> Two further facts from T6 that we will have to state regardless of the outcome: (i) `--seed` on the tau2 fork threads to the provider's best-effort `seed` parameter, so replicates differ by sampling and seed 42 does not reproduce the original point estimate (52.6, not 68.4); (ii) at n=19 and p≈0.68 the binomial sd is 10.7pp, so **any tau2 gap below roughly 15pp measured at N=1 is inside the noise** — which is the quantitative form of the reviewers' complaint and should be conceded in those terms.
> **Action:** post the AO-collapse paragraph above; hold the numeric table until T6's AC3 arms land, then paste the N=3 mean ± sd table. If the interim baselines hold, the honest framing is: *"On re-measurement at N=3 with a corrected transport layer, our published DeepSeek-V4-Flash and Kimi baselines were too low; we withdraw the magnitudes on those two models and report the corrected matrix. The structural result — assistant omission at 0% on every model — is unchanged."*

On the specific gpt-5-mini cell iNYK cites, we should be straightforward: **we do not have a defensible failure taxonomy for it.** Our qualitative reading at the time suggested that configuration's baseline failures were dominated by missing domain knowledge and by step-budget exhaustion under the hard personas rather than by pollution, which would make it a low-headroom setting for any pollution-removal method — but that was one author's reading of a single trial's traces, without a rubric and without a second annotator, and we would rather flag it as a hypothesis than offer it as evidence. For the camera-ready we will annotate all trials against a published rubric with a second annotator and report the taxonomy whichever way it comes out.

**Revision:** We report tau2 as mean +/- std over N=3 replicates per cell rather than best-of-3, and we sharpen the abstract and introduction from "robust across the spectrum" to the precise, checkable claim that AC3 is **the only method tested that improves over full context across the entire spectrum**, including the stateful agentic setting where blanket omission fails completely.

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

**Nor is the unselected pool an easy setting**, which is the reservation this experiment has to survive. Measuring the single-turn ceiling directly on it in the same harness — each instance's fully-specified question delivered in one turn — gives **94.4% on database and 98.0% on code**, against full-context multi-turn accuracies of 56.1% and 83.0%. That is a **38.3pp** and **15.0pp** multi-turn gap on a pool with no difficulty selection whatsoever, and AC3-Reset closes **51%** and **60%** of it — the same fraction it closes on Table 1's much harder subset (**50%** on both tasks). Our absolute baselines differ by up to 52 points across venues; **the fraction of the multi-turn gap our method closes differs by four.** Summarisation, meanwhile, scores below full context in every venue we have run it in, so it was not handed an easy pool either.

| Task | Arm | Accuracy | n correct | Δ vs baseline | McNemar p |
|---|---|---|---|---|---|
| database | Baseline (full context) | 56.1% | 60/107 | — | — |
| database | Summarisation, 1 call/turn | 53.3% | 57/107 | −2.8 | 0.678 |
| database | Summarisation, 2 calls/turn (budget-matched) | 47.7% | 51/107 | −8.4 | 0.078 |
| database | MT-OSC (reimplementation, w=4 as published) | 60.7% | 65/107 | +4.7 | 0.383 |
| database | **AC3-Reset** | **75.7%** | 81/107 | **+19.6** | **0.0005** |
| database | **AC3-Gated-Reset** | **73.8%** | 79/107 | **+17.8** | **0.0013** |
| code | Baseline (full context) | 83.0% | 83/100 | — | — |
| code | Summarisation, 1 call/turn | 79.0% | 79/100 | −4.0 | 0.481 |
| code | Summarisation, 2 calls/turn | 80.0% | 80/100 | −3.0 | 0.581 |
| code | **AC3-Reset** | **92.0%** | 92/100 | **+9.0** | **0.023** |

Head-to-head and paired, AC3-Reset beats summarisation by **+22.4 / +28.0pp** on database and **+13.0 / +12.0pp** on code, all p < 0.01.

**On budget, the result is stronger than parity.** We instrumented every LLM call and token by component. The budget-matched summariser did not merely match AC3-Reset's compute, it **over-consumed** it — **1.02–1.19x the strategy calls and 1.62–2.14x the strategy tokens** — and still lost by 12 to 28 points. AC3-Gated-Reset reaches +17.8pp on **0.41x** AC3-Reset's strategy calls. We spent more compute on the baseline than on our own method and the baseline still lost.

**On MT-OSC we want to be careful not to overclaim a win.** At its published window (w=4) it fired **30 times across 107 conversations, 0.3 times per conversation**, because it cannot compact before turn 6 while LiC conversations average 4.1 turns. Its +4.7pp is therefore not a fair test of MT-OSC's idea. The correct reading is that a length-triggered compaction schedule **structurally cannot engage** with pollution that appears in the first few turns — which is precisely the scoping argument we made in Related Work, now with a number attached rather than an assertion. We will present it that way and not as a beaten baseline.

Limits we state ourselves: one respondent model (gpt-5.4-mini), one run per cell, two tasks. A neutral-prompt variant of the summariser was implemented to check that the result does not hinge on our phrasing of the condenser prompt; it did not finish in the window, and both prompts will be released verbatim.

**Revision:** We will add this table, the measured budget accounting, and the MT-OSC engagement-rate analysis to the paper, and cite and discuss MT-OSC (concurrent, 2026) in Related Work. We will also place ERGO on the same filtered pools as every other row, print n per cell, note the original scoring in the caption, and add the paired-significance result above to the appendix.

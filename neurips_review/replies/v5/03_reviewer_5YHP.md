# Response to Reviewer 5YHP

We sincerely thank the reviewer for an exceptionally thorough review. Your W5 — evaluate the analyzer directly as a detector — turned out to be the most valuable suggestion we received: we built it, and it changed how we describe our own method. We report it below including the part that does not flatter us.

## Response to Weaknesses

> **W1:** The strongest mechanism relies on an assumption that does not hold in the most important referential settings... the paper convincingly demonstrates that structural exclusion works when user messages independently specify the task, but it does not yet solve the harder problem of accurately separating useful and harmful assistant content when both must be visible.

**Response to W1:** Thank you for this careful reading. We would respectfully suggest that this describes the precise scope of our claim rather than a gap in it, and we can now say so with a measurement rather than an argument.

Our contribution is to identify **when** assistant history can be safely excluded, and to show that the safety condition is an **information-flow constraint rather than a prompting problem**. Where user turns independently specify the task, structural exclusion is both necessary and sufficient, and prompt-level instructions to ignore assistant turns are demonstrably insufficient (Table 5, which you identify as one of the paper's strongest results). Appendix D is our own stress test of the method past its stated condition, which is why we report it at all.

Your framing also implicitly raises a mechanism question we had not tested and should have: is the analyzer *auditing* the conversation, or is it just *re-solving the task* and handing the answer over? We tested it directly, and the answer is partly against us.

We took every analyzer output in the LiC replay matrix (n=547) and checked, per conversation, whether the analyzer's text contains the **verified correct answer**. Then we split the paired AC3-vs-baseline comparison on that label:

| Task | Leak rate (analyzer output verified to contain the correct answer) | Paired gain on the **no-leak** subset |
|---|---|---|
| code | **0%** (0/106) | **+30.2pp** (32.1 → 62.3, n=106, p < 0.0001) |
| database | **1%** (1/147) | **+26.0pp** (22.6 → 48.6, n=146, p < 0.0001) |
| actions | 2% (3/150) | +6.8pp (n=147, p = 0.099) |
| **math** | **38%** (54/144) | **−2.6pp** (68.8 → 66.2, n=77, p = 0.815) |
| math + code + database pooled | 11% overall | **+20.7pp** [+14.8, +25.3], n=329, p < 0.0001 |

**We concede math outright.** On math the analyzer does frequently derive the gold answer, and math's entire +9.7pp gain sits on the leaking subset; on the leak-free subset it is −2.6pp. We think the reason is principled rather than embarrassing — on grade-school word problems, to say "your total of 3,270 is wrong because year 9 contributes 0" you must compute the correct total, so auditing and solving are not separable on that task — but it is a concession and we will state it as one in the paper.

**On code and database the auditing interpretation holds cleanly.** Code has *zero* verified leaks across 106 conversations and still gains +30.2pp. AC3-Gated-Reset reproduces the pooled effect (+19.6pp on 311 leak-free conversations). Under a looser judge-based leak label the no-leak gain is *larger* than the leak gain (+24.5 vs +17.3pp), so both label definitions agree.

Caveats we state ourselves: this conditions on a post-treatment variable, and the analyzer leaks on easier items (baseline accuracy is 36.5% on the no-leak subset against 75.0% on the leaking one), so the *between*-stratum contrast is not causal even though the within-stratum paired test is valid; single respondent model; one run per cell. On math we validated the detector by hand — the precision of the no-leak label is 29/32, with all three errors on math and 24/24 correct on database, code and actions.

Structural exclusion is also **not the only mechanism AC3 provides**, and referential settings are not left unaddressed. The operator family handles them, and we have direct evidence in those settings rather than extrapolation from LiC:

* On **tau2-bench**, where state exists only in assistant turns, blanket omission scores **0% on all three models**, and we can now show this is behavioural rather than a scoring artifact: AO rollouts never terminate naturally, they exhaust the step budget, because omission destroys tool-call results that exist only in assistant turns.
* On **WildChat** (real human-AI dialogue), AC3 wins **87.8 +/- 2.1%** (Reset) and **91.2 +/- 2.1%** (Augment) of pairwise comparisons against assistant omission, under a full order-balanced re-judge with cross-family judge agreement (W4 below).

**Revision:** We will state this scope explicitly in Section 3, add the leakage analysis as its own subsection, and concede the math case there.

---

> **W2:** The evaluated system is not a single fixed method across benchmarks.

**Response to W2:** Please see **Common Weakness 1** in the General Response. We now demonstrate rather than assert this: the same four operators run across 3 respondent models x 4 LiC tasks, plus CollabLLM, WildChat, and tau2, with no per-benchmark tuning. We also swapped the analyzer across five models from four families with the respondent held fixed; every analyzer gives a positive, individually significant gain (+12.9 to +39.9pp), so the shared component behaves as a shared component (see our reply to Vg97, Q3). The component table there separates the essential parts from the single tunable knob.

---

> **W3:** The LiC evidence is limited by small samples, replay evaluation, and mostly single-run results... The results should therefore be interpreted as final-turn recovery experiments rather than end-to-end multi-turn improvements.

**Response to W3:** Please see **Common Weakness 2** (scale and paired significance) and **Common Weakness 3** (the new unbiased, end-to-end, 3-replicate experiment).

On replay specifically, we would offer a defence of the design. Holding the polluted trajectory fixed across methods is what makes the comparison **causal**: every method inherits an identical history, so the measured difference is attributable to the intervention rather than to divergent user-simulator paths, which would otherwise confound the intervention with trajectory drift.

That said, your point that end-to-end deployment deserves its own evidence is well taken, so we ran it. On a uniformly random subset (n=40) in **fresh end-to-end conversations** with a new model, over 3 replicate runs, raw accuracy: full context **87.5 +/- 2.0**, AC3-Reset **93.3 +/- 4.2**, AC3-Gated-Reset **95.0 +/- 0.0**, with both operators ahead in every run. We are explicit that at n=40 this experiment is not individually powered; it rules out subset selection, replay and single-run artifacts, and the powered evidence is the 36-comparison paired test. (We had earlier quoted AC3-Reset at 100.0 +/- 0.0 here; that was our false-negative-*adjusted* metric, which excluded 1, 2 and 5 items from AC3's denominator across the three runs and none from baseline's. The raw figures above are the correct comparison — see **Common Weakness 3**.)

We also note that tau2 and CollabLLM are already run as live multi-turn interactions rather than replay.

---

> **W4:** On CollabLLM, AC3 Rewrite is below assistant omission on MATH-Hard and tied with assistant omission on BigCodeBench... BigCodeBench cannot be evaluated with its normal executable tests... The WildChat results... rely on an LLM judge instead of direct task success.

**Response to W4:** Thank you for the close reading. This weakness produced two corrections on our side and one result that came out stronger than we claimed.

**CollabLLM.** The comparison you describe was a user-simulator artifact: the simulator used for those runs failed to communicate the task specification, which suppressed every method and inverted the comparison. We have now re-run the corrected comparison at **3 replicate runs per cell** rather than the single run we previously quoted:

| CollabLLM (competent user simulator, n=20 problems) | Full context | Assistant omission | **AC3** |
|---|---|---|---|
| MATH-Hard | 91.7 +/- 5.8 | 90.0 † | **91.7 +/- 7.6** (Augment) |
| BigCodeBench | 6.7 +/- 5.8 | 15.0 † | **21.7 +/- 5.8** (Reset) |

† assistant-omission cells are single runs and were not re-replicated; treat them accordingly.

**We correct a number we previously gave you.** We had reported AC3-Augment at **100** on MATH-Hard. At N=3 that does not replicate: it is the top of the range, not its centre. AC3-Augment and full context come out **exactly tied** — identical means (91.7 vs 91.7) and identical per-problem totals (55/60 each), with a per-replicate delta of 0.0 +/- 8.7pp. MATH-Hard is near ceiling here, with 15 of 20 problems solved by both arms in every replicate, so a 20-problem draw resolves about five problems' worth of decoding noise. The correct statement is that on MATH-Hard AC3-Augment **matches** full context. That still answers the regression you identified — no arm degrades — but it does **not** support a claimed improvement, and we will not claim one.

**BigCodeBench came out stronger and we now have it at N=3.** AC3-Reset 21.7 +/- 5.8 against full context 6.7 +/- 5.8: **+15pp in every one of three replicates, 3/3 wins**, solving 9 problem-instances that full context never solves once while losing none. It also reproduces on a **fully disjoint** 20-problem draw with zero overlap (Reset 3/20 vs. full context 1/20), which we consider better evidence than three replicates of one draw. At n=20 every cell quantises in 5pp steps, so we will quote this as "roughly 1 in 5 problems, plus or minus one problem" rather than as a bare percentage.

**On BigCodeBench evaluation, we owe you a correction in your favour.** We previously told you that executable tests were unavailable on this harness. That was wrong: the CollabLLM BigCodeBench path scores by **actual test execution** (BigCodeBench's own `untrusted_check`), not by an LLM judge, and the numbers above are execution-based pass rates. What is true, and worth reporting, is that those pass rates are **sensitive to the scoring environment**: a missing plotting library causes BigCodeBench's sandbox guard to abort every test subprocess while the harness silently records 0.0, which produced one spurious 0/20 cell in our own re-runs. We therefore re-scored every cell offline in a single unified environment from the stored extractions, with a canonical-solution pre-flight (19/20 of the reference solutions pass; the one failure is never solved by either arm). We will report the environment specification alongside the numbers, and we recommend the same practice for anyone reporting BigCodeBench.

**WildChat.** You were right that an LLM judge needs auditing, so we re-judged the entire comparison — 1,824 judgements, zero failures — in both presentation orders, with three judges from three families, plus positive controls.

* **Position bias is real and we report the corrected numbers.** The headline judge prefers the second-presented response (AC3 wins 92.3% shown second vs. 86.7% shown first over 452 pairs; of 44 order-discordant pairs, 32 flip toward the second slot and 8 toward the first, exact binomial p = 1.8e-4). The other two judges lean the *opposite* way, so this is a per-model idiosyncrasy rather than a prompt artifact. Our judging code already randomises A/B assignment 50/50 on every call, so the published estimate is unbiased for the order-balanced quantity in expectation; nevertheless we now report the order-balanced values: **AC3-Reset 87.8 +/- 2.1** (submitted 89.8 +/- 1.4) and **AC3-Augment 91.2 +/- 2.1** (submitted 92.1 +/- 1.3). Augment's submitted value sits inside a 200-draw resimulation interval; Reset's sits about 0.5pp outside it, so we adopt the corrected numbers rather than defend the originals.
* **Cross-family agreement holds.** On a frozen 160-pair subset in matched presentation: the headline judge agrees with DeepSeek-V4-Flash 87.5% and with Kimi-K2.6 88.8% raw. Cohen's kappa is 0.45–0.51, which is depressed by the ~90% marginal (the kappa paradox), so we also report the chance-corrected statistics appropriate to that regime: **PABAK 0.79–0.83 and Gwet's AC1 0.84–0.87**. Each judge's own order-balanced AC3 win-rate is 88.8 / 85.6 / 85.3%, a maximum spread of 3.5pp. Under a deliberately punitive rule — a pair counts as an AC3 win only if at least 2 of 3 judges pick AC3 in **both** orders — the win-rate is still **82.5%**.
* **Self-consistency and controls.** Repeating an identical prompt in an identical order gives 96.9% agreement (kappa 0.810), materially higher than the 90.3% swap-consistency, which attributes most judge instability to presentation order rather than to sampling. Against a degraded copy of a real response, the three judges correctly prefer the intact response 39/40, 36/40 and 40/40, symmetrically across orders.
* One honest disclosure: our judge does **not** run at temperature 0 despite the request, because the provider overrides it to 1.0 for this model family. The 96.9% self-consistency figure is the measurement that replaces any determinism claim.

**Revision:** We will report the corrected CollabLLM numbers at N=3, correct our characterisation of BigCodeBench scoring and specify the scoring environment, report the order-balanced WildChat numbers with the judge-agreement and position-bias analysis in an appendix, persist the presentation-order assignment in our judging code, and footnote the per-method sample counts, which differ because each method is evaluated against its own assistant-omission failure pool.

---

> **W5:** The analyzer is not directly evaluated as a pollution detector or preservation mechanism... there is no precision/recall analysis of the issue detector or breakdown of harmful false-positive edits and missed pollution.

**Response to W5:** We agree, we built it, and it changed a claim in our paper. We report the full result, including the part that goes against us.

**Design.** Rather than rely on a judge to label what is harmful — which would make the evaluation circular — we constructed ground truth. Into 145 LiC database and code replay conversations we injected **two** spans each, one known-false and one known-true, in an identical surface frame, each anchored on a rare token verified absent from the conversation. Labels are correct by construction and no judge is involved anywhere. 126 conversations pass a mechanical anchor-admissibility check applied identically to both sides. Four offline positive controls calibrate the metric: an identity editor scores 0.00 removal / 1.00 preservation, a hand-removal oracle 1.00 / 1.00, and a delete-everything editor 1.00 / **0.00** — which is what makes the preservation rate, rather than the removal rate, the metric that cannot be gamed.

**Results for AC3-Reset (n=126):**

| Metric | AC3-Reset |
|---|---|
| Pollution removal rate | **97.6%** (123/126) |
| Preservation rate | **4.0%** (5/126) |
| Edit precision (chance = 50.0% by construction) | **50.4%** (123/244) |
| Gate sensitivity | 98.4% (124/126); clean-arm gate-open base rate 96.8% |
| Injected pollutant named explicitly in the analyzer's `issues` | **78.6%** (99/126); 89.7% on the causally-harmful subset |

**The detection is real; the selectivity is not, for this operator.** The analyzer *names* the injected pollutant in roughly four of five conversations, and nine of ten when the pollutant is causally harmful — that is genuine detection, measured independently of what the editor then does. But Reset's edit precision sits at chance and its preservation rate is 4%: it removes correct injected content at essentially the same rate as false content.

**This means one sentence in our paper is wrong as attributed, and we are fixing it rather than defending it.** We describe AC3 as preserving what is correct and removing what is harmful. That is a claim about **AC3-Rewrite**, which sits at the opposite corner of the same measurement (removal 27.0%, preservation 38.9%) and demonstrates that the metric is not saturated. What AC3-**Reset** does — and what the data supports — is *detect, discard the assistant side, and re-derive the specification from the user side*. It is a different and still-defensible mechanism, and it is the one we should have been describing for that operator. We will state the mechanism per operator in Section 3 and in the ERGO comparison.

**That removal is causally load-bearing, established without reference to the detector.** Because only three conversations had AC3 keep the harmful span, a direct split is underpowered, so we ran a detector-free factorial over the unedited baseline (clean / harmful-span-only / true-span-only / both): the harmful span costs an unedited assistant **−11.1pp**, and the true span is worth **+15.1pp**. On the causally-validated subset: baseline clean 24.7% → baseline with the pollutant 9.3% → **AC3-Reset with the pollutant present 59.8%**.

**Limits, which we put in the first paragraph of our own writeup.** Injected pollution is plausibly more salient than naturally occurring pollution, so these numbers are an **upper bound and a sanity check**, not a field estimate. The injected spans share one surface frame; two of four harmful types are causally inert; single model, single analyzer, one replay turn per conversation, N=1 per cell. The counterfactual span-ablation study is what would license a headline number, and it is queued.

On the gating behaviour you note, the measured gate-open rates are **97.3%** of LiC conversations (n=554; equivalently 98.5% of the 547 turns on which the analyzer actually ran) and **95.3%** of CollabLLM turns (n=659 analyzer calls over 120 conversations; the per-conversation figure is 98.3%), against the roughly 72% you observed on WildChat. The gate is deliberately high-recall, reflecting a design judgement that missing pollution is more costly than editing unnecessarily; the constructed-pollution study puts gate sensitivity at 98.4% with a 96.8% open rate on clean conversations, so the gate is close to always-on and its cost is unnecessary edits rather than missed ones.

We should name a limitation of those rates ourselves, because it would otherwise be inferred from them: they are a **firing rate, not a detection rate**. In 29% of the LiC gate-open records and 73% of the CollabLLM ones, the analyzer sets `needs_edit` while writing `issues: "None"` — the gate opens without the analyzer having committed to anything it found. The detection figure we would actually stand behind is the constructed-pollution one above, where the analyzer *names* the injected pollutant in 78.6% of conversations, not the open rate.

That unnecessary editing does not appear to be harmful: always-on Reset edits every turn by construction, including turns where nothing needs fixing, and it is our strongest operator overall (33 of 36 paired wins, +15.9pp, p < 0.0001). We would not over-read firing rates into a precision/recall claim — that is exactly the measurement your suggestion supplied, and it is reported above.

---

> **W6:** The memory results are mixed and not yet well characterized... the cheatsheet can introduce stale or overly general priors, which is itself a form of context pollution at the analyzer level.

**Response to W6:** We ran the split analysis and the order-sensitivity analysis you implied, and the results split cleanly into one thing we can answer well and one limitation we should state ourselves. We will take them in that order.

**Contamination is measurably zero.** Because our LiC memory runs are continual — the cheatsheet is distilled from trajectories as evaluation proceeds — the fair question is whether the cheatsheet smuggles evaluation-set content into the analyzer. We measured it three ways. (i) The designated memory learn set has **0 exact duplicates and 0 near-duplicates out of 120** against the canonical LiC evaluation set (maximum token-set Jaccard 0.416, and that is boilerplate). (ii) It overlaps the dev subsets used for the `+ Memory` rows on 11 of 98 instances (11.2%), and **on exactly those overlapping instances memory is equal or worse** than no memory. (iii) The sharpest test: within the continual protocol, we compared the same instance evaluated with an empty cheatsheet against one distilled from 5–20 *other* evaluation instances **together with their gold answers**, and the difference is **0.0pp on both tasks** (n=15 database, n=14 math). Exposure to other evaluation instances confers no measurable advantage.

**The limitation we should state ourselves is variance, not contamination.** Varying the trajectory ordering over four recorded orderings gives a spread of ±6.5pp on database. We then ran the control that this number needs: holding the ordering fixed and merely relearning the cheatsheet gives ±6.1pp, and holding both cheatsheet and ordering fixed while resampling only the evaluation gives ±3.8pp. So ordering is **not** a distinguished source of variance — the cheatsheet learner is simply high-variance, around 6pp, at this scale. That matters for how our own numbers should be read: the paper's memory effects (+10pp math, +12pp database) are **single-trial point estimates below that noise floor**, so we will not defend them as established. A four-ordering re-measurement on a different respondent (gpt-5.4-mini) gives −5.0 and −8.0pp, which is a different model and therefore not a direct refutation, but the variance argument is model-independent.

We would rather say this than have it found. Memory is an **optional, ablated component**: every main result in the paper holds without it, and no headline claim depends on it. For the camera-ready we will either re-run the memory rows at N ≥ 4 or soften the claim to match the evidence.

We would also highlight that your diagnosis is a satisfying consistency check on our own thesis rather than a counterexample to it. A stale cheatsheet polluting the analyzer is precisely the mechanism the paper identifies, now appearing one level up. Our own measurement that the learner is high-variance and order-insensitive is consistent with that reading: what the cheatsheet transmits is a stable headline principle (mean pairwise content-word overlap across orderings 0.29–0.32) with unstable operative detail.

**Revision:** We will present memory explicitly as an optional extension with per-setting deltas, report the split analysis and the order/variance controls, state the noise floor, and either re-run at N ≥ 4 or soften the reported effect.

---

## On Clarity

We take the clarity assessment seriously. We are tightening the narrative so the stated scope and the headline claims align, moving the structural-exclusion ablation into the main body as you and Reviewer Vg97 suggest, and making the abstract and introduction claims precise and checkable. Several of the corrections above — the CollabLLM MATH-Hard figure, the preservation claim's attribution to Rewrite, the BigCodeBench scoring description, and the false-negative adjustment — exist because your review pointed us at the right measurements. We are grateful for a review that made the necessary revisions this concrete.

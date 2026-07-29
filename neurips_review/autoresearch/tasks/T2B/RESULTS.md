# T2B — Counterfactual span ablation (natural spans, causal labels)

> **What this is.** For every span S in a set of naturally occurring LiC conversations, the
> assistant's final turn was re-run N times with S **present** and N times with S **removed**,
> everything else byte-identical. A span is **harmful** if removing it reliably raises accuracy
> and **useful** if removing it reliably lowers it. No detector, no judge and no LLM of any kind
> appears anywhere in the path that produces these labels, which is what makes them immune to
> the circularity objection. AC3's own edits are then compared *against* the labels.
>
> **Relation to T2A.** T2A established the same causal logic on *injected* spans and flagged
> exactly one limitation: injected pollution is plausibly more salient than natural pollution.
> T2B is that limitation addressed — **natural spans, causal labels** — and it re-uses T2A's
> injected spans as positive controls so the two studies sit on one scale.
>
> **Metric is raw accuracy.** `adjusted_accuracy` excludes 50–78% of editing-arm failures vs 9%
> for baseline and is not comparable across arms. For span ablation the quantity of interest is
> literally the assistant's raw success rate under a fixed prefix, so raw accuracy is both the
> honest and the correct choice. All numbers below are raw.
## Headline

* **111 natural spans** across **30 LiC conversations** (database + code) received causal labels, from 14 present + 12 ablated replicate runs each at temperature 1.0 (3357 assistant turns, 0 errors).
* **All three controls pass**: a contentless span +0.033 [-0.010, +0.082] (n.s.), T2A's causally-validated pollutant +0.368 [+0.223, +0.512], the full-spec/gold-SQL span -0.447 [-0.574, -0.315]. The harness resolves a large effect in both directions and reports ~0 when nothing is there.
* **Minimum detectable effect**: 0.333 as an observed difference; +0.53 as a true effect at 80% power. Per-span labels resolve only large effects; *inconclusive is not inert*.
* **Natural spans do carry real causal effects, and they are concentrated.** Against a replicate-matched null, the spread of per-span effects is significantly wider than noise (SD of effects 0.155 vs null 0.125, p = 0.0085), and there are **16 spans with |delta| >= 0.25 where the null predicts 9.3** (p = 0.0170). But the *mean* effect over all spans is +0.020 [-0.010, +0.048] — the typical natural span is causally inert. Pollution is a minority phenomenon, not a diffuse fog.
* **Split** (point-estimate labels, |delta| >= 0.25): **11 harmful, 5 useful, 95 inconclusive**. Under the strict Fisher test: 3 harmful, 0 useful.
* **Alignment — neither operator is selective on natural spans.** **AC3-Reset** keeps 5/66 probe-admissible spans; removal rate on causally harmful spans 100.0% (7/7), preservation rate on causally useful spans 0.0% (0/4). **AC3-Rewrite** keeps 0/66 probe-admissible spans; removal rate on causally harmful spans 100.0% (7/7), preservation rate on causally useful spans 0.0% (0/4). Both remove essentially everything, so removal rate is high for the same reason preservation is ~0: the mechanism is rebuild-from-the-user-side, not surgical excision.


## 0. Corpus and replicate counts

* conversations: **30** (Counter({'database_v2': 17, 'code_v2': 13}))
* spans: **111** (Counter({'prose': 68, 'code': 43}))
* 32 conversations were selected and run; 2 code conversations produced no admissible span (every prefix assistant message was a single block, so no in-place ablation exists), which is why the span table covers 30. The control arms and §5 use all 32.
* replicate runs at temperature 1.0 — present: {'code_v2': 14, 'database_v2': 14}, ablation (min over conditions): {1: {'code_v2': 12, 'database_v2': 12}, 2: {'code_v2': 12, 'database_v2': 12}, 3: {'code_v2': 12, 'database_v2': 12}, 4: {'code_v2': 12, 'database_v2': 12}}
* controls: {'ctl_filler': {'code_v2': 8, 'database_v2': 8}, 'ctl_harm': {'code_v2': 8, 'database_v2': 8}, 'ctl_answer': {'code_v2': 8, 'database_v2': 8}}

## 1. Minimum detectable effect at the realised N

n_present = 14, n_ablated = 12, mean present accuracy p0 = 0.393.

| quantity | value |
|---|---|
| smallest **observed** difference that can reach two-sided Fisher p < 0.05 | **0.333** |
| smallest **true** upward effect detectable with 80% power at p0=0.39 | **+0.53** |
| smallest **true** downward effect detectable with 80% power at p0=0.39 | **not reachable — bounded by p0 = 0.39** |

Read this honestly: **per-span labels resolve only large effects.** A span that shifts the
assistant's success probability by 10-20 pp is invisible at this N and will be scored
*inconclusive*, not *inert*. The downward direction is additionally bounded by the base
rate — a span cannot be shown useful in a conversation the assistant never gets right.
The load-bearing analyses are therefore the aggregate ones in §4-§6, which pool across
all spans and are well powered.

## 2. Positive and negative controls

Every control is a **paired, per-conversation** comparison against the same `present` arm, scored by exactly the code that scores the natural spans.

| control | expected sign | n conv | present acc | injected acc | ablation effect (removed − present) | 95% CI | perm p |
|---|---|---|---|---|---|---|---|
| `ctl_filler` | ≈ 0 | 32 | 0.393 | 0.359 | **+0.033** | [-0.010, +0.082] | 0.7264 |
| `ctl_harm` | > 0 | 24 | 0.378 | 0.010 | **+0.368** | [+0.223, +0.512] | 0.0001 |
| `ctl_answer` | ≪ 0 | 32 | 0.393 | 0.840 | **-0.447** | [-0.574, -0.315] | 0.0000 |

**Controls pass: True** ({'ctl_filler': True, 'ctl_harm': True, 'ctl_answer': True}).

`ctl_filler` is the negative control the brief demands ("ablating an irrelevant span should
produce ~0 effect"); `ctl_answer` is the positive control ("ablating the span containing the
answer should produce a large one"); `ctl_harm` calibrates the natural spans against T2A's
causally-validated injected pollution on the same scale.

### 2.1 Empirical null, taken from the negative control

`ctl_filler` gives 32 genuine null ablations (a contentless span removed from a real conversation), scored by exactly the ablation code path. Their |effect| distribution is the empirical noise floor:

* mean +0.0335, mean |effect| 0.0792, max |effect| 0.3750
* **95th percentile of |effect| under the null = 0.339** — used below as the data-driven threshold `TAU_null`. The filler control runs at fewer replicates than the ablation arms, so its noise floor is if anything *wider* than the ablation arms', which makes this threshold conservative.

## 3. Per-span causal labels

Spans with a usable comparison: **111** of 111.

* **strict (two-sided Fisher p < 0.05)**: harmful 3, useful 0, inconclusive 108 (2.7% (3/111) harmful, 0.0% (0/111) useful)
* **null-calibrated (|delta| > 95th pct of the filler null)**: harmful 4, useful 3, inconclusive 104 (3.6% (4/111) harmful, 2.7% (3/111) useful)
* **lenient (|delta| >= 0.25, point estimate)**: harmful 11, useful 5, inconclusive 95 (9.9% (11/111) harmful, 4.5% (5/111) useful)
* **How many of those are real?** The null-calibrated threshold is the 95th percentile of a genuine null, so **5.6** of 111 spans would be labelled by chance. **7** were labelled (binomial p = 3.20e-01), i.e. an excess of ≈ **1** over that floor. This particular comparison is **conservative to the point of being uninformative** — the filler null is measured at 8 replicates while the ablation arms run at 12-14, so its threshold is too wide. §3.0 redoes it with a replicate-matched null, which is the version to read.

### 3.0 Is *anything* here above noise? A matched parametric null

The filler null above is measured at 8 replicates while the ablation arms run at 12-14, so it is systematically **wider** than the ablation noise and under-detects. The clean comparison is a parametric null with the *same* replicate counts and the *same* per-span base rate but **no effect**, simulated 2000 times over all 111 spans:

| statistic | observed | null mean | null 95th pct | p |
|---|---|---|---|---|
| SD of delta across spans | **0.1554** | 0.1249 | 0.1439 | 0.0085 |
| # spans with |delta| >= 0.25 | **16** | 9.341 | 14 | 0.0170 |
| # spans with Fisher p < 0.05 | **3** | 1.458 | 4 | 0.1734 |

This is the well-powered version of the question the per-span labels cannot answer individually: *does the set of natural spans contain real causal effects at all?*

* surviving Benjamini–Hochberg at q = 0.10: **0** spans (0 harmful, 0 useful)

Mean ablation effect over **all** spans: **+0.0195** [95% CI -0.0095, +0.0485] — i.e. the average natural span is close to causally inert, which is itself the finding: pollution is concentrated, not diffuse.

| bucket | n |
|---|---|
| delta <= -0.50 | 0 |
| -0.50 < delta <= -0.25 | 5 |
| -0.25 < delta < -0.05 | 18 |
| |delta| <= 0.05 | 59 |
| 0.05 < delta < 0.25 | 18 |
| 0.25 <= delta < 0.50 | 10 |
| delta >= 0.50 | 1 |

* **database_v2** (63 spans): mean delta -0.0110; strict labels harmful 2 / useful 0 / inconclusive 61
* **code_v2** (48 spans): mean delta +0.0595; strict labels harmful 1 / useful 0 / inconclusive 47
* **code spans** (43): mean delta +0.0507; harmful 2 / useful 0
* **prose spans** (68): mean delta -0.0002; harmful 1 / useful 0

### 3.1 The spans at the extremes (qualitative, for the reader)

Most **harmful** natural spans (removing them helped most)

| task | kind | delta | 95% CI | p | excerpt |
|---|---|---|---|---|---|
| code | prose | **+0.500** | [+0.16, +0.73] | 0.006 | `I don't have enough context to help you with a specific number of carrots, but I can write a Python function t` |
| database | code | **+0.429** | [+0.10, +0.67] | 0.017 | ````sql SELECT e.City FROM employee e JOIN hiring h ON e.Employee_ID = h.Employee_ID GROUP BY e.City HAVING AVG` |
| database | code | **+0.429** | [+0.10, +0.67] | 0.017 | ````sql SELECT e.City FROM employee e JOIN hiring h ON e.Employee_ID = h.Employee_ID WHERE e.Age < 30 GROUP BY ` |
| code | code | **+0.381** | [+0.00, +0.64] | 0.113 | ````python def min_cost_to_make_all_same(bits): """ bits: list of integers (0 or 1) Returns minimum cost to mak` |
| database | prose | **+0.333** | [-0.03, +0.59] | 0.110 | `Also, would you like to see the airport codes, city names, or other details?` |
| code | code | **+0.333** | [-0.03, +0.59] | 0.110 | ````python def sort_list_copy(lst): return sorted(lst) ```` |
| code | code | **+0.286** | [-0.07, +0.57] | 0.218 | ````python def swap_case(message: str) -> str: """Return a new string with uppercase letters converted to lower` |
| database | prose | **+0.250** | [-0.02, +0.53] | 0.085 | `I understand you want to analyze pet types. Could you please clarify what specific analysis you need? For exam` |

Most **useful** natural spans (removing them hurt most)

| task | kind | delta | 95% CI | p | excerpt |
|---|---|---|---|---|---|
| database | prose | **-0.393** | [-0.64, -0.01] | 0.062 | `This query joins the `teacher`, `course_arrange`, and `course` tables, then selects the teacher's name and cou` |
| database | code | **-0.393** | [-0.64, -0.01] | 0.062 | ````sql SELECT t.Name AS Teacher_Name, c.Course AS Course_Name FROM teacher t JOIN course_arrange ca ON t.Teach` |
| database | prose | **-0.345** | [-0.62, -0.01] | 0.065 | `Sure! To analyze only students who have pets, I need to know what specific metrics or breakdown you're interes` |
| code | prose | **-0.321** | [-0.59, +0.05] | 0.130 | `You could modify the function to take an additional parameter representing the required minimum value. Then fi` |
| database | prose | **-0.262** | [-0.54, +0.05] | 0.148 | `Certainly! To help you analyze students, could you clarify what specific analysis you need? For example:` |
| code | code | **-0.238** | [-0.53, +0.13] | 0.267 | ````python def smallest_diff_at_least(arr, min_value): if len(arr) < 2: return None arr_sorted = sorted(arr) sm` |
| database | prose | **-0.238** | [-0.53, +0.13] | 0.267 | `Here's the query to find cities with more than one employee under 30:` |
| database | prose | **-0.238** | [-0.53, +0.13] | 0.267 | `Based on your request "cities with young employees", I need to clarify what you mean by "young employees". Cou` |

## 4. Does AC3 remove the spans the ablation proves harmful?

**Probe.** A span is *kept* if at least 50% of its **unique content tokens** — tokens that occur in that span and nowhere else in the whole conversation — survive into the context AC3 actually hands the assistant (`conversation_analysis.user_intent` ∪ `aligned` for Reset, the stage-2 compaction output for Rewrite; `issues` is excluded because it is not part of the assistant's context). Deterministic, no model. Spans with fewer than 2 unique tokens cannot be probed: **66/111 spans are probe-admissible**.

### 4.1 Probe controls

| control carried-context | expected keep rate | measured |
|---|---|---|
| PC-identity: the full unedited conversation | 1.00 | 1.000 (66/66) |
| PC-nuke: empty context | 0.00 | 0.000 (0/66) |
| PC-other: the conversation **minus this span** | 0.00 | 0.000 (0/66) |
| PC-self: the span alone | 1.00 | 1.000 (by construction) |

PC-other is the specificity control that matters: it shows the probe is testing *this span*, not the conversation's general vocabulary. It is 0 by construction because uniqueness is defined against the rest of the conversation — which is exactly why unprobeable spans are excluded rather than guessed at.

### AC3-Reset  (replicates {'code_v2': 5, 'database_v2': 5}; 66 probe-admissible spans)

**Graded survival** (mean fraction of the span's unique tokens reaching the assistant), so the binary keep/remove call can be audited:

| span kind | n | mean survival | median | frac > 0 | frac >= 0.5 (= "kept") |
|---|---|---|---|---|---|
| all | 66 | 0.119 | 0.000 | 0.333 | 0.076 |
| code | 14 | 0.044 | 0.000 | 0.286 | 0.000 |
| prose | 52 | 0.139 | 0.000 | 0.346 | 0.096 |

**Caveat, stated rather than buried.** The probe measures *lexical* survival. For a **code** span the unique tokens are identifiers (`nummanufacturers`, a column name, a function name) and their absence is causally decisive — an identifier the assistant never sees cannot be used. For a **prose** span the unique tokens are often ordinary words (`bit`, `detail`, `provide`), so an editor that preserves the *meaning* in its own words scores as having removed the span. The prose rows are therefore a **lower bound** on preservation; the code rows are the trustworthy ones, and the 2x2 is repeated on code spans alone below.

**strict (Fisher p<0.05) labels** — causally harmful n=1, causally useful n=0

| | causally harmful | causally useful |
|---|---|---|
| **AC3 removed** | 1 | 0 |
| **AC3 kept** | 0 | 0 |

- pollution removal rate = 100.0% (1/1)  [95% CI 20.7–100.0%]
- preservation rate = n/a (0)
- edit precision = 100.0% (1/1)  (base rate: harmful spans are 100.0% (1/1) of the labelled set)

**null-calibrated labels** — causally harmful n=2, causally useful n=2

| | causally harmful | causally useful |
|---|---|---|
| **AC3 removed** | 2 | 2 |
| **AC3 kept** | 0 | 0 |

- pollution removal rate = 100.0% (2/2)  [95% CI 34.2–100.0%]
- preservation rate = 0.0% (0/2)  [95% CI 0.0–65.8%]
- edit precision = 50.0% (2/4)  (base rate: harmful spans are 50.0% (2/4) of the labelled set)

**lenient (|delta|>=0.25) labels** — causally harmful n=7, causally useful n=4

| | causally harmful | causally useful |
|---|---|---|
| **AC3 removed** | 7 | 4 |
| **AC3 kept** | 0 | 0 |

- pollution removal rate = 100.0% (7/7)  [95% CI 64.6–100.0%]
- preservation rate = 0.0% (0/4)  [95% CI 0.0–49.0%]
- edit precision = 63.6% (7/11)  (base rate: harmful spans are 63.6% (7/11) of the labelled set)

**lenient, **code spans only** (the trustworthy probe) labels** — causally harmful n=3, causally useful n=0

| | causally harmful | causally useful |
|---|---|---|
| **AC3 removed** | 3 | 0 |
| **AC3 kept** | 0 | 0 |

- pollution removal rate = 100.0% (3/3)  [95% CI 43.8–100.0%]
- preservation rate = n/a (0)
- edit precision = 100.0% (3/3)  (base rate: harmful spans are 100.0% (3/3) of the labelled set)

**Label-free aggregate test.** Mean causal effect of the spans AC3-Reset *removed* (61) minus that of the spans it *kept* (5): **-0.0139** (permutation p = 0.8500). A selective editor should score **positive**: it should be dropping the spans whose removal helps and keeping the spans whose removal hurts. This test uses no per-span label at all, so it is not limited by the per-span MDE.
  - mean delta | removed = +0.0146 (n=61); kept = +0.0286 (n=5)
  - analyzer gate opened on 0.970 of replicates

### AC3-Rewrite  (replicates {'code_v2': 5, 'database_v2': 5}; 66 probe-admissible spans)

**Graded survival** (mean fraction of the span's unique tokens reaching the assistant), so the binary keep/remove call can be audited:

| span kind | n | mean survival | median | frac > 0 | frac >= 0.5 (= "kept") |
|---|---|---|---|---|---|
| all | 66 | 0.079 | 0.040 | 0.576 | 0.000 |
| code | 14 | 0.026 | 0.000 | 0.357 | 0.000 |
| prose | 52 | 0.094 | 0.050 | 0.635 | 0.000 |

**Caveat, stated rather than buried.** The probe measures *lexical* survival. For a **code** span the unique tokens are identifiers (`nummanufacturers`, a column name, a function name) and their absence is causally decisive — an identifier the assistant never sees cannot be used. For a **prose** span the unique tokens are often ordinary words (`bit`, `detail`, `provide`), so an editor that preserves the *meaning* in its own words scores as having removed the span. The prose rows are therefore a **lower bound** on preservation; the code rows are the trustworthy ones, and the 2x2 is repeated on code spans alone below.

**strict (Fisher p<0.05) labels** — causally harmful n=1, causally useful n=0

| | causally harmful | causally useful |
|---|---|---|
| **AC3 removed** | 1 | 0 |
| **AC3 kept** | 0 | 0 |

- pollution removal rate = 100.0% (1/1)  [95% CI 20.7–100.0%]
- preservation rate = n/a (0)
- edit precision = 100.0% (1/1)  (base rate: harmful spans are 100.0% (1/1) of the labelled set)

**null-calibrated labels** — causally harmful n=2, causally useful n=2

| | causally harmful | causally useful |
|---|---|---|
| **AC3 removed** | 2 | 2 |
| **AC3 kept** | 0 | 0 |

- pollution removal rate = 100.0% (2/2)  [95% CI 34.2–100.0%]
- preservation rate = 0.0% (0/2)  [95% CI 0.0–65.8%]
- edit precision = 50.0% (2/4)  (base rate: harmful spans are 50.0% (2/4) of the labelled set)

**lenient (|delta|>=0.25) labels** — causally harmful n=7, causally useful n=4

| | causally harmful | causally useful |
|---|---|---|
| **AC3 removed** | 7 | 4 |
| **AC3 kept** | 0 | 0 |

- pollution removal rate = 100.0% (7/7)  [95% CI 64.6–100.0%]
- preservation rate = 0.0% (0/4)  [95% CI 0.0–49.0%]
- edit precision = 63.6% (7/11)  (base rate: harmful spans are 63.6% (7/11) of the labelled set)

**lenient, **code spans only** (the trustworthy probe) labels** — causally harmful n=3, causally useful n=0

| | causally harmful | causally useful |
|---|---|---|
| **AC3 removed** | 3 | 0 |
| **AC3 kept** | 0 | 0 |

- pollution removal rate = 100.0% (3/3)  [95% CI 43.8–100.0%]
- preservation rate = n/a (0)
- edit precision = 100.0% (3/3)  (base rate: harmful spans are 100.0% (3/3) of the labelled set)

**Label-free aggregate test.** Not computable: AC3-Rewrite removed 66 spans and kept 0. An editor that removes *everything* leaves nothing to compare against, which is itself the answer — it is not selective.
  - analyzer gate opened on 1.000 of replicates

## 5. Context: raw accuracy of each arm on this corpus

| arm | n conv | raw accuracy | 95% CI |
|---|---|---|---|
| Baseline (present, unedited) | 32 | 0.393 | [0.263, 0.525] |
| AC3-Reset | 32 | 0.519 | [0.369, 0.681] |
| AC3-Rewrite | 32 | 0.531 | [0.388, 0.675] |

These are the same conversations the ablation ran on, so the editing arms' gain and the span-level causal effects are measured on one population. Raw accuracy throughout.

### 5.1 Does removal of causally-harmful spans predict AC3's gain? (exploratory)

* **AC3-Reset**: n = 6 conversations with at least one causally-harmful span, and the predictor has **zero variance** — AC3-Reset removed 100-100% of the causally-harmful spans in every one of them. The correlation is undefined, and that is the substantive answer: you cannot ask whether *selective* removal predicts the gain when the editor is not selective. **Not answerable with this operator.**
* **AC3-Rewrite**: n = 6 conversations with at least one causally-harmful span, and the predictor has **zero variance** — AC3-Rewrite removed 100-100% of the causally-harmful spans in every one of them. The correlation is undefined, and that is the substantive answer: you cannot ask whether *selective* removal predicts the gain when the editor is not selective. **Not answerable with this operator.**

## 6. What this does and does not cover

**Covered.**

* Causal, detector-free labels for every span in the corpus, on **naturally occurring** assistant content — the exact limitation T2A flagged about itself.
* A negative control (contentless span → no effect) and two positive controls in opposite directions (T2A's validated pollutant → large positive; the full spec + gold SQL → large negative), all scored by the same code path as the natural spans.
* The 2×2 alignment table against **both** operators, plus a label-free aggregate test that does not depend on the per-span MDE.
* An empirical noise floor taken from the negative control rather than asserted.

**Not covered — stated rather than implied.**

1. **Per-span power.** At these replicate counts only very large per-span effects reach significance. Most natural spans are scored *inconclusive*, and *inconclusive is not inert*: a span worth 10-20 pp is real and invisible here. Scaling this to a confident per-span label for every span would need roughly an order of magnitude more replicates.
2. **Useful spans are under-detectable by construction.** A span cannot be shown useful in a conversation the assistant never solves, and LiC database sits near the floor. The corpus was selected to have headroom, which mitigates but does not remove this asymmetry — the harmful count and the useful count are **not** on equal footing and should not be read as a symmetric split.
3. **Corpus selection.** 32 conversations chosen from the conv0 replay pools by pilot accuracy (all mid-range first, then evenly spaced over the rest). This is a **high-power subsample, not a representative sample** of LiC; the marginal rate of harmful spans in the wild is not estimated here.
4. **Probe coverage.** Roughly 40% of spans have no token unique to them and cannot be scored for AC3 alignment without a judge. They receive causal labels but are excluded from the 2×2, and boilerplate prose is over-represented among the excluded — so the 2×2 is computed on a slightly more content-bearing subset than the label set.
5. **One model, one analyzer, one replay turn.** gpt-5.4-mini throughout, `replay_turns=1`, so nothing here speaks to compounding across turns.
6. **Single-span ablation only.** Interactions between spans are not measured; a pair of spans that is jointly harmful but individually inert would be scored inert twice.
7. **Tier C (the scalable oracle-informed judge) is not run.** T2B was scoped as the validation anchor, per the TODO. Calibrating a Tier-C judge against these labels remains open; `per_span.json` is the artifact that would make it a small job.
8. **No seeds.** The `seed=` dispatcher fix is not on `main` in this tree, so replicates are independent draws at temperature 1.0 rather than reproducible seeds. Individual replicates are not bit-for-bit reproducible; the aggregates are.


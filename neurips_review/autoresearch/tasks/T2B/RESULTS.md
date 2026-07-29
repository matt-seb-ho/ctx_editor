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

## 0. Corpus and replicate counts

* conversations: **30** (Counter({'database_v2': 17, 'code_v2': 13}))
* spans: **111** (Counter({'prose': 68, 'code': 43}))
* replicate runs at temperature 1.0 — present: {'code_v2': 9, 'database_v2': 9}, ablation (min over conditions): {1: {'code_v2': 9, 'database_v2': 9}, 2: {'code_v2': 9, 'database_v2': 9}, 3: {'code_v2': 9, 'database_v2': 9}, 4: {'code_v2': 8, 'database_v2': 9}}
* controls: {'ctl_filler': {'code_v2': 8, 'database_v2': 8}, 'ctl_harm': {'code_v2': 8, 'database_v2': 8}, 'ctl_answer': {'code_v2': 8, 'database_v2': 8}}

## 1. Minimum detectable effect at the realised N

n_present = 9, n_ablated = 8, mean present accuracy p0 = 0.396.

| quantity | value |
|---|---|
| smallest **observed** difference that can reach two-sided Fisher p < 0.05 | **0.500** |
| smallest **true** upward effect detectable with 80% power at p0=0.40 | **not reachable** |
| smallest **true** downward effect detectable with 80% power at p0=0.40 | **not reachable — bounded by p0 = 0.40** |

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
| `ctl_filler` | ≈ 0 | 32 | 0.396 | 0.359 | **+0.036** | [-0.017, +0.090] | 0.7043 |
| `ctl_harm` | > 0 | 24 | 0.384 | 0.010 | **+0.374** | [+0.230, +0.522] | 0.0001 |
| `ctl_answer` | ≪ 0 | 32 | 0.396 | 0.840 | **-0.444** | [-0.572, -0.309] | 0.0001 |

**Controls pass: True** ({'ctl_filler': True, 'ctl_harm': True, 'ctl_answer': True}).

`ctl_filler` is the negative control the brief demands ("ablating an irrelevant span should
produce ~0 effect"); `ctl_answer` is the positive control ("ablating the span containing the
answer should produce a large one"); `ctl_harm` calibrates the natural spans against T2A's
causally-validated injected pollution on the same scale.

### 2.1 Empirical null, taken from the negative control

`ctl_filler` gives 32 genuine null ablations (a contentless span removed from a real conversation), scored by exactly the ablation code path. Their |effect| distribution is the empirical noise floor:

* mean +0.0365, mean |effect| 0.0998, max |effect| 0.4028
* **95th percentile of |effect| under the null = 0.319** — used below as the data-driven threshold `TAU_null`. The filler control runs at fewer replicates than the ablation arms, so its noise floor is if anything *wider* than the ablation arms', which makes this threshold conservative.

## 3. Per-span causal labels

Spans with a usable comparison: **111** of 111.

* **strict (two-sided Fisher p < 0.05)**: harmful 0, useful 0, inconclusive 111 (0.0% (0/111) harmful, 0.0% (0/111) useful)
* **null-calibrated (|delta| > 95th pct of the filler null)**: harmful 15, useful 6, inconclusive 90 (13.5% (15/111) harmful, 5.4% (6/111) useful)
* **lenient (|delta| >= 0.25, point estimate)**: harmful 16, useful 6, inconclusive 89 (14.4% (16/111) harmful, 5.4% (6/111) useful)
* **How many of those are real?** The null-calibrated threshold is the 95th percentile of a genuine null, so **5.6** of 111 spans would be labelled by chance. **21** were labelled (binomial p = 1.39e-07), i.e. an excess of ≈ **15 genuinely causal spans** over the noise floor.
* surviving Benjamini–Hochberg at q = 0.10: **0** spans (0 harmful, 0 useful)

Mean ablation effect over **all** spans: **+0.0280** [95% CI -0.0091, +0.0668] — i.e. the average natural span is close to causally inert, which is itself the finding: pollution is concentrated, not diffuse.

| bucket | n |
|---|---|
| delta <= -0.50 | 3 |
| -0.50 < delta <= -0.25 | 3 |
| -0.25 < delta < -0.05 | 17 |
| |delta| <= 0.05 | 58 |
| 0.05 < delta < 0.25 | 14 |
| 0.25 <= delta < 0.50 | 16 |
| delta >= 0.50 | 0 |

* **database_v2** (63 spans): mean delta -0.0088; strict labels harmful 0 / useful 0 / inconclusive 63
* **code_v2** (48 spans): mean delta +0.0764; strict labels harmful 0 / useful 0 / inconclusive 48
* **code spans** (43): mean delta +0.0526; harmful 0 / useful 0
* **prose spans** (68): mean delta +0.0125; harmful 0 / useful 0

### 3.1 The spans at the extremes (qualitative, for the reader)

Most **harmful** natural spans (removing them helped most)

| task | kind | delta | 95% CI | p | excerpt |
|---|---|---|---|---|---|
| code | code | **+0.444** | [-0.01, +0.71] | 0.153 | ````python def sort_list_copy(lst): return sorted(lst) ```` |
| code | prose | **+0.444** | [-0.01, +0.71] | 0.153 | `Here's a Python function that returns a sorted copy of a list of non-negative numbers:` |
| database | prose | **+0.444** | [+0.01, +0.72] | 0.131 | `Also, would you like to see the airport codes, city names, or other details?` |
| database | code | **+0.444** | [+0.05, +0.73] | 0.082 | ````sql SELECT e.City FROM employee e JOIN hiring h ON e.Employee_ID = h.Employee_ID GROUP BY e.City HAVING AVG` |
| database | code | **+0.444** | [+0.05, +0.73] | 0.082 | ````sql SELECT e.City FROM employee e JOIN hiring h ON e.Employee_ID = h.Employee_ID WHERE e.Age < 30 GROUP BY ` |
| code | prose | **+0.444** | [+0.05, +0.73] | 0.082 | `I don't have enough context to help you with a specific number of carrots, but I can write a Python function t` |
| code | prose | **+0.444** | [+0.05, +0.73] | 0.082 | `Wait, this means the sequence would be all zeros if the first three terms start as 0, 0, 0. But you mentioned ` |
| code | code | **+0.417** | [-0.05, +0.69] | 0.153 | ````python def sort_non_negative(lst): return sorted(lst) ```` |

Most **useful** natural spans (removing them hurt most)

| task | kind | delta | 95% CI | p | excerpt |
|---|---|---|---|---|---|
| code | code | **-0.556** | [-0.78, -0.10] | 0.057 | ````python def smallest_diff_at_least(arr, min_value): if len(arr) < 2: return None arr_sorted = sorted(arr) sm` |
| code | prose | **-0.556** | [-0.78, -0.10] | 0.057 | `You could modify the function to take an additional parameter representing the required minimum value. Then fi` |
| database | code | **-0.556** | [-0.78, -0.10] | 0.057 | ````sql SELECT t.Name AS Teacher_Name, c.Course AS Course_Name FROM teacher t JOIN course_arrange ca ON t.Teach` |
| database | prose | **-0.444** | [-0.71, +0.01] | 0.153 | `This query joins the `teacher`, `course_arrange`, and `course` tables, then selects the teacher's name and cou` |
| database | prose | **-0.333** | [-0.65, +0.03] | 0.206 | `Sure! To analyze only students who have pets, I need to know what specific metrics or breakdown you're interes` |
| database | prose | **-0.333** | [-0.65, +0.03] | 0.206 | `Certainly! To help you analyze students, could you clarify what specific analysis you need? For example:` |
| database | code | **-0.222** | [-0.55, +0.20] | 0.637 | ````sql SELECT contestant_number, contestant_name FROM CONTESTANTS; ```` |
| database | prose | **-0.222** | [-0.55, +0.20] | 0.637 | `Based on your request "cities with young employees", I need to clarify what you mean by "young employees". Cou` |

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

**strict (Fisher p<0.05) labels** — causally harmful n=0, causally useful n=0

| | causally harmful | causally useful |
|---|---|---|
| **AC3 removed** | 0 | 0 |
| **AC3 kept** | 0 | 0 |

- pollution removal rate = n/a (0)
- preservation rate = n/a (0)
- edit precision = n/a (0)  (base rate: harmful spans are n/a (0) of the labelled set)

**null-calibrated labels** — causally harmful n=7, causally useful n=4

| | causally harmful | causally useful |
|---|---|---|
| **AC3 removed** | 6 | 4 |
| **AC3 kept** | 1 | 0 |

- pollution removal rate = 85.7% (6/7)  [95% CI 48.7–97.4%]
- preservation rate = 0.0% (0/4)  [95% CI 0.0–49.0%]
- edit precision = 60.0% (6/10)  (base rate: harmful spans are 63.6% (7/11) of the labelled set)

**lenient (|delta|>=0.25) labels** — causally harmful n=8, causally useful n=4

| | causally harmful | causally useful |
|---|---|---|
| **AC3 removed** | 7 | 4 |
| **AC3 kept** | 1 | 0 |

- pollution removal rate = 87.5% (7/8)  [95% CI 52.9–97.8%]
- preservation rate = 0.0% (0/4)  [95% CI 0.0–49.0%]
- edit precision = 63.6% (7/11)  (base rate: harmful spans are 66.7% (8/12) of the labelled set)

**Label-free aggregate test.** Mean causal effect of the spans AC3-Reset *removed* (61) minus that of the spans it *kept* (5): **-0.0605** (permutation p = 0.4954). A selective editor should score **positive**: it should be dropping the spans whose removal helps and keeping the spans whose removal hurts. This test uses no per-span label at all, so it is not limited by the per-span MDE.
  - mean delta | removed = +0.0061 (n=61); kept = +0.0667 (n=5)
  - analyzer gate opened on 0.970 of replicates

### AC3-Rewrite  (replicates {'code_v2': 5, 'database_v2': 5}; 66 probe-admissible spans)

**strict (Fisher p<0.05) labels** — causally harmful n=0, causally useful n=0

| | causally harmful | causally useful |
|---|---|---|
| **AC3 removed** | 0 | 0 |
| **AC3 kept** | 0 | 0 |

- pollution removal rate = n/a (0)
- preservation rate = n/a (0)
- edit precision = n/a (0)  (base rate: harmful spans are n/a (0) of the labelled set)

**null-calibrated labels** — causally harmful n=7, causally useful n=4

| | causally harmful | causally useful |
|---|---|---|
| **AC3 removed** | 7 | 4 |
| **AC3 kept** | 0 | 0 |

- pollution removal rate = 100.0% (7/7)  [95% CI 64.6–100.0%]
- preservation rate = 0.0% (0/4)  [95% CI 0.0–49.0%]
- edit precision = 63.6% (7/11)  (base rate: harmful spans are 63.6% (7/11) of the labelled set)

**lenient (|delta|>=0.25) labels** — causally harmful n=8, causally useful n=4

| | causally harmful | causally useful |
|---|---|---|
| **AC3 removed** | 8 | 4 |
| **AC3 kept** | 0 | 0 |

- pollution removal rate = 100.0% (8/8)  [95% CI 67.6–100.0%]
- preservation rate = 0.0% (0/4)  [95% CI 0.0–49.0%]
- edit precision = 66.7% (8/12)  (base rate: harmful spans are 66.7% (8/12) of the labelled set)

**Label-free aggregate test.** Mean causal effect of the spans AC3-Rewrite *removed* (66) minus that of the spans it *kept* (0): **+nan** (permutation p = nan). A selective editor should score **positive**: it should be dropping the spans whose removal helps and keeping the spans whose removal hurts. This test uses no per-span label at all, so it is not limited by the per-span MDE.

  - analyzer gate opened on 1.000 of replicates

## 5. Context: raw accuracy of each arm on this corpus

| arm | n conv | raw accuracy | 95% CI |
|---|---|---|---|
| Baseline (present, unedited) | 32 | 0.396 | [0.267, 0.535] |
| AC3-Reset | 32 | 0.519 | [0.369, 0.681] |
| AC3-Rewrite | 32 | 0.531 | [0.388, 0.675] |

These are the same conversations the ablation ran on, so the editing arms' gain and the span-level causal effects are measured on one population. Raw accuracy throughout.

### 5.1 Does removal of causally-harmful spans predict AC3's gain? (exploratory)

* **AC3-Reset**: n = 6 conversations with at least one causally-harmful span; Pearson r between (fraction of harmful spans removed) and (accuracy gain) = **-0.376**. Underpowered by design — reported, not leaned on.
* **AC3-Rewrite**: n = 6 conversations with at least one causally-harmful span; Pearson r between (fraction of harmful spans removed) and (accuracy gain) = **+nan**. Underpowered by design — reported, not leaned on.

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


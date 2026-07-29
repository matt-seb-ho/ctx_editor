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
* replicate runs at temperature 1.0 — present: {'code_v2': 4, 'database_v2': 4}, ablation (min over conditions): {1: {'code_v2': 4, 'database_v2': 4}, 2: {'code_v2': 3, 'database_v2': 4}, 3: {'code_v2': 3, 'database_v2': 4}, 4: {'code_v2': 3, 'database_v2': 4}}
* controls: {'ctl_filler': {'code_v2': 3, 'database_v2': 4}, 'ctl_harm': {'code_v2': 3, 'database_v2': 4}, 'ctl_answer': {'code_v2': 3, 'database_v2': 4}}

## 1. Minimum detectable effect at the realised N

n_present = 4, n_ablated = 3, mean present accuracy p0 = 0.383.

| quantity | value |
|---|---|
| smallest **observed** difference that can reach two-sided Fisher p < 0.05 | **1.000** |
| smallest **true** upward effect detectable with 80% power at p0=0.38 | **not reachable** |
| smallest **true** downward effect detectable with 80% power at p0=0.38 | **not reachable — bounded by p0 = 0.38** |

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
| `ctl_filler` | ≈ 0 | 32 | 0.383 | 0.354 | **+0.029** | [-0.042, +0.102] | 0.7867 |
| `ctl_harm` | > 0 | 24 | 0.344 | 0.000 | **+0.344** | [+0.198, +0.500] | 0.0000 |
| `ctl_answer` | ≪ 0 | 32 | 0.383 | 0.823 | **-0.440** | [-0.573, -0.305] | 0.0001 |

**Controls pass: True** ({'ctl_filler': True, 'ctl_harm': True, 'ctl_answer': True}).

`ctl_filler` is the negative control the brief demands ("ablating an irrelevant span should
produce ~0 effect"); `ctl_answer` is the positive control ("ablating the span containing the
answer should produce a large one"); `ctl_harm` calibrates the natural spans against T2A's
causally-validated injected pollution on the same scale.

### 2.1 Empirical null, taken from the negative control

`ctl_filler` gives 32 genuine null ablations (a contentless span removed from a real conversation), scored by exactly the ablation code path. Their |effect| distribution is the empirical noise floor:

* mean +0.0286, mean |effect| 0.1276, max |effect| 0.5000
* **95th percentile of |effect| under the null = 0.500** — used below as the data-driven threshold `TAU_null`. The filler control runs at fewer replicates than the ablation arms, so its noise floor is if anything *wider* than the ablation arms', which makes this threshold conservative.

## 3. Per-span causal labels

Spans with a usable comparison: **111** of 111.

* **strict (two-sided Fisher p < 0.05)**: harmful 1, useful 0, inconclusive 110 (0.9% (1/111) harmful, 0.0% (0/111) useful)
* **null-calibrated (|delta| > 95th pct of the filler null)**: harmful 4, useful 1, inconclusive 106 (3.6% (4/111) harmful, 0.9% (1/111) useful)
* **lenient (|delta| >= 0.25, point estimate)**: harmful 26, useful 17, inconclusive 68 (23.4% (26/111) harmful, 15.3% (17/111) useful)
* surviving Benjamini–Hochberg at q = 0.10: **0** spans (0 harmful, 0 useful)

Mean ablation effect over **all** spans: **+0.0458** [95% CI -0.0030, +0.0961] — i.e. the average natural span is close to causally inert, which is itself the finding: pollution is concentrated, not diffuse.

| bucket | n |
|---|---|
| delta <= -0.50 | 4 |
| -0.50 < delta <= -0.25 | 13 |
| -0.25 < delta < -0.05 | 7 |
| |delta| <= 0.05 | 56 |
| 0.05 < delta < 0.25 | 5 |
| 0.25 <= delta < 0.50 | 14 |
| delta >= 0.50 | 12 |

* **database_v2** (63 spans): mean delta +0.0198; strict labels harmful 0 / useful 0 / inconclusive 63
* **code_v2** (48 spans): mean delta +0.0799; strict labels harmful 1 / useful 0 / inconclusive 47
* **code spans** (43): mean delta +0.0659; harmful 0 / useful 0
* **prose spans** (68): mean delta +0.0331; harmful 1 / useful 0

### 3.1 The spans at the extremes (qualitative, for the reader)

Most **harmful** natural spans (removing them helped most)

| task | kind | delta | 95% CI | p | excerpt |
|---|---|---|---|---|---|
| code | prose | **+1.000** | [+0.25, +1.00] | 0.029 | `This is a prefix flip operation - flipping a prefix of length i+1 costs i+1.` |
| database | prose | **+0.750** | [+0.09, +0.95] | 0.143 | `- Airports that have no flights arriving or departing? - Airports that are isolated (not connected to any othe` |
| code | prose | **+0.750** | [+0.09, +0.95] | 0.143 | `I'll solve the problem of finding the lowest cost to make all bits the same.` |
| code | code | **+0.667** | [-0.00, +0.94] | 0.143 | ````python def min_cost_to_make_all_same(bits): """ bits: list of integers (0 or 1) Returns minimum cost to mak` |
| database | prose | **+0.500** | [-0.14, +0.79] | 0.486 | `Also, would you like to see the airport codes, city names, or other details?` |
| database | code | **+0.500** | [-0.14, +0.79] | 0.486 | ````sql SELECT c.contestant_number, c.contestant_name, COUNT(v.vote_id) AS vote_count FROM CONTESTANTS c JOIN V` |
| database | prose | **+0.500** | [-0.14, +0.79] | 0.486 | `This query returns the contestant number, name, and total vote count for only those contestants who have recei` |
| database | prose | **+0.500** | [-0.10, +0.85] | 0.429 | `I understand you want to analyze pet types. Could you please clarify what specific analysis you need? For exam` |

Most **useful** natural spans (removing them hurt most)

| task | kind | delta | 95% CI | p | excerpt |
|---|---|---|---|---|---|
| database | prose | **-0.750** | [-0.95, -0.09] | 0.143 | `Based on your request "cities with young employees", I need to clarify what you mean by "young employees". Cou` |
| code | prose | **-0.500** | [-0.79, +0.14] | 0.486 | `Here's a Python function that returns a sorted copy of the input list, leaving the original unchanged:` |
| database | prose | **-0.500** | [-0.85, +0.10] | 0.429 | `Certainly! To help you analyze students, could you clarify what specific analysis you need? For example:` |
| database | prose | **-0.500** | [-0.85, +0.10] | 0.429 | `Here's the query to find cities with more than one employee under 30:` |
| code | code | **-0.417** | [-0.76, +0.23] | 0.486 | ````python def sort_list_copy(lst): return sorted(lst) ```` |
| code | code | **-0.333** | [-0.79, +0.23] | 0.429 | ````python def solve(n, colors, queries): # colors is mutable; we modify in-place count = 0 for i in range(n - ` |
| code | prose | **-0.333** | [-0.79, +0.23] | 0.429 | `If you had a different operation in mind involving `k`, please let me know.` |
| code | prose | **-0.250** | [-0.66, +0.32] | 1.000 | `You could modify the function to take an additional parameter representing the required minimum value. Then fi` |

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

**null-calibrated labels** — causally harmful n=2, causally useful n=1

| | causally harmful | causally useful |
|---|---|---|
| **AC3 removed** | 2 | 1 |
| **AC3 kept** | 0 | 0 |

- pollution removal rate = 100.0% (2/2)  [95% CI 34.2–100.0%]
- preservation rate = 0.0% (0/1)  [95% CI 0.0–79.3%]
- edit precision = 66.7% (2/3)  (base rate: harmful spans are 66.7% (2/3) of the labelled set)

**lenient (|delta|>=0.25) labels** — causally harmful n=17, causally useful n=13

| | causally harmful | causally useful |
|---|---|---|
| **AC3 removed** | 16 | 11 |
| **AC3 kept** | 1 | 2 |

- pollution removal rate = 94.1% (16/17)  [95% CI 73.0–99.0%]
- preservation rate = 15.4% (2/13)  [95% CI 4.3–42.2%]
- edit precision = 59.3% (16/27)  (base rate: harmful spans are 56.7% (17/30) of the labelled set)

**Label-free aggregate test.** Mean causal effect of the spans AC3-Reset *removed* (61) minus that of the spans it *kept* (5): **+0.0937** (permutation p = 0.4845). A selective editor should score **positive**: it should be dropping the spans whose removal helps and keeping the spans whose removal hurts. This test uses no per-span label at all, so it is not limited by the per-span MDE.
  - mean delta | removed = +0.0437 (n=61); kept = -0.0500 (n=5)
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

**null-calibrated labels** — causally harmful n=2, causally useful n=1

| | causally harmful | causally useful |
|---|---|---|
| **AC3 removed** | 2 | 1 |
| **AC3 kept** | 0 | 0 |

- pollution removal rate = 100.0% (2/2)  [95% CI 34.2–100.0%]
- preservation rate = 0.0% (0/1)  [95% CI 0.0–79.3%]
- edit precision = 66.7% (2/3)  (base rate: harmful spans are 66.7% (2/3) of the labelled set)

**lenient (|delta|>=0.25) labels** — causally harmful n=17, causally useful n=13

| | causally harmful | causally useful |
|---|---|---|
| **AC3 removed** | 17 | 13 |
| **AC3 kept** | 0 | 0 |

- pollution removal rate = 100.0% (17/17)  [95% CI 81.6–100.0%]
- preservation rate = 0.0% (0/13)  [95% CI 0.0–22.8%]
- edit precision = 56.7% (17/30)  (base rate: harmful spans are 56.7% (17/30) of the labelled set)

**Label-free aggregate test.** Mean causal effect of the spans AC3-Rewrite *removed* (66) minus that of the spans it *kept* (0): **+nan** (permutation p = nan). A selective editor should score **positive**: it should be dropping the spans whose removal helps and keeping the spans whose removal hurts. This test uses no per-span label at all, so it is not limited by the per-span MDE.

  - analyzer gate opened on 1.000 of replicates

## 5. Context: raw accuracy of each arm on this corpus

| arm | n conv | raw accuracy | 95% CI |
|---|---|---|---|
| Baseline (present, unedited) | 32 | 0.383 | [0.250, 0.516] |
| AC3-Reset | 32 | 0.519 | [0.369, 0.681] |
| AC3-Rewrite | 32 | 0.531 | [0.388, 0.675] |

These are the same conversations the ablation ran on, so the editing arms' gain and the span-level causal effects are measured on one population. Raw accuracy throughout.

### 5.1 Does removal of causally-harmful spans predict AC3's gain? (exploratory)

* **AC3-Reset**: too few conversations with a labelled harmful span (2) to correlate. **Not established.**
* **AC3-Rewrite**: too few conversations with a labelled harmful span (2) to correlate. **Not established.**


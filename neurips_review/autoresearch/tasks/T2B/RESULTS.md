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
* replicate runs at temperature 1.0 — present: {'code_v2': 1, 'database_v2': 2}, ablation (min over conditions): {1: {'code_v2': 1, 'database_v2': 2}, 2: {'code_v2': 1, 'database_v2': 2}, 3: {'code_v2': 1, 'database_v2': 2}, 4: {'code_v2': 1, 'database_v2': 2}}
* controls: {'ctl_filler': {'code_v2': 1, 'database_v2': 2}, 'ctl_harm': {'code_v2': 1, 'database_v2': 2}, 'ctl_answer': {'code_v2': 1, 'database_v2': 1}}

## 1. Minimum detectable effect at the realised N

n_present = 1, n_ablated = 1, mean present accuracy p0 = 0.344.

| quantity | value |
|---|---|
| smallest **observed** difference that can reach two-sided Fisher p < 0.05 | **nan** |
| smallest **true** upward effect detectable with 80% power at p0=0.34 | **not reachable** |
| smallest **true** downward effect detectable with 80% power at p0=0.34 | **not reachable — bounded by p0 = 0.34** |

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
| `ctl_filler` | ≈ 0 | 17 | 0.294 | 0.294 | **+0.000** | [-0.118, +0.118] | 1.0000 |
| `ctl_harm` | > 0 | 13 | 0.308 | 0.000 | **+0.308** | [+0.115, +0.500] | 0.0155 |
| `ctl_answer` | ≪ 0 | 0 | — | — | **not run** | — | — |

**Controls pass: True** ({'ctl_filler': True, 'ctl_harm': True, 'ctl_answer': None}).

`ctl_filler` is the negative control the brief demands ("ablating an irrelevant span should
produce ~0 effect"); `ctl_answer` is the positive control ("ablating the span containing the
answer should produce a large one"); `ctl_harm` calibrates the natural spans against T2A's
causally-validated injected pollution on the same scale.

## 3. Per-span causal labels

Spans with a usable comparison: **111** of 111.

* **strict (two-sided Fisher p < 0.05)**: harmful 0, useful 0, inconclusive 111 (0.0% (0/111) harmful, 0.0% (0/111) useful)
* **lenient (|delta| >= 0.25, point estimate)**: harmful 21, useful 13, inconclusive 77 (18.9% (21/111) harmful, 11.7% (13/111) useful)
* surviving Benjamini–Hochberg at q = 0.10: **0** spans (0 harmful, 0 useful)

Mean ablation effect over **all** spans: **+0.0856** [95% CI +0.0000, +0.1712] — i.e. the average natural span is close to causally inert, which is itself the finding: pollution is concentrated, not diffuse.

| bucket | n |
|---|---|
| delta <= -0.50 | 13 |
| -0.50 < delta <= -0.25 | 0 |
| -0.25 < delta < -0.05 | 0 |
| |delta| <= 0.05 | 77 |
| 0.05 < delta < 0.25 | 0 |
| 0.25 <= delta < 0.50 | 0 |
| delta >= 0.50 | 21 |

* **database_v2** (63 spans): mean delta -0.0238; strict labels harmful 0 / useful 0 / inconclusive 63
* **code_v2** (48 spans): mean delta +0.2292; strict labels harmful 0 / useful 0 / inconclusive 48
* **code spans** (43): mean delta +0.1512; harmful 0 / useful 0
* **prose spans** (68): mean delta +0.0441; harmful 0 / useful 0

## 4. Does AC3 remove the spans the ablation proves harmful?

**Probe.** A span is *kept* if at least 50% of its **unique content tokens** — tokens that occur in that span and nowhere else in the whole conversation — survive into the context AC3 actually hands the assistant (`conversation_analysis.user_intent` ∪ `aligned` for Reset, the stage-2 compaction output for Rewrite; `issues` is excluded because it is not part of the assistant's context). Deterministic, no model. Spans with fewer than 2 unique tokens cannot be probed: **66/111 spans are probe-admissible**.

### 4.1 Probe controls

| control carried-context | expected keep rate | measured |
|---|---|---|
| PC-identity: the full unedited conversation | 1.00 | 1.000 (66/66) |
| PC-nuke: empty context | 0.00 | 0.000 (0/66) |
| PC-other: the conversation **minus this span** | 0.00 | 0.000 (0/66) |
| PC-self: the span alone | 1.00 | 1.000 (by construction) |

PC-other is the specificity control that matters: it shows the probe is testing *this span*, not the conversation's general vocabulary. It is 0 by construction because uniqueness is defined against the rest of the conversation — which is exactly why unpr obeable spans are excluded rather than guessed at.

### AC3-Reset  (replicates {'code_v2': 1, 'database_v2': 1}; 66 probe-admissible spans)

**strict labels** — causally harmful n=0, causally useful n=0

| | causally harmful | causally useful |
|---|---|---|
| **AC3 removed** | 0 | 0 |
| **AC3 kept** | 0 | 0 |

- pollution removal rate = n/a (0)
- preservation rate = n/a (0)
- edit precision = n/a (0)  (base rate: harmful spans are n/a (0) of the labelled set)

**lenient labels** — causally harmful n=12, causally useful n=8

| | causally harmful | causally useful |
|---|---|---|
| **AC3 removed** | 12 | 7 |
| **AC3 kept** | 0 | 1 |

- pollution removal rate = 100.0% (12/12)  [95% CI 75.7–100.0%]
- preservation rate = 12.5% (1/8)  [95% CI 2.2–47.1%]
- edit precision = 63.2% (12/19)  (base rate: harmful spans are 60.0% (12/20) of the labelled set)

**Label-free aggregate test.** Mean causal effect of the spans AC3-Reset *removed* (61) minus that of the spans it *kept* (5): **+0.2820** (permutation p = 0.2332). A selective editor should score **positive**: it should be dropping the spans whose removal helps and keeping the spans whose removal hurts. This test uses no per-span label at all, so it is not limited by the per-span MDE.
  - mean delta | removed = +0.0820 (n=61); kept = -0.2000 (n=5)
  - analyzer gate opened on 0.970 of replicates

### AC3-Rewrite  (replicates {'database_v2': 1}; 37 probe-admissible spans)

**strict labels** — causally harmful n=0, causally useful n=0

| | causally harmful | causally useful |
|---|---|---|
| **AC3 removed** | 0 | 0 |
| **AC3 kept** | 0 | 0 |

- pollution removal rate = n/a (0)
- preservation rate = n/a (0)
- edit precision = n/a (0)  (base rate: harmful spans are n/a (0) of the labelled set)

**lenient labels** — causally harmful n=4, causally useful n=4

| | causally harmful | causally useful |
|---|---|---|
| **AC3 removed** | 4 | 4 |
| **AC3 kept** | 0 | 0 |

- pollution removal rate = 100.0% (4/4)  [95% CI 51.0–100.0%]
- preservation rate = 0.0% (0/4)  [95% CI 0.0–49.0%]
- edit precision = 50.0% (4/8)  (base rate: harmful spans are 50.0% (4/8) of the labelled set)

**Label-free aggregate test.** Mean causal effect of the spans AC3-Rewrite *removed* (33) minus that of the spans it *kept* (4): **+0.0000** (permutation p = 1.0000). A selective editor should score **positive**: it should be dropping the spans whose removal helps and keeping the spans whose removal hurts. This test uses no per-span label at all, so it is not limited by the per-span MDE.
  - mean delta | removed = +0.0000 (n=33); kept = +0.0000 (n=4)
  - analyzer gate opened on 1.000 of replicates


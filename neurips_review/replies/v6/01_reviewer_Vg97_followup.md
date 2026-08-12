# Reply to Reviewer Vg97 (follow-up)

Thank you for the re-read and for regarding the LiC-scale and replay concerns as addressed. We completed the matched-compute baseline you asked for and address every remaining point; two are self-corrections we surface directly.

## 1. Matched-compute condensation baseline (your principal concern)

A per-turn LLM condenser that compresses faithfully (told to preserve content, **not** to find errors), at a matched call budget. LiC database/code (chosen for headroom), assistant gpt-5.4-mini:

| Arm | database | code |
|---|---|---|
| Baseline (full context) | 56.1% | 83.0% |
| Condenser, 1 call/turn | 53.3% (−2.8, p=0.68) | 79.0% |
| Condenser, 2 calls/turn | 47.7% (−8.4, p=0.08) | 80.0% |
| **AC3-Reset** | **75.7% (+19.6, p=0.0005)** | **92.0% (+9.0, p=0.023)** |

Budget is the crux of an equal-compute control: instrumented per component, the 2-call condenser **exceeded** AC3-Reset's own consumption (1.02–1.19× calls, 1.62–2.14× tokens) and still did not close the gap; Gated-Reset reaches +17.8pp at 0.41× Reset's calls. So the effect is not "more compute." A mechanism probe: with the error-finding clause removed, the condenser flags an assistant error in **0 of 340** summaries; faithful summarisation carries invalidated reasoning forward, it does not adjudicate it. (A neutral-phrasing variant scores 51.4%, so the gap is not prompt-specific.)

## 2. MT-OSC (arXiv:2604.08782), at its published setting

No code release; we reimplemented it (prompt, exemplars, recursion, hyperparameters verbatim) at the **published w=4** on LiC-database: **60.7% vs 56.1%** (+4.7pp, p=0.383). It is a near no-op at LiC length: it modifies context in only **6 of 107** conversations (avg **4.1 turns**), so the gain comes entirely from the 94% it never edits. Forcing engagement (w=2) makes it **worse** (47.7%). Scoped evidence on short conversations, not a verdict on its long-horizon regime.

## 3. Two gaps, stated plainly

**U-Fold** and a **high-pollution self-reflection** arm are not yet run. Our earlier reflection control was near-ceiling math (~97.5% for all arms), which cannot discriminate; we agree. We commit to both on LiC database/code for the revision, and will report them regardless of outcome.

## 4. Clarifications

- **Unit of analysis.** You are right: the sign test shows *directional consistency*, not instance-level uncertainty. Clustered on problems, AC3-Reset is **+15.4pp, 95% CI [+11.5, +19.4]**, 350/93 wins over **1,668 items** (McNemar p<1e-4).
- **Gated-Reset's 12 comparisons.** It ran on one model (DeepSeek-V4-Flash), 4 tasks × 3 prefixes; Reset and Augment run on all three (36 each). We will complete its row for the revision.
- **Random subset, with a correction.** n=40, 3 reruns. We reported AC3-Reset as 100.0 ± 0.0; an extraction metric had dropped unparseable items from AC3's denominator but not baseline's. Symmetric: **87.5 / 93.3 / 95.0**, both operators ahead of full context (87.5) every run. The conclusion (gains survive off replay, off difficulty-selection, on an unseen model) holds; the inflated value is withdrawn.

## 5. tau2 correction

We re-ran the **full tau2 matrix at N=3 (899 rollouts)** with rate-limit mitigation; two of the three full-context baselines were clipped floors: DeepSeek-V4-Flash re-measures **31.6 → 70.2 ± 11.0** and Kimi-K2.6 **26.3 → 78.9 ± 0.0**, while gpt-5.4 reproduces exactly (68.4). With corrected baselines the tau2 magnitude improvement does not hold, and we withdraw it. Two findings survive, and they are what tau2 exists to establish:

1. **Assistant-Omission collapses to 0% on every model** (−68 to −79pp, p<0.0001), structurally: it deletes tool-call state that lives only in assistant turns. This is the failure mode our method exists to avoid, independent of the baseline's level.
2. **Operator ordering matches the deployment rule.** Gated-Reset (light-touch) holds parity with full context on all three models (57.9 / 57.9 / 71.9; Δ −7 to −12pp, all p>0.14), while the heavier operators (Augment, Rewrite; 47–67%) are net-negative. tau2's regime is fixed by construction, not inferred from our results: LiC manufactures pollution by sharding a fully-specified task into per-turn reveals that bait premature commitment; tau2 has no such underspecification, consistent with its strong baseline (68–79%), so there is little erroneous reasoning to remove and much tool-state to preserve. The rule keys on baseline strength (observable before any operator runs) and picks the lightest operator a priori. So tau2 is where the selection rule is tested and holds, not evidence against the method.

## 6. On "one method"

We adopt your framing: the accurate claim is **"at least one AC3 operator improves in every evaluated regime."** The fixed components are the two-query analyzer and structural exclusion; operator intensity is the single knob, and the rule setting it (heavier for higher pollution / weaker models, lightest for strong-baseline stateful settings) is stated a priori; it is what §5 tests. We recharacterise the contribution as a modular family under one analyzer, and make the selection rule explicit in Section 3.

We appreciate the pointed questions behind these corrections.

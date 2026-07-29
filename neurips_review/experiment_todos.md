# Experiment TODOs — NeurIPS Rebuttal Window

Updated 2026-07-29 after a commitment audit against `replies/v4/`. Ordered by risk-adjusted value.

**Strategy context:** push back with existing results where possible. Spend compute only where it (a) closes a gap a reviewer explicitly named, (b) removes a claim we currently assert on thin data, or (c) is already promised in the rebuttal text. Remaining limitations go in the camera-ready limitations appendix.

---

## P0 — The two headline items

### T1. Compression / condensation baselines
**Answers:** Vg97 W1/Q1, AC "limited baselines." **Status:** underway.

Two parts; the first is required even if the second slips.

1. **Justification (no compute).** Already written into `replies/v4/02_reviewer_Vg97.md` and the General Response: our baselines target *pollution*; compaction and folding target *context-length pressure*, and can preserve invalidated reasoning in compressed form. Framed as a scoping decision, positively.
2. **Run at least one condensation baseline** so we tested the boundary rather than argued it. Priority order:
   - **Generic LLM summarisation/condensation** per turn at matched call budget. Closest to MT-OSC in spirit, easiest to implement, equal-budget by construction. The repo's `ContextCompactionStrategy` (S3) is the scaffold; the honest external baseline is a *non-analyzer* summariser variant.
   - **MT-OSC** (arXiv:2604.08782) if specified concretely enough to reimplement.
   - **U-Fold** on tau2 if time allows.

   **Predicted result:** summarisation carries invalidated reasoning forward in compressed form and does not close the gap. If it *does* close the gap, that is a genuinely interesting negative result and we report it.
   **Run on:** LiC database and code first (highest pollution, most headroom). **Blocked on Spider DBs for database** (see Blockers).

### T2. Pollution-detection evaluation
**Answers:** 5YHP W5, and pre-empts "is it auditing or just re-solving?" **Status:** design below; not yet implemented.

#### The circularity problem, and why it dissolves

The concern: we want to measure whether AC3 detects pollution, but producing the labels *is* the task AC3 performs, so a judge is just a peer detector.

The resolution is an **information asymmetry**. LiC instances are constructed by shredding a fully-specified single-turn question, so we hold `full_spec_q` and `ground_truth_a`. The analyzer at turn *t* sees only shards 1..k and must *infer* the task. The evaluator, post hoc, *knows* it. So the evaluator's job is **checking consistency against ground truth**, not inferring intent. Those are different difficulty classes, the same way grading with an answer key is legitimate even though writing the key needed the same knowledge.

That argument alone is not enough to lead with, so build three tiers of ground truth, increasing in rigor and decreasing in scale.

#### Tier A — Constructed pollution (no judge at all)
Inject a specific, known-false assumption at a known position into a clean prefix (e.g. "assume the discount applies before tax" when the spec says after). The polluted span is ground truth **by construction**.
- **Pros:** zero judge dependence, perfect labels, cheap, scales.
- **Cons:** synthetic. Injected pollution may be more salient than naturally occurring pollution, so treat detection rates here as an **upper bound / sanity check**, not the headline.
- Generate injections that mirror observed natural failure modes (use the LiC failure-mode report and the tau2 failure-mode table as the taxonomy).

#### Tier B — Counterfactual span ablation (causal; the gold standard)
For a span S in the history: re-run the assistant N times with S present and N times with S removed, everything else fixed. If removing S reliably improves accuracy, S was **harmful**. If removing S hurts, S was **useful and must be preserved**.
- This defines pollution **operationally, by causal effect**, not by anyone's judgment. It is exactly what the method claims to do, so it is the right target.
- Fully non-circular: no detector is involved in producing the label.
- **Cost:** N re-runs per span. Only feasible on ~20-30 conversations (~100-150 spans), which is enough to serve as the **validation anchor** for Tier C.

#### Tier C — Oracle-informed judge (scalable)
Judge sees `full_spec_q`, `ground_truth_a`, and the conversation, and labels each assistant span as *invalidated* / *still-valid* / *necessary-state*.
- **Use a different model family from the analyzer** so it is not literally grading itself.
- **Only trustworthy because it is calibrated against Tiers A and B.** Report agreement on the overlap set.
- Then scale to the full eval set.

#### Human annotation: where it is actually needed
Not as primary ground truth. Tier B is *better* than human opinion because it is causal. Humans are needed for:
- A small **agreement check on Tier C** labels (50-100 spans, 2 annotators, report Cohen's kappa). Cheap, and reviewers expect to see it.
- Adjudicating cases where Tier B is ambiguous (span removal changes accuracy by less than noise).

#### The metric
2x2 confusion over {AC3 removed, AC3 kept} x {harmful, useful}:
- **Pollution removal rate** = of harmful spans, fraction removed.
- **Preservation rate** = of useful spans, fraction kept.
- **Edit precision** = of spans removed, fraction actually harmful.
- **Gate accuracy** at the turn level: when the analyzer declines to edit, was there genuinely nothing to remove?

**Then close the loop:** test whether removal rate **predicts downstream accuracy gain** across instances. If it does, we have converted "AC3 helps" into "AC3 helps *because* it removes pollution," which is the mechanistic claim the paper actually makes.

### T2c. Auditing vs. re-solving (small, high value)
5YHP explicitly raises this: is the analyzer auditing the context, or just re-solving the task and handing over the answer? Direct test: measure whether analyzer output contains or entails the final answer, then check whether AC3 still helps on the subset where it does **not**. If gains persist there, the mechanism is auditing. Cheap, and it defends the paper's core claim.

---

## P1 — Higher risk than they look

### T8. CollabLLM N=3 with the competent user simulator
**Currently N=1.** We are telling 5YHP that the CollabLLM regression "was a user-simulator artifact" and quoting 100% / 20%. Those numbers come from **a single run**. If any reviewer asks how many seeds, we are exposed on a claim we lead with. **Cheap to fix, and I would run this before anything else in P1.**

### T6. Multi-seed tau2
**Currently N=1 (seed 42).** tau2 is the benchmark iNYK attacked hardest, and the multi-model Foundry sweep is now front and centre in the General Response and the AC response. Adding 2 seeds lets us report mean +/- std where we currently cannot. Agentic rollouts are slow, so this is the expensive one, but it is the single largest remaining statistical hole.

### T9. Analyzer-model sensitivity (NEW — currently an unanswered question)
Vg97 Q3 asks "How sensitive are the results to the **analyzer model** and compute budget?" We answered the compute half and **never answered the analyzer-model half**. Hold the assistant fixed, swap the analyzer across 2-3 models of differing strength, measure the delta on LiC. Cheap, directly requested, and it doubles as evidence that the method is not gpt-specific.

---

## P2 — Promised in the rebuttal, previously unlisted (NEW)

Every "We will..." in `replies/v4/` is a commitment. These four had no TODO entry:

| # | Item | Promised in | Cost |
|---|---|---|---|
| T10 | **BigCodeBench execution-based scoring** where the harness permits | 5YHP W4 | Medium (harness work) |
| T11 | **WildChat judge-agreement + position-bias checks** | 5YHP W4 | Low |
| T12 | **Memory order-sensitivity analysis** | 5YHP W6 | Low |
| T13 | **Memory train/evaluation-split analysis** | 5YHP W6 | Low |

T11-T13 are cheap and can be batched. T10 may slip to camera-ready; if so, say so explicitly rather than leaving it implied.

---

## Done

| # | Item | Result |
|---|---|---|
| T3 | Paired significance across the LiC matrix (zero API cost) | Reset +15.9pp, 33/36 wins, sign-test p < 0.0001; beats the AO design-oracle (+13.3pp). `experiments/paired_analysis.py` |
| T4 | Random unbiased subset, end-to-end, N=3 | FN-adjusted: Baseline 87.5 +/- 2.0, Reset 100.0 +/- 0.0, Gated 99.1 +/- 1.2 |
| T5 | Equal-budget control (partial) | Reflection 97.5 vs Reset 97.5 vs Baseline 90.0 on near-ceiling math. **Non-discriminating**; needs re-run on a high-pollution task (folds into T1) |

---

## Not planned, argue instead
- **End-to-end tau2 replay:** ~2 dev-days. Defend replay as causal-attribution design; T4 already supplies fresh end-to-end evidence on LiC.
- **Full human evaluation on WildChat:** out of window. Defend with N=3 seeds and tight intervals; T11 supplies the judge checks.

## Blockers
- **Spider SQLite DBs (`data/spider/databases/`) are not on disk.** This gates every LiC-database run, which is the highest-pollution text task and therefore the right venue for T1, T2 and the discriminating T5. **This is the single blocking dependency for the most valuable remaining work.** Download or point at an existing copy.

## Suggested order if time is short
1. T8 (CollabLLM N=3) — removes an exposed claim we already made
2. T9 (analyzer-model sensitivity) — answers a question currently left hanging
3. T2 Tier A + T2c — the detector story, cheapest useful version
4. T1 condensation baseline — needs Spider for the best venue
5. T11-T13 — cheap promised items
6. T6 (tau2 seeds) — expensive, highest remaining statistical value

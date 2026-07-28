# Experiment TODOs — NeurIPS Rebuttal Window

Ordered by rebuttal value. Status as of 2026-07-27.

**Strategy context:** push back with existing post-submission results wherever possible (see `replies/v2/`). Only spend compute on things that either (a) close a gap a reviewer explicitly named, or (b) let us stop conceding something. Full disclosure of remaining limitations goes in the camera-ready limitations appendix, not the rebuttal.

---

## P0 — In flight this window (the two the rebuttal promises)

### T1. Compression/condensation baselines
**Answers:** Vg97 Q1 (MT-OSC, U-Fold, Context-Folding), AC "limited benchmarks/baselines."
**Status:** underway (user).

Two parts, and the first is required even if the second slips:
1. **Justification (write-up, no compute).** Our baselines were chosen because they target the *same problem we do*: pollution (AO, Concat-User, ERGO all manipulate what stays in context to remove bad influence). Compaction/folding methods target a *different* problem, context-length pressure. Say this explicitly and positively: it is a scoping decision, not an oversight. This lands in `replies/v2/reviewer_Vg97.md`.
2. **Run at least one compression baseline on LiC** so we can say we tested the boundary rather than argued it. Candidates in rough order of effort:
   - Generic **LLM summarization/condensation** of the conversation at each turn (closest to MT-OSC's spirit, easy to implement, equal-budget by construction). The repo already has `ContextCompactionStrategy` (S3) which compacts every turn; a *non-analyzer* summarizer variant is the honest external baseline.
   - **MT-OSC** (arXiv:2604.08782) if the method is specified concretely enough to reimplement.
   - **U-Fold** on tau2 (compaction of agent trajectories) if the tau2 harness time allows.
   
   Expected/hoped result: compression preserves the polluted reasoning in condensed form, so it underperforms AC3 on LiC-database (our highest-pollution text task) even at equal budget. That is the cleanest possible evidence for "pollution != length."
   
   **Run on:** LiC database + code first (highest pollution, most headroom). gpt-5.4-mini via TRAPI.

### T2. Pollution-removal detection metric
**Answers:** 5YHP W5 (the analyzer is never evaluated as a detector), and pre-empts "is it auditing or just re-solving?"
**Status:** to implement (user).

Goal: a metric that scores the *edit itself*, not just downstream accuracy.

Proposed design (cheap version that still answers the criticism):
- On LiC we have ground truth for what the task actually is (`full_spec_q`) and which shards were revealed. So for a polluted prefix we can label, per assistant message, whether it contains a claim contradicted by the final spec.
- **Metric A (removal recall):** of the spans identified as invalidated by an independent judge, what fraction does AC3 remove?
- **Metric B (preservation precision):** of the spans the judge marks as still-valid work, what fraction does AC3 keep?
- **Metric C (gate accuracy):** when the analyzer says `needs_edit=False`, was there genuinely nothing to remove?
- Report as a 2x2 (removed/kept x harmful/useful). This directly counters "no precision/recall analysis of the issue detector."
- Sample size: 40-60 conversations is enough for a rebuttal-grade table.
- Judge: gpt-5.4-mini via TRAPI, with the ground-truth spec available to the judge (that is what makes the labels trustworthy).

Existing partial evidence to cite meanwhile: gate-open rate >=97% on text (LiC 97.3%, CollabLLM 98.3%), and the WildChat gpt-5.4 case where gating costs 14.5pp vs always-on Reset, which characterizes the detector's error profile as false-negative dominated.

---

## P1 — Cheap, high value

### T3. Paired significance across the LiC matrix — DONE (zero API cost)
**Answers:** Vg97 Q2 (paired tests), iNYK Q2 (does the mean clear baseline).
`experiments/paired_analysis.py` -> `paired_analysis_results.txt`. Parses the per-run tables already in `docs/reports/post_neurips_ac3_phase{1,2}.md`. Because all strategies share the same (model, task, prefix) triples, the paired delta is the correct statistic.

Result: over 36 paired comparisons (3 models x 4 tasks x 3 prefixes):
| Strategy | mean paired delta | W/L/T | sign-test p |
|---|---|---|---|
| AC3-Reset | **+15.9pp** | 33/2/1 | <0.0001 |
| AC3-Augment | +15.2pp | 31/1/4 | <0.0001 |
| AC3-Gated-Reset | +17.0pp (n=12, DeepSeek only) | 11/1/0 | 0.0063 |
| AO (design-oracle) | +13.3pp | 31/4/1 | <0.0001 |

Note Reset (+15.9) beats the AO design-oracle (+13.3) on the same paired set. Exclude Rewrite from any claim here: those rows are pre-analyzer-parity and superseded by R6.

### T4. Random unbiased subset, end-to-end, N=3 — DONE
**Answers:** iNYK Q1 (subset selected independently of baseline), iNYK Q2 (variance), 5YHP W3 (replay != end-to-end).
`experiments/exp1_results.txt` + `exp1_reps_results.txt`. Random N=40 LiC-math, fresh end-to-end sim, gpt-5.4-mini, 3 reruns.
FN-adjusted: Baseline 87.5+/-2.0 -> Reset 100.0+/-0.0, Gated 99.1+/-1.2. Raw: Reset 93.3+/-4.2, Gated 95.0+/-0.0. Both operators win in every rerun.

### T5. Equal-budget control — DONE (partial)
**Answers:** Vg97 Q3.
`experiments/exp2_results.txt`. Matched-call-budget reflection ties Reset on random math (97.5 vs 97.5, baseline 90.0). Near-ceiling task, so it does not discriminate. **Re-run on LiC-database** (high pollution, baseline ~19-22%) to get the discriminating version. Fold into T1, same harness.

---

## P2 — Gaps reviewers can still hit

### T6. Multi-seed tau2
tau2 is still **N=1 per cell** (seed 42), and it is the benchmark iNYK attacked hardest. Adding 2 more seeds on `telecom_small` would let us report mean+/-std where we currently cannot. Cost is the concern (agentic rollouts are slow). If it fits the window, it removes the single most legitimate remaining statistical objection.

### T7. Fill Gated-Reset for gpt-5.4 and Kimi on LiC
Currently Gated-Reset paired stats are DeepSeek-only (n=12). Filling the other two models takes the paired n from 12 to 36 and lets us report Gated-Reset with the same confidence as Reset. Reconstructable from existing Reset+Baseline traces via `scripts/reconstruct_gated_reset.py` if traces survive; otherwise re-run.

### T8. CollabLLM N=3 with the competent user-sim
The good CollabLLM numbers (Augment 100% math-hard, Reset 20% bigcodebench) are **N=1**. Three seeds would make the "earlier regression was a user-sim artifact" argument airtight rather than assertable.

---

## Not planned, argue instead
- **End-to-end tau2 replay:** scoped at ~2 dev-days. Defend replay as a deliberate causal-attribution design (identical polluted trajectory for all methods) and note T4 already provides fresh end-to-end evidence on LiC.
- **Human evaluation on WildChat:** out of window. Defend with N=3 seeds and tight CIs (+/-1.3-1.4pp), and offer judge-agreement/position-bias checks for camera-ready.
- **BigCodeBench execution harness:** the simulator cannot pass function signatures. Note the judge discriminates (v8-Rewrite 17.6% vs Reset 0% on gpt-5.4) and defer execution to camera-ready.

## Blocked
- **LiC database experiments need Spider SQLite DBs** (`data/spider/databases/`), not on disk. Required for T1/T2/T5 on database. Download or point at an existing copy before those runs. This is currently the single blocking dependency for the highest-value remaining experiments.

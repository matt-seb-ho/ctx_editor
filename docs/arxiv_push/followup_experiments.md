# Follow-up experiments — deferred to future paper versions

Experiments worth running for a *later* revision but **out of scope for the current arXiv push** (which only bakes in results we already have + improves writing). Sourced from `jun1_megatable_findings.md` §5 and `post_may26_megatable_round_summary.md` §6. Ordered by value.

Status legend: ⬜ not started.

| # | Experiment | Why it matters | Rough cost | Fills / fixes |
|---|---|---|---|---|
| 1 | ⬜ **tau2 Kimi-K2.6 Baseline + AO at workers=2** | Current Kimi tau2 Baseline (26.3%) and AO cells are rate-limit-clipped floors at workers=4 (14–19/20 short-exits). A clean floor (~40–50%) would firm up the +47.4pp Rewrite delta and remove the caveat footnote. AC3 cells already ran clean, so ordering is safe regardless. | ~20 min wall | Table 2 tau2 Kimi Baseline/AO caveat |
| 2 | ⬜ **WildChat × Gated-Reset for DSV4F + Kimi** | The gpt-5.4 finding (Gated-Reset −14.5pp vs always-on Reset) is currently single-respondent. This checks whether the gate's false-negative cost is a strong-respondent effect or cross-model. | ~1 h wall | Table 3 Gated-Reset cells (currently `---` for Foundry) |
| 3 | ⬜ **Multi-seed on the tau2 headline cells** | Table 2 tau2 is N=1 per cell (except the gpt-5-mini best-of-3). Error bars on the +15.8pp Augment / +47.4pp Rewrite gaps would preempt the "single-seed" reviewer attack. | 3 seeds × key cells | Table 2 tau2 variance; Limitations |
| 4 | ⬜ **CollabLLM Reset × {gpt-5.4, Kimi} × BigCodeBench, content-filter back-off** | Two Reset cells are MATH-Hard-only (`†`) because BigCodeBench hit Azure content-filter rejections / Foundry endpoint instability. A back-off + lower-concurrency rerun would fill them. | moderate | Table 2 CollabLLM `†` cells |
| 5 | ⬜ **CollabLLM Gated-Reset reconstruction for all (model, dataset) pairs with Reset cells** | No-LLM reconstruction (`scripts/reconstruct_gated_reset.py`) can fill more cells cheaply, extending the "gate ≈ Reset on text" evidence. | trivial (no new LLM calls) | Table 2 CollabLLM Gated-Reset |

## Larger / structural ideas (not yet scoped)
- **Long-horizon agentic settings** (multi-file coding, iterative design) — named as untested in the Limitations appendix; the natural next frontier beyond tau2 `telecom_small`.
- **Real-user (non-simulated) evaluation** — all current benchmarks use simulated users (LiC/CollabLLM/tau2); a real-user study would address the top Limitations caveat.
- **Self-distillation of the analyzer** — §6 argues the analyzer's plain-text reasoning could be absorbed into the base model to remove the inference-time call overhead; an actual distillation experiment would turn that from speculation into a result.

---
When any of these are run, port the numbers into `writing/overleaf_repo/` and update `jun1_megatable_findings.md` / this file.

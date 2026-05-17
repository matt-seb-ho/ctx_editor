# Post-NeurIPS AC3 Experiment Plan (rev. 3)

**Date**: 2026-05-16
**Status**: revision 3 after two feedback rounds. Pending final approval.

This rev addresses three changes from rev.2:

- **Gating moves into Phase 1** (still last-turn replay; small scope). The full multi-turn gating study is set aside for now.
- **Phase 3 becomes a cross-benchmark study** (CollabLLM + WildChat redos with the winning method, for error bars).
- **Content-filter discussion deepened**: pulled in the v12-archive history; s1 is *not* a complete CF fix; proposed contingency is a fresh "v13" prompt taking v12's structural fix and back-porting v8's analyzer-content quality, documented if needed.

The pricing scaffold is now populated by the user (thank you). Token counts and dollar-cost will flow into reports automatically.

## Decision points (post rev.3)

### 1. Prompt strategy — `v8` default, escalation chain documented

Unchanged from rev.2 in spirit. `v8` is the default for LiC, CollabLLM, WildChat. Concrete escalation chain if Azure CF trips fire:

1. **`v8`** — paper default. First attempt for every cell.
2. **`s1`** — content-filter-aware single-query header-format prompt. *Caveat: s1 also tripped CF at ~65% on gpt-5-mini with embedded system message in May 2026* (see `docs/archive/v12_attempt/azure_jailbreak_filter_triggers.md` table). It is a *partial* fix, not a complete one — viable only when the embedded system message is benign / short.
3. **`v13` (new, only built if needed)** — port the v12 structural fix (drops conversation's original system message, uses markdown-only delimiters, no XML, no `[system]` role prefix in the conversation dump) but reuse v8's analyzer-content design (the two-query split with Q1 = task-spec extraction from user-only messages, Q2 = aligned/issues comparison against full conversation). v12 hit 0% trip rate but its raw content was rushed and analyzer quality regressed — v13 keeps the structural fix, fixes the content. Build only if `s1` also trips above 5% on a cell.

If we build v13, we register it in `analyzer_prompts.py` alongside the existing versions and document the diff in a new `docs/v13_analyzer_design.md`. The doc spec: differences from v8 (structural-only), example input + output, expected analyzer-quality comparison to v8 on a small probe set (10 problems × 1 task) before any large run uses it.

### s1 background (what the user asked about)

s1's design is in code (`src/ctx_editor/strategies/prompts/s1_analysis.txt`) and partial provenance in:

- `docs/archive/v12_attempt/azure_jailbreak_filter_triggers.md` — table of trip rates by template family; s1 is the "no-XML" row at ~65% on gpt-5-mini.
- `docs/reports/dev_set_round2_content_filter_fix.md` — the March 2026 round-2 fix attempt; this is where s1 was first deployed.
- `docs/context_strategies.md` — describes s1 as `single_query_s1` flow: simplified header-format (TASK SPECIFICATION/ALIGNED/ISSUES), drops XML, designed for CollabLLM where the original `v8` was triggering CF.

There is no dedicated "s1 design doc" with rationale. The closest thing is `docs/archive/v12_attempt/notes.md` for the *v12* design (which superseded s1's CF strategy and actually achieved 0% trips). I'd propose **writing a fresh `docs/analyzer_prompt_design_notes.md`** that consolidates:

- The trip-rate evidence (from azure_jailbreak_filter_triggers.md)
- What each surviving prompt version is *for* (v8 = paper default, s1 = CF-aware fallback, v13 = structural fix port if we need it)
- The quality vs CF-safety trade-off table

I'll write that doc as part of the pre-launch checklist, regardless of whether we end up needing v13. It serves as the "here are the prompt adjustments and why" appendix the user asked for in the original `post_nips_exp_plan_pr.md`.

### 2. Single-model exploration → scale-up (unchanged)

Phase 1 = DeepSeek-V4-Flash, Phase 2 = the other three. Promotion logic stays the same: Augment is always promoted (it's the ablation); the best of {Reset, Gated-Reset, Rewrite} also advances; 3pp tiebreak favors Reset over Gated-Reset and Reset over Rewrite (simpler / cheaper).

### 3. Gating — folded into Phase 1 (last-turn replay)

Per the user's feedback: the 10-12 h multi-turn fresh-sim Phase 3 is too expensive right now. We keep the gating question alive but scope it to **last-turn replay** for now, where it can be answered cheaply alongside the rest of Phase 1.

How gating manifests in last-turn replay:

- **AC3-Reset (always-on)**: analyzer runs on the prefix; the edit is applied to the final turn regardless. (`min_turns=1`, `max_resets=large`.)
- **AC3-Gated-Reset**: analyzer runs on the prefix; the analyzer's `needs_edit` signal (the `issues` block being non-empty in v8's output) decides whether to apply the edit. If gate=False, the final turn is generated from the original (un-edited) full context, i.e. behaves like Baseline. (`min_turns=3, max_resets=3` — the paper setting.)

In replay we get exactly one decision point per prefix, so this measures "given a prefix that ended in a failure (or a success), does the analyzer correctly decide whether intervention is warranted?". Two metrics matter:

- **Accuracy** on the 50-problem replay set (already what we measure).
- **Gate-fire rate** — the fraction of prefixes where the gate decided to edit. Critical for the deployment-cost story; an analyzer that always fires is just AC3-Reset rebranded. We log this per cell.

Decision rules:

- Gated-Reset ≥ Reset (always-on) in accuracy → gating preferred.
- Gated-Reset within −2pp of Reset AND gate-fire rate ≤ 75% → gating preferred (cost win without accuracy loss).
- Gated-Reset ≪ Reset → gate is mis-calibrated; report and recommend always-on.

The full multi-turn gating study (where the gate fires repeatedly per conversation, not once per prefix) is **deferred** — captured below as "Future work: multi-turn gating study" but not in this batch.

### 4. Content filter — escalation chain (rev.3 enhancement)

Mostly unchanged from rev.2 but with the s1 caveat made explicit and v13 added as a documented contingency. Also: **Foundry is part of Azure**, so we will explicitly monitor `content_filter_errors.jsonl` on every Foundry cell, not just OAI cells.

### 5. Analysis reuse + registry — unchanged from rev.2

Cache backend, registry, and Hydra integration as previously specified. This is the single largest engineering lift in the rev.2 → rev.3 transition and stays.

## Phase summary (rev.3)

| Phase | What | Model(s) | Strategies | Mode | Est. wall time | Notes |
|---|---|---|---|---|---|---|
| **1** | Variant exploration incl. gating | DeepSeek-V4-Flash | S0, AO, Augment, Reset, **Gated-Reset**, Rewrite | Last-turn replay (3 prefixes/problem) | ~1.5 h | 6 strategies. Cache populates here. |
| **2** | Scale-up | gpt-5.4, Kimi-K2.6, gpt-5.5 | S0, AO, Augment, + winner of {Reset, Gated-Reset, Rewrite} | Last-turn replay | ~5-6 h | Each new analyzer-model is a fresh cache namespace. |
| **3** | Cross-benchmark error bars | DeepSeek-V4-Flash (and Phase-2 winning model if cheap) | S0, AO, Augment, + winner | CollabLLM, WildChat — both N=3 reps with reuse of paper prompts where possible | ~3-5 h | Replaces the multi-turn gating Phase from rev.2. Variance-bar redo of the paper-equivalent setup with our winning method. |
| **Future** | Multi-turn gating study | DeepSeek (then gpt-5.4) | Reset (always-on) vs Gated-Reset, S0, AO | Fresh multi-turn LiC sims | ~10-12 h | Deferred per user feedback. Re-eval after Phase 3 results. |

## Phase 1 cell math (rev.3)

- 4 tasks × **6** strategies (S0, AO, Augment, Reset, Gated-Reset, Rewrite) × 3 prefixes = **72 invocations**.
- Each: last-turn replay on 44-50 problems, wall ~30-90 s on DeepSeek (varies by strategy — Rewrite is slowest).
- Cache savings: Augment + Reset + Gated-Reset + Rewrite all use the same v8 analyzer output on each prefix → 4 strategies share 1 cached analysis. Out of 4×4×3 = 48 analyzing cells, only 4×3 = 12 unique (task, prefix) pairs need a fresh analyzer call. **~75% of analyzer queries are cached after the first variant per (task, prefix) finishes.**
- Total wall: roughly 1.5 h.

## Phase 2 cell math (rev.3)

- 3 models × 4 strategies (S0, AO, Augment, winner) × 4 tasks × 3 prefixes = **144 invocations**.
- gpt-5.4 dominates dollar cost (~$0.85 / 50-problem run, ~$50 total).
- Kimi dominates wall time (100 RPM cap).
- Within-model cache hits across Augment + winner.

## Phase 3 — Cross-benchmark error-bar redos (replaces rev.2's multi-turn gating)

Cross-benchmark validation that the winning AC3 variant survives outside LiC. Two sub-phases:

### 3a. CollabLLM N=3 redo

- Driver: `ctx-editor-collabllm` (i.e. `run_collabllm.py`).
- Tasks: math (MATH-Hard) and code (BigCodeBench) — the two CollabLLM tasks.
- Model: **DeepSeek-V4-Flash** initially. If Phase 2 picks a different headline model, run that too — it's a small batch.
- Strategies: S0, AO, Augment, + winning AC3 variant from Phase 1/2.
- N=3 sampling reps per (strategy, task). The original CollabLLM batch was N=1 with high variance (40-60% on math across seeds per `docs/reports/collabllm_baseline_comparison.md`); the N=3 here is specifically to put error bars on the headline numbers.
- Cell count: 4 strategies × 2 tasks × 3 reps = **24 invocations**.
- Wall time: each invocation is ~5-10 min on DeepSeek per the CollabLLM record → ~2 h.

### 3b. WildChat / Huang N=3 redo

- Driver: the post-refactor `huang_eval/strategies.py` exposes `HuangAC3{Augment, Reset, GatedReset, Rewrite}Strategy` so the same variant works.
- Phase structure: Huang's pipeline has its own Phase 1 (AO-failure detection) + Phase 2 (strategy evaluation on those). Our "redo" is the Phase 2 step.
- Model: DeepSeek-V4-Flash.
- Strategies: S0 (full context), AO, Augment, + winning AC3 variant.
- N=3 sampling reps per (strategy, conversation pool).
- Conversation pool: the existing 30-conversation WildChat sample from the paper (`outputs/huang_eval/...`).
- Cell count: 4 strategies × 1 pool × 3 reps = **12 invocations** (each one processes the full pool).
- Wall time: ~1-2 h based on the paper's Huang-eval timings.

### 3c. Total Phase 3 estimate

36 invocations, ~3-5 h. Fits comfortably in the same overnight slot as Phase 1+2 plus headroom.

### Scoping caveat

If Phase 2 reveals that the Augment ablation is essential (or that the winner differs by benchmark), we can extend Phase 3 with more variants. The 36-invocation budget above is the **minimum needed for error bars on the winning method**, not the full cross-benchmark sweep.

## Future work — multi-turn gating study (deferred)

Scoped exactly as rev.2 said but explicitly off the table for this batch. Re-evaluate after Phase 3 if gating is the bottleneck for the deployment-realism narrative; build incrementally then.

## Content filter — concrete monitoring + escalation

For each cell, we tail `content_filter_errors.jsonl` in the run dir and compute:

```
cf_rate = num_filtered_calls / num_total_analyzer_calls
```

per cell. Thresholds:

- `cf_rate == 0`: green; report as `v8`.
- `0 < cf_rate ≤ 5%`: yellow; report `v8 (CF skips: N)` and continue.
- `cf_rate > 5%`: red; abort the cell, re-run with `analyzer_prompt_version=s1`, mark in the per-cell metadata.
- `s1` cell still red: write up the cell as red-skipped, raise a flag, propose building v13 before Phase 2 expands to that variable.

Phase 1 on Foundry DeepSeek is expected green (no Azure-OAI route in the analyzer call path). Phase 2 on gpt-5.4 / gpt-5.5 is where we expect to need the escalation.

## Engineering deliverables (rev.3 — what we build before launching)

The list grew slightly vs rev.2 — splitting out the gating piece and the cross-benchmark cell math.

1. **Pricing file** `src/ctx_editor/models/foundry_pricing.yaml` — DONE, populated by user.
2. **Cost-merge wiring** `src/ctx_editor/models/base.py` — DONE.
3. **Analysis cache backend** `src/ctx_editor/strategies/analysis_cache.py` — new file.
4. **Registry / inspector** `scripts/inspect_analysis_cache.py` — new file.
5. **Analyzer integration** — add optional `cache=` kwarg to `ConversationAnalyzer.analyze()`, thread through strategies and the runner.
6. **Hydra knob** `experiment.analysis_cache=outputs/analysis_cache` default.
7. **`context_edit_v2_no_gate.yaml`** experiment config — `max_resets: 1, min_turns: 1` (always edit on final turn in replay).
8. **`context_edit_v2_gated.yaml`** experiment config — `max_resets: 3, min_turns: 3` (paper-default gating).
9. **`ac3_rewrite_lic.yaml`** experiment config — LiC adaptation of `collabllm_compaction.yaml`.
10. **Phase 1 launcher** `scripts/run_phase1_ac3_deepseek.sh` — 6 strategies × 4 tasks × 3 convs, with the cache.
11. **One-cell smoke** end-to-end on a small subset (1 task × 1 conv × 1 strategy) to confirm: replay + analyzer + accumulate + cache + gate-rate logging all wire up.
12. **Prompt design doc** `docs/analyzer_prompt_design_notes.md` — capture v8, s1, archived-v12, contingent-v13. Useful regardless of whether we build v13.

After Phase 1:

13. **Phase 2 launcher** `scripts/run_phase2_ac3_other_models.sh` (winner-aware).

After Phase 2:

14. **Phase 3 cross-benchmark launchers**: `scripts/run_phase3_collabllm_redo.sh` + `scripts/run_phase3_huang_redo.sh`.

## Budget summary

| Phase | Invocations | Wall time | Reported cost | Notes |
|---|---|---|---|---|
| Phase 1 (DeepSeek explore) | 72 | ~1.5 h | will fill in via pricing.yaml | 6 strategies incl. gating. |
| Phase 2 (3 other models) | 144 | ~5-6 h | ~$50 measurable (gpt-5.4 dominates) + tokens for Foundry models | Cache hits across Augment + winner. |
| Phase 3 (cross-benchmark redos) | 36 | ~3-5 h | smaller, mostly DeepSeek-Foundry tokens | |
| **Total this batch** | ~252 | ~10-12 h | ~$50 + tokens | Fits in one overnight slot. |
| Future: multi-turn gating | ~1200 | ~10-12 h | + DeepSeek tokens / gpt-5.4 $ | Held for later. |

## Risks and contingencies (rev.3)

| Risk | Mitigation |
|---|---|
| Azure CF trips on Phase-2 gpt-5.4/gpt-5.5 cells | Escalation: v8 → s1 → v13 (build only if needed). v13 design noted above. |
| Phase 1 winner is model-specific | Promote 2 variants to Phase 2 (Augment + winner of Reset/Gated/Rewrite); 3pp tiebreak rules documented above. |
| AC3-Rewrite LLM compaction adds noise | Cache analyzer output for variant-comparison cleanliness; if Phase-1 within-cell std > 8pp for Rewrite, flag as unstable, prefer Reset. |
| Cost unknown for unpriced models | Pricing file populated; token counts always logged regardless. |
| Output-dir collision | Every launcher uses `logging.output_dir=outputs/<runtag>/<exp>_<ts>` (≥ 2 levels deep). |
| Cache poisoning (bad prompt commit, etc.) | Cache key encodes prompt_version and analyzer_model; registry records experiment_origin → can invalidate per origin or full reset. |
| Phase 3 huang_eval port issues | If `HuangAC3{Variant}Strategy` classes have integration gaps (per `ac3_variants_per_benchmark.md`), defer 3b to a follow-up batch; report 3a alone. |

## Changes from rev.2

| Topic | rev.2 | rev.3 |
|---|---|---|
| Gating | Dedicated multi-turn fresh-sim Phase 3 (~10-12 h) | Folded into Phase 1 as a 6th strategy in last-turn replay. Multi-turn gating deferred to "future work". |
| Phase 3 | Multi-turn gating study | **Cross-benchmark error-bar redos** (CollabLLM + WildChat N=3 with winning AC3 method). |
| Content-filter chain | v8 → s1 → degraded | v8 → s1 → (build v13 if needed). s1's limitations documented. v13 design noted but not pre-built. |
| Prompt design doc | Implied but not on the deliverable list | Explicit deliverable: `docs/analyzer_prompt_design_notes.md` capturing v8/s1/v12/v13 history and trade-offs. |

## Ready-to-launch checklist (rev.3)

Pre-launch:

- [x] Pricing file populated by user.
- [ ] Analysis cache backend (`src/ctx_editor/strategies/analysis_cache.py`).
- [ ] Cache inspector (`scripts/inspect_analysis_cache.py`).
- [ ] `ConversationAnalyzer.analyze` cache integration.
- [ ] Hydra knob.
- [ ] `context_edit_v2_no_gate.yaml` + `context_edit_v2_gated.yaml` + `ac3_rewrite_lic.yaml`.
- [ ] Phase 1 launcher.
- [ ] `docs/analyzer_prompt_design_notes.md`.
- [ ] One-cell end-to-end smoke (1 task × 1 conv × 1 strategy with cache enabled; verify cache hit on rerun).

Then: user approval → execute Phase 1.

Pending your sign-off.

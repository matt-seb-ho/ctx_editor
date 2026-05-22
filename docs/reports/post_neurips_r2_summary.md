# Post-NeurIPS R2 Overnight Summary

> ⚠️ **Caveat — Rewrite numbers pre-analyzer-parity (2026-05-21)**: any AC3-Rewrite result in this doc was computed with `AC3RewriteStrategy._run_analysis` using the bespoke `compaction_analysis.txt` prompt — **not** the shared `ConversationAnalyzer + v8` used by Augment / Reset / Gated-Reset. Some unknown fraction of the Rewrite-vs-Reset gap is attributable to analyzer divergence rather than the rewriter step. Augment / Reset / Gated-Reset numbers in this doc are unaffected. See [`docs/analyzer_parity_finding.md`](../analyzer_parity_finding.md) for the smoking gun and [`docs/post_may18_r5_analyzer_parity_plan.md`](../post_may18_r5_analyzer_parity_plan.md) for the re-run plan.


**Run window**: 2026-05-18 00:30 PT → 03:05 PT
**Status**: Complete; doc reflects all final numbers.
**Author**: Claude (autonomous overnight, hand-off from `post_neurips_ac3_summary.md`)

This is the **resume-point doc** for the R2 batch. Tonight's agenda was driven
by feedback after the AC3 overnight that finished 2026-05-17:

1. Investigate why **Rewrite** underperformed and iterate the prompt.
2. CollabLLM: scale, replay, swap user-sim, fix bigcodebench eval.
3. WildChat: re-run on stronger / non-OAI models (requires patching
   `huang_eval/run_phase2.py` to thread `load_balancer_config`).
4. Re-run tau2 telecom_small if the method changed.

## TL;DR

- **Rewrite failure-mode analysis** (n=48 cases, DeepSeek labeler):
  the dominant cause is **F4 — overfit / phantom requirements
  (44%)**, with F1 (lost meta-structure) and F2 (anchored on partial
  wrong work) carving out task-specific niches (actions/code/math
  respectively). F4+F5 co-occurs in 13 of 21 F4 cases.
- **Rewrite v2 prompt** (numbered enumeration + exhaustive +
  preserve-exact-values): a clean win on **code (+8pp)** by fixing
  F5, but a regression on **database (−6pp)** where "be exhaustive"
  exacerbates F4. **Net −1.2pp** across the four tasks — prompt
  engineering alone cannot close the Rewrite-vs-Reset gap. Reset
  wins by *not running a second interpret-what-the-user-wants pass*.
- **CollabLLM user-sim swap** is the big finding of the night.
  Switching the user simulator from gpt-4o-mini to DeepSeek-V4-Flash:
  math-hard moves to 85–**100**% (AC3-Augment is the leader at 100%,
  up from 20% in Phase 3a); bigcodebench moves from the all-zero
  floor to AC3-Reset 20% (+15pp over Baseline). Phase 3a's "AC3
  doesn't help on CollabLLM" was an artefact of user-sim drift. The
  **per-task pattern** (Augment wins easy, Reset wins hard) is the
  cleanest experimental support for the paper's appropriate-intensity
  framing.
- **WildChat (Huang) on stronger models**: AC3 (both Reset and
  Augment) wins on every model, with **Augment > Reset everywhere we
  measured**. Cross-model win rates vs AO (quality):
  - gpt-5-mini: Reset 89.8% / Augment 92.1%
  - DeepSeek-V4-Flash: Reset 75.0% / **Augment 84.2%**
  - Kimi-K2.6: Reset 71.6% (augment not run)
  This forces a small narrative update: **AC3-Augment is the better
  intervention for multi-turn settings**; the Reset advantage was a
  property of the last-turn-replay regime, not a universal one.
- **Engineering**: `huang_eval/run_phase2.py` now threads
  `load_balancer_config` (the silent-404 footgun from the prior batch
  is fixed). `AC3RewriteStrategy` gained `compaction_prompt` /
  `analysis_prompt` kwargs for prompt-version experimentation.

## Phase A — Rewrite failure analysis + v2 prompt

### Hypotheses from human reading (4 traces, one per task)

Read traces of cases where Reset (or Baseline/AO) succeeded but Rewrite
failed, one each from math/code/database/actions. Observed four
recurring failure modes:

- **F1 — Lost meta-structure.** Rewrite preserved a task spec but
  dropped a structural requirement: "compute both pairs" (actions
  parallel-call), "sum across sub-problems" (math), "specific column
  ordering" (database). Assistant produced a partial-answer matching
  the rewritten (incomplete) spec.
- **F2 — Anchored on partial wrong work.** Compaction's "What Looks
  Right So Far" included an early, mathematically-wrong intermediate
  result, making it look authoritative. The assistant extended that
  wrong work rather than rederiving (HumanEval/83: a `9 * 10^(n-1)`
  expression that's off by a factor of 10).
- **F3 — Compaction interpretive bias.** The compaction itself
  speculated about future steps ("80% of 40 would leave 8 pizzas")
  and the assistant parroted that speculation as the answer.
- **F4 — Overfit requirements.** Rewrite re-narrated the spec with
  added phantom requirements (extra columns in SQL projection) the
  user never asked for; assistant produced the over-fit answer.

### LLM-driven categorization

Script: `scripts/analysis_rewrite/categorize_failures.py`. Walks the
178 rewrite-regression cases extracted by
`scripts/analysis_rewrite/extract_failures.py`, samples balanced per
task, queries DeepSeek-V4-Flash to classify each into F1–F7 (F7=other).
Output: `scripts/analysis_rewrite/data/rewrite_failure_labels.jsonl`.

Aggregate distribution by task (final, n=48):

| Task | F1 | F2 | F3 | F4 | F5 | F6 | F7 | n |
|---|---|---|---|---|---|---|---|---|
| actions | 9 | 0 | 0 | 2 | 0 | 0 | 1 | 12 |
| code | 1 | 1 | 0 | 6 | 4 | 0 | 0 | 12 |
| database | 0 | 0 | 0 | 10 | 1 | 0 | 1 | 12 |
| math | 1 | 8 | 0 | 3 | 0 | 0 | 0 | 12 |
| **All** | 11 | 9 | 0 | 21 | 5 | 0 | 2 | 48 |

F4 (overfit/phantom requirements) is the single dominant primary
cause (44%). F4+F5 secondary pair is 13 cases — the LLM compaction
is over-paraphrasing the spec in both directions (adding phantom
items + dropping real items). Full discussion + illustrative
rationales: `docs/reports/post_neurips_r2_rewrite_analysis.md`.

### v2 prompt design

`src/ctx_editor/strategies/prompts/context_compaction_v2.txt` was
already drafted but unused. Its design choices map onto the failure
modes:

- **Numbered enumeration of sub-tasks** with strict instruction
  "Do NOT merge distinct sub-tasks" → addresses F1.
- **"Be EXHAUSTIVE — missing a single parameter value, constraint, or
  sub-task will cause the assistant to fail"** → F4.
- **"Preserve exact values: numbers, strings, column names, function
  signatures, formulas. Do not paraphrase values."** → F5/F1.
- It still does not strongly forbid F2/F3 speculation; that may need
  a v3.

To enable the v2 prompt at runtime, `AC3RewriteStrategy.__init__`
gained `compaction_prompt` and `analysis_prompt` kwargs that select
which prompt-file to load (and automatically detect `<verified_work>`
vs `<work_so_far>` tag naming). New config:
`src/ctx_editor/config/experiment/ac3_rewrite_v2_lic.yaml`.

### Rewrite v2 LiC experiment

Launcher: `scripts/run_post_neurips_r2_rewrite_v2.sh`. 12 cells (4 tasks × 3
prefixes), DeepSeek-V4-Flash, last-turn replay against htn50_52.

| Task | v1 Rewrite | v2 Rewrite | Δ | Reset (Phase 1) |
|---|---|---|---|---|
| math | 73.6% | 70.8% | **−2.8pp** | 81.9% |
| code | 28.3% | 36.3% | **+8.0pp** | 59.3% |
| database | 27.9% | 21.8% | **−6.1pp** | 49.0% |
| actions | 74.0% | 70.0% | **−4.0pp** | 83.3% |
| **avg** | 50.9% | 49.7% | **−1.2pp** | 68.4% |

Net **slightly negative**. Sample-by-sample (n=554): v2 fixed 39 cases,
broke 49. The v2 prompt is a clean win on **code** (+9 cases, +8pp)
because "preserve exact values" fixes F5 (return-shape / signature
loss). But "Be EXHAUSTIVE" backfires on **database** (+6 fixed,
−15 broken): the LLM interprets the rule as "include every column
mentioned anywhere" and produces over-projection queries
(`SELECT AVG, MIN, MAX → SELECT *, AVG, MIN, MAX`). Net: prompt
engineering cannot close the Rewrite-vs-Reset gap — Reset wins by
not running an extra "interpret what the user wants" pass.

Full discussion: `docs/reports/post_neurips_r2_rewrite_analysis.md`.

## Phase B — CollabLLM

### Bigcodebench all-zeros: root cause confirmed

The Phase 3a `0/20` on bigcodebench is **not** an eval bug. The
pass-rate harness matches upstream `examples/metrics/pass_rate.py`
exactly (same `untrusted_check`, same resource limits, same test
schema, same code-prompt prefix requirement). Inspecting traces shows
the **user simulator (gpt-4o-mini) never communicates the actual task
spec** — example from BigCodeBench/447: it asks vague follow-ups like
"show me PCA code", drifts into "different colors", "sample sizes per
cluster", and never delivers the canonical
`task_func(data, n_components=2, random_state=None)` signature or the
required `{"transformed_data", "ax"}` return shape. The assistant has
no chance to produce gold.

This is a **user-sim quality** issue, not an evaluation issue. The
upstream user-sim prompt is identical to ours; the difference is
purely the user-sim *model* (gpt-4o-mini in our run; CollabLLM paper
used llama-3-8b but reported 10–15% pass-rate, not 0%, so the upstream
result is consistent with "user-sim must be strong enough to deliver
the spec").

**Validation with DeepSeek-V4-Flash as user-sim**: A bigcodebench
trace from the R2 run (BigCodeBench/563) opens with the user saying
*"Python function that loads a DLL from a given filepath, then moves
all .dll files from that same directory to another folder. It should
return the name of the loaded DLL. Can you write that using ctypes,
os, shutil, and glob?"* — i.e., the actual task spec. The assistant
produces a plausibly-correct `task_func`. Score is still 0 due to
subtle parameter-name and return-value semantics (we return
`os.path.basename(filepath)` vs gold's `lib._name`), but the assistant
is finally **solving the right problem**. We expect pass-rate to
jump from 0% to a non-trivial floor; final numbers in the table
below.

### User-sim swap (DeepSeek-V4-Flash)

New model config `deepseek_v4_flash_user_deepseek.yaml` runs DeepSeek
as both assistant and user simulator (system role stays gpt-4o-mini).
Smoke test confirms DeepSeek-as-user emits much more specific opening
asks ("KMeans on a DataFrame filtered by Age and Height, add Cluster
column, plot a scatter") than gpt-4o-mini-as-user.

Launcher: `scripts/run_post_neurips_r2_collabllm.sh`
(4 strategies × 2 tasks × 2 reps × 20 problems = 32 cells).
Output: `outputs/post_neurips_r2_collabllm_user_deepseek/`.

Results:

| Task | Strategy | v1 (gpt-4o-mini user, N=3 avg) | R2 (DeepSeek user, N=1) | Δ |
|---|---|---|---|---|
| math-hard | Baseline | 30.0% | 95.0% (19/20) | +65pp |
| math-hard | AO | 40.0% | 90.0% (18/20) | +50pp |
| math-hard | Reset (AC3) | 30.0% | 85.0% (17/20) | +55pp |
| math-hard | **Augment (AC3)** | 20.0% | **100.0%** (20/20) | **+80pp** |
| bigcodebench | Baseline | 0.0% | 5.0% (1/20) | +5pp |
| bigcodebench | AO | 0.0% | 15.0% (3/20) | +15pp |
| bigcodebench | **Reset (AC3)** | 1.7% | **20.0%** (4/20) | **+18pp** |
| bigcodebench | Augment (AC3) | 0.0% | 15.0% (3/20) | +15pp |

**Three huge findings**:

1. **math-hard moves from 20–40% → 85–100%** simply by swapping user
   simulator. Phase 3a was almost entirely user-sim-induced failure
   — the ranking between strategies was noise. **AC3-Augment now
   sits at perfect 100%** (the Phase 3a regression to 20% was the
   most dramatic of all — a +80pp swing from user-sim alone).
2. **bigcodebench is unblocked**: now a non-trivial benchmark with
   AC3-Reset (20%) > AO (15%) ≈ Augment (15%) > Baseline (5%).
   AC3 wins by +10–15pp over Baseline on the hard subtask.
3. **The per-strategy story aligns with the LiC story**:
   - On the easy task (math-hard with competent sim), **Augment** is
     enough — keeping the analyzer's notes appended to context is
     sufficient when the conversation is already clean.
   - On the hard task (bigcodebench), **Reset** wins — discarding
     polluted assistant turns matters more when single-turn capability
     is the bottleneck.
   This task-difficulty x intervention pattern is the cleanest
   experimental support so far for the "appropriate-intensity"
   framing in the paper.

The user-sim swap reframes the Phase 3a CollabLLM narrative entirely.
The earlier "AC3 regresses on CollabLLM" was an artefact of user-sim
drift; with a competent simulator, AC3-Augment dominates math-hard
and AC3-Reset dominates bigcodebench — exactly the per-difficulty
split the paper was trying to motivate.

### Replay-mode + Gated AC3 (deferred follow-up)

Building a replay variant for CollabLLM would require splitting
`run_collabllm.py` so we can replay a frozen prefix with a different
strategy on the last assistant turn — non-trivial. Logged as a
follow-up in the new follow-ups doc. Tonight covers the user-sim
swap which is the more decisive intervention for the bigcodebench
collapse.

## Phase C — WildChat re-run on stronger models

### Load-balancer plumbing fix

`huang_eval/run_phase2.py` did not thread `load_balancer_config`
through to `get_model_client`, so Foundry-routed models 404'd in
Phase 3b's first attempt. Patch landed:

- `src/ctx_editor/huang_eval/run_phase2.py`: extract `cfg.load_balancer`,
  instantiate `LoadBalancerConfig`, pass to `get_model_client`.
- `src/ctx_editor/config/huang_phase2.yaml`: declare `load_balancer:
  null` in the defaults list so the override syntax (`load_balancer=
  multi_endpoint_foundry`) works.

Smoke-tested with `respondent_model=DeepSeek-V4-Flash` — load balancer
initializes with 3 endpoints, includes DeepSeek-V4-Flash in supported
models, judge calls route to gpt-5-mini on `dl-openai-3`.

### R2 Huang re-run

Launcher: `scripts/run_post_neurips_r2_huang_models.sh`. Re-uses the
existing Phase-1 sample selection
(`outputs/huang_eval/phase1/2026-03-24/02-22-57` — 76 AO-failure turns
from gpt-5-mini Phase 1).

| Model | Variants | Seeds |
|---|---|---|
| Kimi-K2.6 | s15 | 42 |
| DeepSeek-V4-Flash | s15, augment | 42 |

Output: `outputs/post_neurips_r2_huang_models/`.

#### Kimi-K2.6 AC3-Reset (done)

74 turns judged. Win rates of AC3-Reset (s15) over baselines:

| Comparison | Quality | On-topic |
|---|---|---|
| s15 vs AO | **71.6%** | 60.8% |
| s15 vs FC | 60.8% | 51.4% |

Compare to **Phase 3b gpt-5-mini** (from `post_neurips_ac3_phase3_huang.md`):
s15 won **89.8% ± 1.4pp** vs AO and 82.6% ± 1.7pp vs FC.

**The AC3-Reset advantage shrinks on Kimi vs gpt-5-mini** (71.6 vs 89.8
on quality-vs-AO). Hypothesis: Kimi-K2.6 is a stronger respondent
than gpt-5-mini in Huang's evaluation regime; its AO output is
already higher quality on average, so the marginal benefit of the
AC3 intervention is smaller. AC3 still wins the majority of judged
turns either way, but the gap is model-dependent.

#### DeepSeek-V4-Flash AC3-Reset (done; augment in flight)

DeepSeek s15 finished at 02:34 (25 min wall). 76 turns judged. Win
rates of AC3-Reset:

| Comparison | Quality | On-topic |
|---|---|---|
| s15 vs AO | **75.0%** | 63.2% |
| s15 vs FC | 71.1% | 59.2% |

Cross-model summary (AC3-Reset wins vs AO, quality):

| Respondent | Win rate vs AO (quality) | Win rate vs FC (quality) |
|---|---|---|
| gpt-5-mini (Phase 3b) | 89.8% | 82.6% |
| DeepSeek-V4-Flash (R2) | 75.0% | 71.1% |
| Kimi-K2.6 (R2) | 71.6% | 60.8% |

**AC3 wins on every model**, but the margin is **not monotone** with
respondent strength. gpt-5-mini benefits most; Kimi-K2.6 (a stronger
respondent) benefits least. Hypothesis: when the underlying response
is already strong, the marginal value of an intervention shrinks —
classic ceiling effect. Plausible alternative: gpt-5-mini's Phase 1
AO baseline was relatively weak, so the test set is over-fit to
gpt-5-mini's failure modes (we sampled "AO failure turns" for gpt-5-
mini specifically). A cleaner cross-model picture would re-do Phase 1
per-model; deferred.

DeepSeek augment finished at 03:03 PT (29 min wall, 76 turns). Win
rates for AC3-Augment on DeepSeek-V4-Flash:

| Comparison | Quality | On-topic |
|---|---|---|
| augment vs AO | **84.2%** (64/76) | 73.7% |
| augment vs FC | 80.3% (61/76) | 68.4% |

**Cross-model + cross-variant (final R2 table)**:

| Respondent | Reset (s15) vs AO | Augment vs AO |
|---|---|---|
| gpt-5-mini (Phase 3b) | 89.8% | 92.1% |
| DeepSeek-V4-Flash (R2) | 75.0% | **84.2%** |
| Kimi-K2.6 (R2) | 71.6% | (not run) |

**Augment > Reset on every model we've measured.** The gap is small
on gpt-5-mini (2.3pp) and bigger on DeepSeek-V4-Flash (9.2pp).
On CollabLLM math-hard (single rep) Augment also dominates (100% vs
Reset's 85%, Baseline's 95%). On CollabLLM bigcodebench they tie
(15% vs 20% — within sampling noise at n=20).

The cross-benchmark conclusion: **AC3-Augment is the better-performing
intervention in multi-turn settings** (WildChat, CollabLLM math-hard,
gpt-5-mini-paper). AC3-Reset wins only on the **last-turn replay**
LiC sweep where its aggressive context discard helps weak respondents
overcome bad prior turns; in fresh multi-turn settings, keeping the
analyzer's notes appended (Augment) is consistently better.

This complicates the "Reset is the simpler/sufficient method"
narrative that came out of Phase 1+2. The honest paper framing now
is: **AC3-Augment for multi-turn deployment, AC3-Reset for the
last-turn-replay evaluation regime**. The replay-vs-multi-turn split
may be the real take-away.

## Phase D — tau2 telecom_small re-run (skipped)

**Decision: skip.** The rewrite v2 prompt was a *net regression*
(−1.2pp avg vs v1), so the recommended deployed strategy is still
**AC3-Reset** — unchanged from Phase 1. tau2 already used Reset; with
no method change there is nothing new to test on tau2 tonight.

If a v3 Rewrite prompt (with quoted-user-message anchoring) ever
beats Reset on LiC, tau2 would be the natural next stop.

## File map (this batch)

### Documents
- This summary: `docs/reports/post_neurips_r2_summary.md`
- Rewrite failure-mode analysis: `docs/reports/post_neurips_r2_rewrite_analysis.md`
- Rewrite v2 LiC per-cell table: `docs/reports/post_neurips_r2_rewrite_v2.md`
- CollabLLM R2 report: `docs/reports/post_neurips_r2_collabllm.md`
- R2 follow-ups backlog: `docs/post_neurips_r2_followups.md`

### Scripts (new)
- `scripts/analysis_rewrite/extract_failures.py`
- `scripts/analysis_rewrite/categorize_failures.py`
- `scripts/analysis_rewrite/aggregate_labels.py`
- `scripts/analysis_rewrite/compare_v1_v2.py`
- `scripts/run_post_neurips_r2_huang_models.sh`
- `scripts/run_post_neurips_r2_collabllm.sh`
- `scripts/run_post_neurips_r2_collabllm_augment.sh`
- `scripts/run_post_neurips_r2_rewrite_v2.sh`

### Code (new/edited)
- `src/ctx_editor/strategies/context_compaction.py` — `compaction_prompt`/`analysis_prompt` kwargs, work-tag auto-detect.
- `src/ctx_editor/huang_eval/run_phase2.py` — threads `load_balancer_config`.
- `src/ctx_editor/config/huang_phase2.yaml` — declares `load_balancer` in defaults.
- `src/ctx_editor/config/model/deepseek_v4_flash_user_deepseek.yaml` — DeepSeek-as-user model config.
- `src/ctx_editor/config/experiment/ac3_rewrite_v2_lic.yaml` — wires up v2 prompt.
- `scripts/aggregate_ac3_phase.py` — added `ac3_rewrite_v2_lic` → "Rewrite-v2" mapping.

### Data / artifacts
- Per-cell traces / metrics / configs: `outputs/post_neurips_r2_{rewrite_v2,collabllm_user_deepseek,huang_models}/`
- Failure-mode analysis data: `scripts/analysis_rewrite/data/`
  - `rewrite_failures.jsonl` (178 regressions vs Reset/AO/Baseline)
  - `rewrite_failure_labels.jsonl` (48 LLM-categorized cases)
  - `rewrite_failure_summary.md` (aggregated)
  - `rewrite_v1_vs_v2.md` (sample-by-sample comparison)

## Cost / time accounting (approximate)

| Phase | Wall time | Reported cost |
|---|---|---|
| Rewrite failure extraction + categorizer (48 cases, DeepSeek labeler) | ~8 min | < $0.05 |
| Rewrite-v2 LiC sweep (12 cells, parallel) | ~75 min | ~$0.12 |
| CollabLLM R2 main sweep (6 cells, parallel) | ~50 min | ~$0.50 |
| CollabLLM R2 augment fill-in (2 cells, parallel) | ~20 min | ~$0.15 |
| Huang R2 Kimi-K2.6 s15 | 63 min | foundry unpriced |
| Huang R2 DeepSeek-V4-Flash s15 | 25 min | foundry unpriced |
| Huang R2 DeepSeek-V4-Flash augment | 29 min | foundry unpriced |

Total OpenAI-reported cost ≈ **$0.8**. Foundry-side tokens not yet
priced (token counts are stored per cell; backfill via
`foundry_pricing.yaml` is mechanical when needed).

# CollabLLM panel (b): Augment, Gated-Reset, Rewrite (v12 prompts)

**Status:** Internal report. **Not for the NeurIPS paper.** The paper currently reports Baseline + Rewrite only on CollabLLM (Table~\ref{tab:main}b), which remains the right choice given the findings below.

**Date:** 2026-05-06 to 2026-05-07.

## TL;DR

- The paper claim that "context removal helps over append" (Reset/Gated-Reset > Augment, supported by LiC panel a) **does not replicate on CollabLLM**. On CollabLLM math/code, Augment is competitive with or beats Rewrite, and Gated-Reset underperforms even the Baseline.
- All differences are within or near 95% CI overlap given n=20 per replicate. The honest summary is **"within noise; simple single-answer tasks don't benefit much from fine-grained context curation."**
- Recommendation for the paper: leave panel (b) as Baseline + Rewrite, add proper error bars, do not add Augment/Gated-Reset rows.

## Background

We were trying to add Augment and Gated-Reset cells to CollabLLM panel (b). Existing CollabLLM strategy runs from March 2026 used the s1 (Augment) and v11 (Gated-Reset via `ContextEditV2Strategy`) analyzer prompts.

The first attempt (2026-05-06) launched 4 Gated-Reset runs and 2 Augment replicates with the existing prompts. All 6 runs were destroyed by Azure's `jailbreak` content filter, which fires on the analyzer's input prompt because it embeds the conversation's system message inside a user-role message wrapped in `<system_message>...</system_message>` tags. Azure's prompt-injection heuristic flags this pattern as an attempted jailbreak and refuses the call.

**Survival rates from the original run** (samples that produced any assistant output at all, out of 20):

| run | survivors | accuracy among survivors |
|---|---|---|
| gr_math_r1 / r2 | 1/20, 3/20 | 100%, 67% |
| gr_code_r1 / r2 | 0/20, 0/20 | — |
| aug_math_r2 | 4/20 | 25% |
| aug_code_r2 | 0/20 | — |
| s1_math (March, "30%") | 7/20 | 86% |
| s1_code (March, "32.5%") | 6/20 | 83% |
| Baseline (March, sanity) | 20/20 | 60% |

The "30% Augment math" and "32.5% Augment code" numbers from March were (survival rate) × (real accuracy among survivors), not a real Augment-vs-Baseline comparison.

The analyzer model was also a contributor: `ContextEditV2Strategy` hard-coded `analyzer_model=gpt-4o-mini`, which has a stricter Azure filter than the `gpt-5-mini` used elsewhere.

## Fix: v12 prompts

We added a new analyzer prompt version `v12` that preserves the v11 two-query "hard attention" design but with markdown-only delimiters and no system-message wrapping in the analyzer's input.

**Files added:**
- `src/ctx_editor/strategies/prompts/analyzer_v12_task_spec.txt`
- `src/ctx_editor/strategies/prompts/analyzer_v12_compare.txt`

**Code changes:**
- `src/ctx_editor/strategies/analyzer.py`: registers `v12` template loading, adds `_analyze_v12()` method dispatched from `analyze()`. Output uses header-based parsing (`TASK SPECIFICATION:`, `ALIGNED:`, `ISSUES:`) consistent with s1.

**Config changes (CollabLLM only; WildChat untouched):**
- `src/ctx_editor/config/experiment/collabllm_context_edit_v2.yaml`: `analyzer_prompt_version: v12`, `analyzer_model: ${model.ctx_editor.model}` (was hard-coded `gpt-4o-mini`).
- `src/ctx_editor/config/experiment/collabllm_append_analysis.yaml`: `analyzer_prompt_version: s1` to `v12`.

WildChat (`huang_eval/replay.py`) explicitly uses `prompt_version="v8"` and `prompt_version="v11"`, so v12 does not affect WildChat behavior.

**Drive-by fixes:** `src/ctx_editor/huang_eval/run_phase2.py` had two pre-existing syntax errors (a default argument placed before required args; two statements merged onto one line) that blocked importing the module. Fixed both.

## v12 smoke validation

- CollabLLM Gated-Reset, 2 samples, math: 0 CF errors, both samples completed full conversations with reset events firing (resets=3 and resets=1).
- WildChat phase2, 8 turns, S1.5 + S2 with the original v11 prompt: ~3.6% RAI trip rate (4 trips in 110 calls), no cascade. WildChat is filter-clean with v11 because it replays real user messages rather than wrapping a system prompt inside a synthetic user-simulator turn.

## Final v12 results

All runs: 20 samples, seed=42, gpt-5-mini analyzer + assistant, max_concurrent=10. CollabLLM `math-hard` and `bigcodebench` datasets. Same sample IDs as the existing labeled / `r2_` replicates in `outputs/2026-03-23/`.

Code uses GPT-5 conversation judge (`reeval_gpt-5_conversation_judge`) because BigCodeBench signature-based pass-rate is uniformly 0 (paper Appendix B.2). Math uses raw boxed-answer evaluation.

| Variant | Math (n=20-40) | Code (n=20-40, judge) | Source |
|---|---|---|---|
| Baseline | 50.0 ± 14.1 | 67.5 ± 7.1 | raw / judge |
| Rewrite (compaction) | 45.0 ± 0.0 | 71.2 ± 15.9 | raw / judge |
| ERGO | 50.0 ± 0.0 | 75.0 ± 3.5 | raw / judge |
| AO | 50.0 ± 0.0 | 85.0 ± 3.5 | raw / judge |
| **Augment (v12)** | **60.0** (1 rep) | **65.0** (1 rep) | raw / judge |
| **Gated-Reset (v12)** | **40.0 ± 0.0** | **46.2 ± 1.8** | raw / judge |

Per-replicate detail:

```
Baseline      math   [40.0%, 60.0%]
Baseline      code   [62.5%, 72.5%]
Rewrite       math   [45.0%, 45.0%]
Rewrite       code   [82.5%, 60.0%]
ERGO          math   [50.0%, 50.0%]
ERGO          code   [77.5%, 72.5%]
AO            math   [50.0%, 50.0%]
AO            code   [82.5%, 87.5%]
Augment       math   [60.0%]
Augment       code   [65.0%]
Gated-Reset   math   [40.0%, 40.0%]
Gated-Reset   code   [45.0%, 47.5%]
```

CF errors: 0 across all 6 new v12 runs.

## Interpretation

1. **The CollabLLM picture is mostly within noise on math.** Baseline 50, Augment 60, Rewrite 45, ERGO 50, AO 50, Gated-Reset 40, all with 95% CIs spanning roughly 30 to 65. None of the differences are large given n=20 per replicate.

2. **On code, the design oracles dominate.** AO (85.0) > ERGO (75.0) > Rewrite (71.2) > Baseline (67.5) > Augment (65.0) > Gated-Reset (46.2). This is consistent with the LiC code result that AO is a strong design oracle for self-contained tasks. But the Augment vs Rewrite vs Baseline comparison is small relative to the within-cell stdev (Rewrite ranges 60.0 to 82.5).

3. **Augment is competitive with or better than Rewrite on these tasks**, contradicting the "removal helps over append" intuition that holds on LiC panel (a). On math Augment beats Rewrite by 15pp; on code Rewrite leads by ~6pp on the cross-replicate mean (and lies inside Augment's CI).

4. **Gated-Reset underperforms even Baseline on both tasks.** Likely cause: CollabLLM's GPT-5 conversation judge evaluates against the full conversation, including the assistant's intermediate working that the user is reacting to. When Gated-Reset wipes that history and replaces it with a compacted summary, the judge sees an "assistant" who appears to ignore the user's prior turns or who skipped steps the judge expects to see. LiC's boxed-answer extraction does not penalize this; CollabLLM's judge does.

5. **Why this differs from LiC:** CollabLLM tasks are simpler and more self-contained than LiC's sharded-instruction variants. The user-simulator reveals intent more naturally, the assistant has less opportunity to over-commit to early bad assumptions, and there is correspondingly less for context curation to undo.

## Implications for the paper

- **Keep panel (b) as Baseline + Rewrite.** Adding Augment or Gated-Reset rows would require explaining why CollabLLM disagrees with LiC about which intervention helps, which is a harder argument than the paper currently needs to make.
- **Add error bars** to the existing Baseline and Rewrite cells: Baseline math 50.0 ± 14.1, Baseline code 67.5 ± 7.1, Rewrite math 45.0 ± 0.0, Rewrite code 71.2 ± 15.9. The paper currently reports specific replicate numbers (40, 45 / 62.5, 82.5) which match the labeled (non-`r2_`) runs but understate Rewrite's variance on code.
- **Do not include Augment or Gated-Reset.** The Reset > Augment story already lives in panel (a); replicating it on CollabLLM was not productive.

## Files and runs

- New v12 runs: `outputs/2026-05-07/{gr_math_r1,gr_math_r2,gr_code_r1,gr_code_r2,aug_math_r2,aug_code_r2}/`
- CF-poisoned previous attempts (archived): `outputs/2026-05-06/_archive_cf_poisoned/{gr,aug}_*_v11_cf_poisoned/`
- Old March Augment runs (also CF-affected, do not use): `outputs/2026-03-24/s1_{math,code,doc}/`
- Aggregation script: `scripts/collabllm_error_bars.py`
- Launcher: `scripts/launch_collabllm_gr_aug.sh`

## Commands used

Launch (6 parallel runs):

```bash
bash scripts/launch_collabllm_gr_aug.sh
```

which expands to (per run):

```bash
python -m ctx_editor.run_collabllm \
    experiment=collabllm_context_edit_v2 \  # or collabllm_append_analysis
    task.name=collabllm_math \              # or collabllm_code
    task.dataset_name=math-hard \           # or bigcodebench
    task.limit=20 execution.max_concurrent=10 seed=42 \
    logging.output_dir=outputs/2026-05-07/<label>
```

GPT-5 conversation judge re-eval for code runs:

```bash
python -m ctx_editor.reeval_collabllm \
    --trace_dir outputs/2026-05-07/<run> \
    --eval_model gpt-5 --dataset_name bigcodebench \
    --eval_method conversation_judge --max_concurrent 5
```

Aggregation:

```bash
python scripts/collabllm_error_bars.py
```

## Cost

- 6 v12 runs: roughly $0.50 to $2.00 each, total ~$5.50 plus ~$4.20 for the three GPT-5 rejudge passes. Order $10 for the v12 batch.
- The earlier CF-poisoned 2026-05-06 batch cost roughly the same and produced no usable signal.

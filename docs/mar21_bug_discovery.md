# Bug Discovery: `<context_edit_notes>` Injected into System Prompt for S1.5 Runs

**Date**: 2026-03-21
**Discovered during**: Prior work baseline comparison experiments

## The Bug

`scripts/run_s15_experiment.py` (lines 177-181) injects the analysis `issues` section into the **system message** as `<context_edit_notes>`:

```python
issues = analysis.get("issues", "")
if issues and issues.strip().lower() != "none":
    notes = f"\n\n<context_edit_notes>\n{issues}\n</context_edit_notes>"
    messages[0]["content"] += notes  # appends to system message
```

This means every S1.5 run has the analyzer's issue descriptions — natural language prose about what the assistant did wrong — appended to the system prompt. This is problematic because:

1. **S1.5 already removes the contaminated conversation.** The issues describe errors in work the assistant can no longer see. There's no clear reason to tell the model "here's what you did wrong" when the wrong work has been deleted.
2. **On structured output tasks** (actions, database), the system prompt says things like "You should only return the function calls" or "Return only SQL", and then we inject paragraphs of analysis prose into it.
3. **The issues can be actively misleading.** Example: on `parallel_195`, the issues flagged `extra_info=true` as "an assumption about output verbosity that may be unnecessary" — the model then omitted it, but the ground truth required it.

## What's Affected

### Affected (all use `run_s15_experiment.py`)

All S1.5 runs from the v8 batch (2026-03-16/17):
- S1.5 (no mem): math, code, database, **actions** — paper Table 1 "Context Edit" row
- S1.5 + mem: math, code, database, actions — paper Table 2 "Context Edit + Memory" row
- S1.5 + mem + sanitize: math, code, database — paper Table 2 "Context Edit + Memory" row (sanitized variant used for database)

All S1.5 runs from the spec-curation eval (2026-03-20):
- S1.5-soft-cot (no mem): math, code, database — paper Table 6
- S1.5-soft-cot + mem: math, code, database — paper Table 6
- S1.5-speconly (hard attn): math, code, database — paper Table 6

### NOT Affected

- **S0, S0+mem** (baseline) — no analysis, no notes
- **S1, S1+mem** (append analysis) — analysis appended as a separate conversation message via the main pipeline, not injected into system prompt
- **S2, S2+mem** (gated context edit) — uses `ContextEditV2Strategy._build_edited_context()` which does NOT inject issues into system message; issues only guide the edit/no-edit decision
- **All S1 soft-attention variants** — run through the main pipeline (`append_analysis_soft_cot*.yaml`)
- **CollabLLM experiments** — use `ContextCompactionStrategy` which does not inject notes

## Impact Assessment on Actions

We ran a 2×2 factorial (notes × accumulate instruction) on actions to isolate the effect:

| | With notes | No notes |
|---|---|---|
| **No accumulate** | 30% (7/23) | 13% (3/23) |
| **Accumulate** | 57% (13/23) | 61% (14/23) |

Without the accumulate instruction, the notes were *accidentally helping* — they described missing function calls, which nudged the model to include them. This was compensating for a separate evaluation artifact (the model thinks "aligned" work is already submitted and only generates the remaining calls). With the accumulate instruction providing a clean fix for that problem, removing notes gives a small +4pp improvement.

## Impact on Other Tasks

Unknown — not yet re-run. Math, code, and database do not have the accumulation problem (single-answer tasks), so the notes effect there is purely about whether the issue descriptions help or hurt the model's fresh attempt. This needs to be tested.

## Fix

Added `--no-notes` flag to `run_s15_experiment.py` and `accumulate_instruction` parameter to `ContextEditV2Strategy`. The default behavior is unchanged (notes are still injected) to preserve reproducibility of prior runs.

## Output Directories

| Run | Result | Dir |
|-----|--------|-----|
| S1.5 original (notes, no acc) | 30% (7/23) | `outputs/2026-03-17/01-28-08` |
| S1.5 (notes + accumulate) | 57% (13/23) | `outputs/2026-03-21/08-06-56` |
| S1.5 (no notes + accumulate) | 61% (14/23) | `outputs/2026-03-21/08-52-37` |
| S1.5 (no notes, no accumulate) | 13% (3/23) | `outputs/2026-03-21/08-52-38` |

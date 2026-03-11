# Changelog: V2/V3 Prompt Redesign + Memory Fixes

## Summary

This change set covers the V2/V3 prompt redesign for context editing strategies,
mechanical infrastructure fixes, memory learning improvements, and the experiment
results on the code task (n=20).

## Strategy Changes

### Prompt Versioning (`strategies/prompt_registry.py` — NEW)
- Central registry for versioned editor and decision prompts (V2, V3)
- Strategies accept `prompt_version` parameter to select prompts via config
- V2: Clean structured output (`<user_intent>` + `<approach_evaluation>`) without guardrails
- V3: Same structure + guardrails (don't invent details, don't over-flag ambiguity)

### Context Edit Strategy (`strategies/context_edit.py`)
- Added `prompt_version`, `editor_timeout`, `max_resets` parameters
- `max_resets=3` prevents infinite reset loops (was unlimited, up to 9 resets observed)
- Timeout properly threaded from config (was defaulting to 30s instead of 60s)
- `editor_reasoning_effort` support (but should NOT be used — degrades quality)

### Agentic Edit Strategy (`strategies/agentic_edit.py`)
- Added `prompt_version` — loads decision prompt from registry AND passes to inner ContextEditStrategy
- V3 decision prompt uses numbered questions format (gpt-5-mini ignores XML tags)
- Editor timeout properly threaded
- Decision call explicitly does NOT pass reasoning_effort (editor needs full reasoning)

### Saved Prompts (`strategies/saved_prompts/` — NEW)
- `v2_best_math_prompts.py`: Preserved V2 prompts that produced best math results (5/9 = 55.6%)

## Memory / Cheatsheet Fixes

### CheatsheetUpdater (`memory/cheatsheet.py`)
- Added `timeout` parameter (default 60) — all three `model_client.generate()` calls now pass timeout
- Previously crashed at 25-50% completion due to timeout on gpt-5-mini calls

### Memory Updater Model (`run_experiment.py`)
- `CheatsheetUpdater` now uses `cfg.model.ctx_editor.model` (was defaulting to gpt-4o-mini)
- Also passes `timeout` from config

### Cheatsheet Size Cap (reflection/unify prompts)
- All reflection prompts and unify prompt now include SIZE LIMIT: 500-1500 words
- Prevents unbounded growth (previously 16-19K chars by batch 4, consuming 65% of editor prompt)
- Capped cheatsheets stay at ~1000-1100 words (~7-8K chars)

### Reflection Prompt Improvements
- `context_editor_reflection.txt`: Added size limit, more specific guidance
- `context_editor_reflect_takeaways.txt`: Better examples of good/bad takeaways
- `unify_takeaways.txt`: Rewritten with explicit BAD/GOOD examples to prevent genericization
- `assistant_reflection.txt`, `edit_decision_reflection.txt`: Added size limits

## Config Changes

### Experiment Configs
- `context_edit.yaml`: Added `prompt_version: v3`, `editor_timeout`, `max_resets: 3`, `use_memory`, `memory_target`
- `agentic_edit.yaml`: Added `prompt_version: v3`, `decision_model`, `editor_timeout`, `edit_threshold_turns`, `use_memory`, `memory_target`
- `context_edit_memory.yaml` (NEW): Same as context_edit with `use_memory: true`
- `agentic_edit_memory.yaml` (NEW): Same as agentic_edit with `use_memory: true`
- `baseline_memory.yaml` (NEW): Baseline with memory injection

## Infrastructure

### Error Handling (`execution/batched.py`, `execution/parallel.py`)
- Error result trace type fixed: `trace=[]` → proper dict structure
- Added filter to skip error results before passing to `batch_update()`

## Experiment Results (Code Task, n=20)

| Config                              | Result     |
|-------------------------------------|------------|
| Baseline                            | 4/19 (21%) |
| Reflection                          | 6/20 (30%) |
| Context edit V1 (no fixes)          | 2/19 (11%) |
| Context edit V2 + fixes             | 7/20 (35%) |
| Context edit V2 + fixes + memory    | 4/19 (21%) |
| **Context edit V3 + fixes**         | **9/20 (45%)** |
| Context edit V3 + fixes + memory    | 7/19 (37%) |
| Agentic edit V1                     | 2/18 (11%) |
| Agentic edit V3 + fixes             | 7/20 (35%) |

## Documentation (NEW files)
- `docs/code_experiment_analysis.md`: Detailed V1 failure analysis on code task
- `docs/code_v2b_trace_analysis.md`: V2 trace-level analysis
- `docs/false_negatives_and_test_subset.md`: Test subset filtering methodology
- `docs/plans/experiment_runs_math_code.md`: Full experiment tracking with all results

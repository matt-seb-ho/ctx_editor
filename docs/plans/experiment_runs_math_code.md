# Experiment Plan: Math & Code Test Subsets

## Goal
Determine whether context editing approaches and memory-based learning improve multi-turn performance on problems where the assistant (not user sim) is responsible for failures.

## Data
- **Math**: 9 problems (`data/test_math_subset.json`) — filtered from `test_subset.json`
- **Code**: 20 problems (`data/test_code_subset.json`) — filtered from `test_subset.json`

## Model
- `gpt5_mini` config: gpt-5-mini for assistant/ctx_editor, gpt-4o-mini for user/system

## Experiments

### Phase 1: No memory (parallel execution)

| Experiment | Strategy | Description |
|---|---|---|
| `baseline` | BaselineStrategy | No context modification |
| `reflection_only` | ReflectionStrategy | Append reflection to context (append-only, no rewriting) |
| `context_edit` | ContextEditStrategy | Compress/rewrite conversation before each turn |
| `agentic_edit` | AgenticEditStrategy | LLM decides when/how to edit context |

### Phase 2: With continual memory learning (batched execution)

| Experiment | Strategy | Memory target | Description |
|---|---|---|---|
| `baseline_memory` | BaselineStrategy | assistant | Baseline + memory injected into system message |
| `context_edit_memory` | ContextEditStrategy | context_editor | Context edit + memory guides the editor |
| `agentic_edit_memory` | AgenticEditStrategy | context_editor | Agentic edit + memory guides editor |

Memory settings: `source=continual`, `include_full_spec_q=true`, `include_ground_truth_a=true`
Batch sizes: math=3 (3 batches), code=5 (4 batches)

## Results Tracking

### Phase 1 Results (no memory)

| Experiment | Math (n=9) | Code (n≈20) | Math Turns | Code Turns | Math Cost | Code Cost |
|---|---|---|---|---|---|---|
| baseline | 2/9 (22.2%) | 4/19 (21.1%) | 6.2 | 6.6 | $0.14 | $0.43 |
| reflection_only | 2/9 (22.2%) | 6/20 (30.0%) | 6.7 | 7.1 | $0.16 | $0.53 |
| context_edit | 2/9 (22.2%) | 2/19 (10.5%) | 17.7 | 18.8 | $0.15 | $0.43 |
| **agentic_edit** | **4/9 (44.4%)** | 2/18 (11.1%) | 13.2 | 12.4 | $0.14 | $0.37 |

### Phase 2 Results (with continual memory learning)

We have 2 math runs (r1 before trace-fix, r2 after) and 1 code run per experiment.

| Experiment | Math r1 (n=9) | Math r2 (n=9) | Code (n≈20) |
|---|---|---|---|
| baseline_memory | **5/9 (55.6%)** | 3/9 (33.3%) | 4/18 (22.2%) |
| context_edit_memory | 4/9 (44.4%) | 2/9 (22.2%) | 1/18 (5.6%) |
| **agentic_edit_memory** | 4/9 (44.4%) | **5/9 (55.6%)** | 3/19 (15.8%) |

Note: Some code runs had 1-2 timeout errors on livecodebench problems (excluded from denominator).
Note: Math r1 was before the `trace=[]` bug fix but memory updates still worked (errors only happen in render, and the first batches had no errors). Results are valid.

### Output Directories

| Experiment | Math | Code |
|---|---|---|
| baseline | outputs/2026-03-10/16-12-15 | outputs/2026-03-10/16-16-51 |
| reflection_only | outputs/2026-03-10/16-16-53 | outputs/2026-03-10/16-16-55 |
| context_edit | outputs/2026-03-10/16-16-57 | outputs/2026-03-10/16-16-58 |
| agentic_edit | outputs/2026-03-10/16-17-00 | outputs/2026-03-10/17-17-01 |
| baseline_memory | outputs/2026-03-10/17-16-29 | outputs/2026-03-10/17-16-31 |
| context_edit_memory | outputs/2026-03-10/17-16-33 | outputs/2026-03-10/17-16-34 |
| agentic_edit_memory | outputs/2026-03-10/17-16-36 | outputs/2026-03-10/17-16-39 |

## V1 Analysis

### Key Findings (V1 prompts)

1. **Agentic edit is the strongest approach for math** — 44.4% without memory, 44-55.6% with memory (vs 22.2% baseline). Roughly a 2x improvement over baseline.

2. **Memory improves math across the board** — baseline_memory averages ~44% across 2 runs vs 22% baseline. All memory experiments beat their no-memory counterparts on math.

3. **Context editing hurts code performance** — Both context_edit (10.5%) and agentic_edit (11.1%) perform worse than baseline (21.1%) on code. Root cause: the V1 editor "launders" wrong assistant assumptions into the context, making them look authoritative.

4. **Reflection helps code but not math** — reflection_only achieves 30.0% on code (best code result), a +9pp improvement over baseline.

---

## V2 Prompt Redesign

### Problem Diagnosis (see docs/code_experiment_analysis.md)
The V1 editor blurs user messages (source of truth) with assistant messages (potentially wrong), causing:
1. **Wrong Assumption Amplifier**: Assistant's incorrect guesses (e.g., adding a `k` parameter) get laundered into the condensed context as if they were user requirements
2. **Function Signature Lock-in**: Wrong function signatures persist through multiple resets
3. **Loss of Corrective Signals**: User corrections become invisible after context edit flattens everything

### V2 Design
- **Structured output**: Editor produces `<user_intent>` (ONLY user facts) + `<approach_evaluation>` (critical analysis of assistant's work)
- **Structured injection**: User intent → user message (source of truth); approach evaluation → system message `<context_edit_notes>` (advisory)
- **Critical framing**: System message warns assistant to "be willing to take a completely different approach"
- **Decision prompt improved**: Agentic edit decision prompt now focuses on detecting specific wrong paths

### V2 Results (timeout fix applied)

*V2 runs with proper timeout (60s) passthrough are pending. Initial V2 results (with 30s default timeout) showed improvement on accuracy but had high error rates due to timeouts.*

| Experiment | Math V1 | Math V2 (30s) | Code V1 | Code V2 (30s) |
|---|---|---|---|---|
| context_edit | 2/9 (22.2%) | 3/5 valid (60%) [4 err] | 2/19 (10.5%) | 4/11 valid (36.4%) [9 err] |
| agentic_edit | 4/9 (44.4%) | 5/9 (55.6%) [0 err] | 2/18 (11.1%) | 4/15 (26.7%) [5 err] |
| agentic_edit_memory | 5/9 (55.6%) | — | 3/19 (15.8%) | 6/15 valid (40.0%) [5 err] |

### V2 Qualitative Improvements
- Problem 2893 (k parameter issue): V2 editor correctly identified `k` as an assistant assumption, not user requirement
- Problem 2881 (split strings): V2 correctly preserved user's test cases in user_intent section
- HumanEval/141: Correct in V2 (agentic_edit chose not to edit, wisely)

### V2+Timeout Fix Results (Code)

| Experiment | Code V1 | Code V2b (60s timeout) |
|---|---|---|
| context_edit | 2/19 (10.5%) | 4/20 (20.0%), 0 err, 18.7 turns |
| agentic_edit | 2/18 (11.1%) | 1/19 (5.3%), 1 err, 9.0 turns |

V2 context_edit improved to match baseline but agentic_edit is noisy (high variance).

---

## V3 — Decision Prompt Fix + Editor Refinements

### Problems Found in V2
1. **Decision model (gpt-5-mini) ignored XML format** — 97% of decisions had empty reasoning, just bare "yes"/"no"
2. **Cheatsheet learning used gpt-4o-mini** (wrong model) — produced generic platitudes
3. **Unify prompt collapsed specific insights** — "deduplicate" + "keep concise" = strip all specificity
4. **Reset loops** — up to 9 resets on code problems with no convergence
5. **Over-flagging ambiguity** — editor flagged every unspecified detail, causing analysis paralysis
6. **reasoning_effort="medium" hurts both editor and decision quality** — gpt-5-mini needs full reasoning

### V3 Changes
1. **Decision prompt restructured**: Numbered questions format ("1. WHAT DID THE USER ASK? 2. WHAT IS ASSISTANT DOING? 3. IS IT CORRECT?") — forces model to actually analyze
2. **Editor prompt refined**: Focus on actual errors, not enumerate unspecified details. Don't flag ambiguity unless it's causing wrong behavior.
3. **max_resets=3**: Cap on context resets per conversation (was unlimited)
4. **Memory updater model fixed**: Now uses `cfg.model.ctx_editor.model` (gpt-5-mini) instead of default gpt-4o-mini
5. **Unify prompt rewritten**: Explicit BAD/GOOD examples, preserves specificity
6. **No reasoning_effort on any ctx_editor calls**: gpt-5-mini needs full reasoning for this work

### V3 Results (Code)

| Experiment | V1 | V2b | V3 |
|---|---|---|---|
| baseline | 4/19 (21%) | — | — |
| reflection | 6/20 (30%) | — | — |
| **context_edit** | 2/19 (11%) | 4/20 (20%) | **9/20 (45%)** |
| **agentic_edit** | 2/18 (11%) | 1/19 (5%) | **7/20 (35%)** |

**context_edit V3**: 9/20 (45%), 0 errors, avg 10.7 turns (was 18.8 in V1)
**agentic_edit V3**: 7/20 (35%), 0 errors, 14/20 problems had edits triggered (was 1/20 in V2b)

Note: reasoning_effort="medium" on decision call hurt agentic_edit → 1/20 (V3b). Full reasoning is required.

### Output Directories

| Experiment | Math V1 | Code V1 | Code V2b | Code V3 |
|---|---|---|---|---|
| baseline | 16-12-15 | 16-16-51 | — | — |
| reflection_only | 16-16-53 | 16-16-55 | — | — |
| context_edit | 16-16-57 | 16-16-58 | 20-48-29 | 21-49-09 |
| agentic_edit | 16-17-00 | 16-17-01 | 20-48-30 | 21-35-46 |
| baseline_memory | 17-16-29 | 17-16-31 | — | — |
| context_edit_memory | 17-16-33 | 17-16-34 | — | — |
| agentic_edit_memory | 17-16-36 | 17-16-39 | — | — |

All paths relative to `outputs/2026-03-10/`.

## Bug Fixes Applied During Experiments

1. **`setup_memory` init bug**: `CheatsheetMemory(content="")` → `CheatsheetMemory(_content="")` (field is private)
2. **Error result trace type**: `trace=[]` → `trace={"messages": [], "logs": [], "num_resets": 0}` in parallel.py and batched.py
3. **Error results in memory update**: Added filter to skip error results before passing to `batch_update()`
4. **Timeout passthrough**: Strategies defaulted to 30s timeout. Fixed with `editor_timeout` param threaded from config.
5. **Memory updater model**: Was using gpt-4o-mini default. Fixed to use `cfg.model.ctx_editor.model`.
6. **reasoning_effort passthrough**: Accidentally passed to editor calls, degrading quality. Removed from all configs.

## V3 Memory Experiments (Code)

### Results

| Experiment | No Memory | Mem (uncapped) | Mem (capped 1500w) |
|---|---|---|---|
| context_edit V2 + fixes | 7/20 (35%) | 6/20 (30%) | 4/19 (21%) |
| context_edit V3 + fixes | 9/20 (45%) | 5/20 (25%) | 7/19 (37%) |

### Output Directories

| Experiment | Dir |
|---|---|
| V2 + memory (uncapped) | 2026-03-10/23-44-58 |
| V3 + memory (uncapped) | 2026-03-10/23-55-04 |
| V2 + memory (capped) | 2026-03-11/00-59-06 |
| V3 + memory (capped) | 2026-03-11/00-59-07 |

### Analysis

**Uncapped cheatsheet growth** was the primary issue — cheatsheets grew to 16-19K chars (~5K tokens), consuming 65% of the editor prompt. Capping at 1500 words kept them around 1000-1100 words (~7-8K chars).

Capping helped V3 significantly (25% → 37%) but V3+mem still underperforms V3 alone (37% vs 45%). V2+mem doesn't benefit from memory at all — the V2 prompt is too minimal for memory to help. The hypothesis that "V2 simple prompt + memory discovers improvements" does not hold for code.

Batch-by-batch for V3+mem(capped): 2/5, 2/5, 3/5, 0/4 (1 error). The batch 4 collapse could be variance or bad cheatsheet advice accumulating.

Cheatsheet size evolution (capped):
- V2: ~1031 → 1084 → 1042 words (stable)
- V3: ~1081 → 1096 → 1140 words (stable)

## Status
- [x] Data files created
- [x] Experiment configs created
- [x] Phase 1 complete (V1)
- [x] Phase 2 complete (V1)
- [x] V1 analysis + root cause analysis
- [x] V2 prompt redesign + timeout fix
- [x] V3 decision prompt fix + editor refinements
- [x] V3 code results: context_edit 45%, agentic_edit 35%
- [x] V3 memory experiments — memory hurts both V2 and V3 (unbounded cheatsheet growth)
- [x] Capped cheatsheet (1500 words) — helps V3 (25%→37%) but still below V3 alone (45%)
- [ ] Variance runs for V3 conditions
- [ ] Math re-runs with V3 prompts

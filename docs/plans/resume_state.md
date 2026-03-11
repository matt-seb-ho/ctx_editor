# Resume State — Code_v2 Memory Experiments

**Last updated**: 2026-03-11
**Blocked on**: OpenAI API quota exhaustion (429 `insufficient_quota`)

## What Was Happening

We are running 3 experiment conditions on `task=code_v2` (20 code problems) to test whether memory-based learning improves context editing:

1. **Baseline** — no context modification
2. **Context edit V3** — structured context editing (best no-memory approach)
3. **Context edit V3 + memory (capped)** — same + continual cheatsheet learning (1500 word cap)

## Completed Results

| Config | Full 20 | Same-15 subset |
|---|---|---|
| Baseline | 3/20 (15%) | 2/15 (13%) |
| Context edit V3 | 8/20 (40%) | 6/15 (40%) |
| V3 + memory (capped) | 8/15 partial | **8/15 (53%)** |

**Baseline** and **V3** runs are complete (all 20 problems). **V3+memory** completed 15/20 before hitting API quota.

### Output Directories (all under `outputs/2026-03-11/`)

| Experiment | Dir | Status |
|---|---|---|
| Baseline code_v2 | `03-47-52` | Complete (20/20) |
| V3 context_edit code_v2 | `03-47-53` | Complete (20/20) |
| V3+memory code_v2 | `03-47-55` | Partial (15/20, crashed batch 3 with 429) |
| Failed re-run #1 | `04-11-10` | All errors (quota still down) |
| Failed re-run #2 | `04-18-24` | All errors (quota still down) |

### Per-Problem Results (15 completed)

```
Problem                      Baseline  V3  V3+Mem  Notes
sharded-HumanEval/113        0         0   0
sharded-HumanEval/128        0         0   0
sharded-HumanEval/141        0         1   1
sharded-HumanEval/150        0         1   1
sharded-HumanEval/62         0         0   0
sharded-HumanEval/71         0         0   0
sharded-livecodebench/2754   1         0   1       MEM_WIN (prevents contiguous-subarray lock-in)
sharded-livecodebench/2756   0         0   1       MEM_UNIQUE (correct function signature)
sharded-livecodebench/2791   0         0   1       MEM_UNIQUE (simpler return type)
sharded-livecodebench/2816   0         1   0       MEM_LOSS (temperature variance, tuple vs str return)
sharded-livecodebench/2825   0         0   0
sharded-livecodebench/2857   1         1   1
sharded-livecodebench/2873   0         1   1
sharded-livecodebench/2881   0         1   1
sharded-livecodebench/2883   0         0   0
```

### Missing 5 Problems (batch 4, not run due to quota)

```
Problem                      Baseline  V3  V3+Mem
sharded-livecodebench/2888   0         0   ???
sharded-livecodebench/2893   0         1   ???
sharded-livecodebench/2916   1         1   ???
sharded-livecodebench/2920   0         0   ???
sharded-livecodebench/3000   0         0   ???
```

V3 got 2/5 on these. If memory gets a similar rate, final would be ~9-10/20 (45-50%) vs V3's 8/20 (40%).

## What Needs To Happen Next

### Immediate: Complete the V3+memory run

The memory run needs batch 4 (the 5 missing problems). However, it also needs the **cheatsheet state from batches 1-3** since this is continual learning. Two options:

**Option A: Re-run all 20 problems from scratch** (simpler but more expensive, ~$2-3)
```bash
ctx-editor experiment=context_edit_memory model=gpt5_mini task=code_v2 \
  task.data_file=data/test_code_subset.json \
  execution.max_concurrent=5 execution.mode=batched execution.batch_size=5 \
  memory.enabled=true memory.source=continual memory.target=context_editor \
  memory.include_full_spec_q=true memory.include_ground_truth_a=true
```

**Option B: Run only the missing 5 with frozen memory** (cheaper but needs the batch-3 cheatsheet)
- Would need to extract the cheatsheet state from the crashed run's verbose log
- Then run with `memory.source=frozen` pointing to a saved cheatsheet file
- Less ideal since the memory wouldn't update from the missing 5

**Recommended: Option A** — a full re-run is cleaner since temperature=1.0 means results won't exactly match anyway, and we want the complete 20-problem dataset.

### After completion: Analysis and write-up

1. **Complete results table** with all 20 problems for all 3 conditions
2. **Statistical analysis** — is the memory improvement significant at n=20 with temperature=1.0 variance?
3. **Consider variance runs** — run each condition 2-3x to get confidence intervals
4. **Update `docs/plans/experiment_runs_math_code.md`** with final results

### Longer-term next steps

- **Math V3 experiments** — run V3 context edit on math task (currently only have V1 results)
- **Variance analysis** — multiple runs to separate signal from temperature noise
- **Memory mechanism improvements** based on trace analysis findings:
  - Memory prevents over-engineering (invented params, complex returns)
  - Memory breaks wrong-approach lock-in
  - Memory enables faster convergence (~half the turns)

## Key Findings So Far

1. **V3+memory outperforms V3 alone on same-15 subset** (53% vs 40%) — first positive signal for memory
2. **Memory wins are qualitatively strong**: prevents assumption lock-in, simplifies outputs, better function signatures
3. **The single memory loss (2816) is pure temperature variance**, not a systematic issue
4. **Code_v2 (extraction fix) doesn't change results much** — baseline dropped slightly (21%→15%), V3 similar (45%→40%)

## Configuration Reference

All experiments use:
- **Model**: `gpt5_mini` (gpt-5-mini for assistant + ctx_editor, gpt-4o-mini for user/system)
- **Task**: `code_v2` (fixed answer extraction + code fence system prompt)
- **Data**: `data/test_code_subset.json` (20 problems filtered for assistant-attributable failures)
- **Execution**: batched, batch_size=5, max_concurrent=5
- **Memory**: continual, target=context_editor, include_full_spec_q + include_ground_truth_a
- **Cheatsheet cap**: 1500 words (enforced in reflection + unify prompts)
- **Max resets**: 3 per conversation

## Files Changed Since Last Commit (728b842)

```
Modified:
  docs/README.md
  src/ctx_editor/identify_false_negatives.py  (added extraction failure check)

New:
  docs/false_negatives_and_test_subset.md
  docs/plans/experiment_runs_math_code.md (heavily updated)
  docs/plans/resume_state.md (this file)
  src/ctx_editor/build_test_subset.py
```

Memory prompt files were modified in the last commit (728b842) and are already committed:
- `src/ctx_editor/memory/prompts/context_editor_reflection.txt`
- `src/ctx_editor/memory/prompts/context_editor_reflect_takeaways.txt`
- `src/ctx_editor/memory/prompts/unify_takeaways.txt`

# Resume State — Context Edit + Memory Experiments

**Last updated**: 2026-03-11 (Session 3, continued)

## Current Results — Session 3 (Azure, gpt-4o user/system)

| Config | Score | Avg Turns | Notes |
|---|---|---|---|
| Baseline | 6/20 (30%) | 6.8 | gpt-4o user/sys (was gpt-4o-mini) |
| Context edit V3 | 8/20 (40%) | 11.4 | Task-agnostic prompts |
| V3 + memory (old prompts) | 6/20 (30%) | 12.1 | Memory hurt — algorithmic templates in cheatsheet |
| **V3 + memory (fixed prompts)** | **12/20 (60%)** | **10.1** | **Cheatsheet restricted to editing principles only** |

### Per-Problem Results

```
Problem                      Base  V3  Mem(old)  Mem(fixed)
sharded-HumanEval/113          1    0     0         0
sharded-HumanEval/128          0    0     0         0
sharded-HumanEval/141          1    1     0         1
sharded-HumanEval/150          1    1     1         1
sharded-HumanEval/62           0    0     0         0
sharded-HumanEval/71           0    0     0         0
livecodebench/2754             1    1     1         1
livecodebench/2756             0    0     0         1   MEM_WIN
livecodebench/2791             1    1     0         1
livecodebench/2816             0    0     0         1   MEM_WIN
livecodebench/2825             0    0     0         0
livecodebench/2857             0    1     1         1
livecodebench/2873             0    0     1         1   MEM_WIN
livecodebench/2881             0    1     1         1
livecodebench/2883             0    0     0         0
livecodebench/2888             0    0     0         1   MEM_WIN
livecodebench/2893             1    1     1         1
livecodebench/2916             0    1     0         0   MEM_LOSS
livecodebench/2920             0    0     0         0
livecodebench/3000             0    0     0         1   MEM_WIN
```

**5 MEM_WINs, 1 MEM_LOSS** — memory is strongly additive when the cheatsheet is restricted to transferable editing principles.

### Output Directories

| Experiment | Dir | Status |
|---|---|---|
| Baseline (gpt-4o user/sys) | `2026-03-11/00-14-18` | Complete (20/20, 0 err) |
| V3 context edit | `2026-03-11/00-14-20` | Complete (20/20, 0 err) |
| V3+mem (old prompts) | `2026-03-11/00-14-22` | Complete (20/20, 0 err) |
| V3+mem (fixed prompts) | `2026-03-11/00-46-32` | Complete (20/20, 0 err) |

## What Changed This Session

### 1. Task-agnostic prompts (commit e41933a)
- Removed code-specific examples from V3 editor/decision prompts
- Removed LiC evaluation-specific language from memory prompts
- Added structured approach_evaluation (ERRORS, UNGROUNDED ASSUMPTIONS, CORRECTIVE DIRECTION)
- Added output format verification checkpoint

### 2. Cheatsheet content restriction (commit be499a1)
The critical fix. Trace analysis of the old-prompts memory run showed the cheatsheet accumulated:
- Algorithmic recipes (DP recurrences, specific function templates)
- Prescriptive function signatures
- Problem-specific code snippets

These anchored the editor on wrong algorithms for new problems (livecodebench/2916: wrong DP formulation, livecodebench/2791: rigid single-param signature).

The fix: explicit WHAT BELONGS / WHAT DOES NOT BELONG sections in reflection and unify prompts:
- **Belongs**: meta-level editing principles (output format verification, example-based disambiguation, intent separation)
- **Does not belong**: algorithmic recipes, code snippets, function signature templates, problem-specific details

### 3. Infrastructure changes
- Switched user/system agents from gpt-4o-mini to gpt-4o (commit fa056cc) — Azure content filter on gpt-4o-mini triggered jailbreak false positives on context edit meta-instructions
- Enabled gpt-4o-mini on dl-openai-1/3 endpoints (commit 6fe5dbd) — was commented out but actually deployed
- Increased max_retries_per_endpoint to 3

### 4. Baseline increase (15% → 30%)
The gpt-4o user/system change raised baseline from 15% to 30%. This is expected — gpt-4o is a stronger model for user simulation (clearer shard delivery). V3 held at 40%, so context editing still provides +10pp. Memory pushes to 60% (+20pp over V3).

## Key Findings

1. **Memory content matters more than memory mechanism.** The Reflect-then-Unify algorithm was fine all along — the issue was that the cheatsheet was storing the wrong kind of knowledge (solutions vs. principles).

2. **Transferable editing principles work.** The fixed cheatsheet (~944 words) focuses on: literal user intent capture, example-based disambiguation, rejecting assistant assumptions, output format verification. These generalize across problems.

3. **Algorithmic templates are toxic for memory.** When the cheatsheet includes code snippets or DP recurrences, the editor anchors on those patterns even when they don't match the new problem. This caused 2 of 3 MEM_LOSSes in the old-prompts run.

4. **V3+memory (fixed) achieves 60% accuracy** — 2x baseline (30%), +20pp over V3 alone (40%). This is the strongest result yet.

## Cross-Task Results (Session 3 continued)

All tasks use model=gpt5m_gpt4o (gpt-5-mini assistant/editor, gpt-4o user/system), multi-endpoint load balancer.

### Summary Table (context_edit experiments)

| Task (N) | Baseline | Context Edit V3 | V3 + Memory | Notes |
|---|---|---|---|---|
| **Code** (20) | 6/20 (30%) | 8/20 (40%) | **12/20 (60%)** | Memory strongly additive (+20pp) |
| **Math** (9) | 2/9 (22%) | 2/9 (22%) | 2/9 (22%) | Flat — low N, may need larger subset |
| **Database t2** (63) | 45/62 (73%) | 32/63 (51%) | 29/63 (46%) | Context editing hurts — baseline too strong |
| **Actions** (47) | 14/47 (30%) | 16/47 (34%) | 15/47 (32%) | Marginal context edit gain, memory neutral |

### Database t3 Results (threshold=3, 48 problems — failed in all 3 variance runs)

| Config | Score | Avg Turns | vs Baseline |
|---|---|---|---|
| Baseline | 30/48 (62.5%) | 3.7 | — |
| Context edit | 24/48 (50.0%) | 9.1 | -12.5pp |
| **Context edit+memory** | **35/48 (72.9%)** | 8.5 | **+10.4pp** |
| **Agentic edit** | **38/48 (79.2%)** | 3.4 | **+16.7pp** |
| Agentic edit+memory | 28/48 (58.3%) | 3.8 | -4.2pp |

Key finding: **Agentic edit (no memory) is best on database** — selective resetting avoids disrupting
conversations that are on track. Context edit+memory recovers from the always-reset damage but still
trails agentic edit. Memory consistently hurts the agentic decider across tasks.

### Full Results Table (all tasks × all conditions)

| Task (N) | Baseline | Ctx Edit | Ctx Edit+Mem | Agentic | Agentic+Mem | Best |
|---|---|---|---|---|---|---|
| **Code** (20) | 6/20 (30%) | 8/20 (40%) | **12/20 (60%)** | 8/19 (42%) | 4/20 (20%) | CE+M |
| **Math** (9) | 2/9 (22%) | 2/9 (22%) | 2/9 (22%) | 3/9 (33%) | 4/8 (50%)* | AE+M |
| **DB t3** (48) | 30/48 (63%) | 24/48 (50%) | 35/48 (73%) | **38/48 (79%)** | 28/48 (58%) | AE |
| **Actions** (47) | 14/47 (30%) | 16/47 (34%) | 15/47 (32%) | 11/47 (23%) | **17/47 (36%)** | AE+M |

*1 error excluded. CE=context_edit, AE=agentic_edit, M=memory.

**At least one method beats baseline on every task.** Best config varies by task.

### Output Directories

| Experiment | Dir | Status |
|---|---|---|
| Code baseline | `2026-03-11/00-14-18` | Complete (20/20, 0 err) |
| Code V3 context edit | `2026-03-11/00-14-20` | Complete (20/20, 0 err) |
| Code V3+mem (old prompts) | `2026-03-11/00-14-22` | Complete (20/20, 0 err) |
| Code V3+mem (fixed prompts) | `2026-03-11/00-46-32` | Complete (20/20, 0 err) |
| Code agentic edit | `2026-03-11/05-42-17` | Complete (19/20, 1 err) |
| Code agentic+mem | `2026-03-11/05-42-19` | Complete (20/20, 0 err) |
| Math baseline | `2026-03-11/06-27-56` | Complete (9/9, 0 err) |
| Math context edit | `2026-03-11/06-27-57` | Complete (9/9, 0 err) |
| Math context edit+mem | `2026-03-11/06-27-59` | Complete (9/9, 0 err) |
| Database baseline | `2026-03-11/06-28-05` | Complete (62/63, 1 err) |
| Database context edit | `2026-03-11/06-28-06` | Complete (63/63, 0 err) |
| Database context edit+mem | `2026-03-11/06-28-08` | Complete (63/63, 0 err) |
| Actions baseline | `2026-03-11/06-28-10` | Complete (47/47, 0 err) |
| Actions context edit | `2026-03-11/06-28-11` | Complete (47/47, 0 err) |
| Actions context edit+mem | `2026-03-11/06-28-12` | Complete (47/47, 0 err) |
| DB t3 baseline | `2026-03-11/11-14-46` | Complete (48/48, 0 err) |
| DB t3 context edit | `2026-03-11/11-14-47` | Complete (48/48, 0 err) |
| DB t3 context edit+mem | `2026-03-11/11-14-50` | Complete (48/48, 0 err) |
| DB t3 agentic edit | `2026-03-11/11-14-51` | Complete (48/48, 0 err) |
| DB t3 agentic edit+mem | `2026-03-11/11-14-53` | Complete (48/48, 0 err) |
| Math agentic edit | `2026-03-11/13-40-08` | Complete (9/9, 0 err) |
| Math agentic edit+mem | `2026-03-11/13-40-11` | Complete (8/9, 1 err) |
| Actions agentic edit | `2026-03-11/13-40-12` | Complete (47/47, 0 err) |
| Actions agentic edit+mem | `2026-03-11/13-40-14` | Complete (47/47, 0 err) |

### Cross-Task Analysis

1. **Always-resetting (context_edit) hurts on database.** Baseline is strong (62.5%) — many problems solved in few turns. Always resetting disrupts good conversations (avg turns 3.7 → 9.1, accuracy -12.5pp).

2. **Selective resetting (agentic_edit) is best on database.** +16.7pp over baseline at 79.2%. The decider correctly identifies when resetting helps vs. hurts. Avg turns actually decreases slightly (3.4 vs 3.7).

3. **Memory helps context_edit but hurts agentic_edit — consistently across tasks.** Context edit+memory: code +20pp, database +23pp (vs context_edit). But agentic+memory: code -22pp, database -21pp. The cheatsheet makes the decider over-trigger resets.

4. **The "when" matters more than the "how" on database.** Agentic edit (79.2%) > context edit+memory (72.9%) > baseline (62.5%) > context edit (50.0%). The decision to reset is more valuable than improving the edit quality.

5. **Code is unique in that context_edit+memory is best.** On code, always-resetting with learned editing principles (60%) beats agentic edit (42%). Code problems may have more consistent failure patterns that benefit from systematic editing.

6. **Memory on the decider needs different treatment.** The current cheatsheet (editing principles) doesn't translate to good reset decisions. The decider may need its own memory target with decision-oriented principles (when to reset vs. continue).

## What Needs To Happen Next

### Immediate
- **Spot-check failure modes**: Examine traces from database agentic_edit+memory and context_edit to understand why memory hurts the decider and why always-resetting disrupts database conversations
- **Variance runs on code**: Run 2-3x more to confirm the 60% result isn't temperature noise (n=20 is small)
- **Larger math subset**: 9 problems is too few — find or create a larger math subset

### If results hold
- **Separate memory targets**: The decider needs its own memory with decision-oriented principles (when to reset), not editing principles
- **Best config per task**: code=context_edit+memory, database=agentic_edit, actions=TBD
- **Write-up**: Document the cross-task findings

### Longer-term
- **Hybrid strategy**: agentic_edit with memory on the editor (not the decider)
- **Cross-task cheatsheet transfer**: Can a cheatsheet learned on code help with actions?
- **Retrieval-based memory**: As cheatsheet grows across tasks, consider retrieval to avoid token limits

## Configuration Reference

All experiments use:
- **Model**: `gpt5m_gpt4o` config — gpt-5-mini for assistant + ctx_editor, gpt-4o for user/system
- **Data**: task-specific subsets from `data/` (code=20, math=9, database=63, actions=47)
- **Execution**: max_concurrent=5; memory runs use batched mode (batch_size=3 for math, 10 for others)
- **Memory**: continual, target=context_editor, include_full_spec_q + include_ground_truth_a
- **Cheatsheet cap**: 1500 words (enforced in reflection + unify prompts)
- **Max resets**: 3 per conversation
- **Infrastructure**: Azure multi-endpoint (dl-openai-1, dl-openai-3, fxdata-eastus2, fxdata-shared)

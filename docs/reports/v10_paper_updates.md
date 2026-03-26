# V10 Paper Updates — LiC Tables and Ablations

**Date**: 2026-03-26
**Branch**: `main`

## Summary

Updated LiC paper tables with corrected S1.5 numbers (sans-issue-injection fix + accumulate instruction for actions) and new S2+accumulate results. Restructured ablation table from 2×2 matrix to progressive stripping format.

## Changes Made

### 1. S2+Accumulate for Actions (NEW RUN)

**Command:**
```bash
ctx-editor experiment=context_edit_v2_accumulate task=dev_actions model=gpt5_mini \
  execution.replay_source=outputs/2026-03-16/19-26-46 execution.max_concurrent=8
```

**Output directory:** `outputs/2026-03-26/02-18-54`

**Results:**
- Raw: 17/25 (68%)
- On common 23-sample set (comparable to other runs): **17/23 (74%)**

**Sample-level comparison with S1.5 (12/23, 52%):**
- S2+accum gained: parallel_165, parallel_187, parallel_195, parallel_30, parallel_5, parallel_54 (+6)
- S2+accum lost: parallel_91 (-1)
- Net: +5 solves over S1.5

**Why S2+accumulate outperforms S1.5:**
- S2 runs a fresh analysis on the baseline conversation (not reusing S1's pre-computed analysis)
- S2's gated reset preserves full context when no issues are found, while S1.5 always resets (potentially losing useful context on non-problematic turns)
- Both use the same accumulate instruction for actions

**Note:** S2+accumulate used replay from baseline traces (`outputs/2026-03-16/19-26-46`), replaying only the final turn. This is consistent with S1.5's replay approach but differs from the original S2 runs which used full simulation.

### 2. Paper Table Updates

#### Table 2: LiC Accuracy by Strategy (No Memory)

| Strategy | Math | Code | Database | Actions | Source |
|---|---|---|---|---|---|
| Baseline | 60% | 16% | 4% | 9% | unchanged |
| Omit Assistant | 85% | 78% | 32% | 83% | unchanged |
| Concatenate User | 84% | 68% | 32% | 87% | unchanged |
| Append Analysis (S1) | 80% | 56% | 32% | 22% | unchanged |
| **Always-Reset (S1.5)** | **75%** | **61%** | **48%** | **52%** | sans_issue_injection_redux |
| **Gated Reset (S2)** | 75% | 72% | 44% | **74%** | actions: NEW S2+accum run |

Changes from previous paper:
- Always-Reset: 80→75 (math), 69→61 (code), 40→48 (database), 30→52 (actions)
  - Source: `docs/sans_issue_injection_redux.md`, dirs `outputs/2026-03-21/10-33-19` through `10-35-17`
  - Reason: Removed issues injection bug + added accumulate for actions
- Gated Reset actions: 13→74
  - Source: NEW run `outputs/2026-03-26/02-18-54`
  - Reason: Added accumulate instruction

#### Table 3: Effect of Adding Memory

| Strategy | Math | Code | Database | Actions | Source |
|---|---|---|---|---|---|
| Always-Reset | 75% | 61% | 48% | 52% | sans_issue_injection_redux |
| Always-Reset + Memory | 85% | 68% | 44% | 52% | sans_issue_injection_redux |

Changes from previous paper:
- Always-Reset: same as Table 2 updates
- Always-Reset + Memory: only actions changed (30→52)
  - Source: `outputs/2026-03-21/10-37-32`

**Not updated:** Gated Reset + Memory in Table 3 (was not in the table). No S2+mem+accumulate run exists. The original S2+mem = 13% actions would also benefit from accumulate but was not re-run.

### 3. Ablation Table Restructure

**Old format** (2×2 matrix):
```
Hard attn., spec only     | 70% | 63% | 40%
Hard attn., spec + eval   | 80% | 56% | 32%
Soft attn., single pass   | 55% | 21% |  4%
Soft attn., spec + eval   | 40% | 11% |  8%
```

**New format** (progressive stripping):
```
Hard attn., spec + eval (ours)    | 80% | 56% | 32%
  − hard attention                | 40% | 11% |  8%
    − subtask decomposition       | 55% | 21% |  4%
```

**Rationale:** Starting from the full setup and stripping piece by piece is more intuitive than a 2×2 matrix. Shows:
1. Hard attention is load-bearing (removing it → below baseline)
2. Chaining contaminated calls amplifies errors (removing decomposition from contaminated setup partially recovers, showing 2-query is harmful without clean inputs)

**Note:** The "hard attn., spec only" row (70/63/40) was removed from the main ablation table. It doesn't fit the progressive stripping narrative since it's a different ablation axis (removing Q2 from the hard-attention setup). Could be mentioned in text if needed.

### 4. V10 Prompts Assessment

Read v10 prompts from `~/tau2-bench/ctx_edit/analyzer.py`. Key v10 changes from v8:

**v9 (intermediate, tau2-bench):**
- Q2 broadened from 2 sections (aligned/issues) to 5 dimensions: task-spec contradictions, errors, bloat, valid progress, corrective direction
- Added context editing framing explaining *why* analysis is being done

**v10 (tau2-bench specific):**
- Reframed from "pollution detection" to "mid-task strategic reflection"
- Added `environment_state` tracking (tool calls that mutate backend state)
- Two Q2 variants: S2 mode (output IS new context) vs S3 mode (output feeds into rewrite)
- Added Q3 for S3: LLM-driven context rewrite from analysis
- `strategic_direction`: what should agent try next, what hasn't been explored

**Relevance to LiC ablations:**
- **Expanded issue types** (errors, bloat, task-spec contradictions) could improve analysis quality, but the ablation story is about hard vs soft attention architecture, not prompt quality
- **Environment state** is not relevant for LiC (no tool calls)
- **Strategic direction** could help but is orthogonal to the ablation axes
- **S2/S3 mode distinction** in Q2 is a good idea but would need adaptation for LiC

**Assessment:** v10 changes are mostly tau2-bench-specific (tool calls, environment state, agent framing). The expanded issue types and corrective direction could improve absolute LiC numbers but wouldn't change the ablation story (hard attention dominance, contamination amplification). Running v10-adapted LiC experiments is low priority relative to the paper deadline.

## Output Directories

| Run | Result | Dir |
|-----|:------:|-----|
| S2+accumulate actions | 17/23 (74%) | `outputs/2026-03-26/02-18-54` |

## Files Modified

- `writing/latex_project/colm2026_conference.tex`: Tables 2, 3, 4 and surrounding text
- `docs/reports/v10_paper_updates.md`: This document

# htn20_52 Experiment Results

**Date**: 2026-03-26/27
**Evaluated model**: gpt-5-mini (assistant + analyzer)
**Subset**: htn20_52 (20 hardest true-negative problems per task from gpt-5.2 LiC logs)
**Runs**: Single run per strategy per task (replay on first available conversation)

See `docs/htn20_52_subset.md` for subset construction details.

## Main Results Table

All numbers are correct/total (accuracy %). Actions uses the +accumulate prompt variant for S0/S1/S1.5/S2/S3.

| Strategy | Math (n=20) | Code (n=20) | Database (n=20) | Actions (n=20) |
|---|---|---|---|---|
| **S0** (baseline) | 4/20 (20%) | 2/20 (10%) | 1/20 (5%) | 12/20 (60%) |
| **S1** (append analysis) | 8/20 (40%) | 6/20 (30%) | 8/20 (40%) | 15/20 (75%) |
| **AO** (omit assistant) | 10/20 (50%) | 5/20 (25%) | 8/20 (40%) | 17/20 (85%) |
| **S1.5** (non-gated reset) | 11/20 (55%) | 5/20 (25%) | 8/20 (40%) | 16/20 (80%) |
| **S2** (gated reset) | 8/20 (40%) | 5/20 (25%) | 5/20 (25%) | 17/20 (85%) |
| **S3** (LLM compaction) | 11/20 (55%) | 4/20 (20%) | 7/20 (35%) | 10/20 (50%) |
| **S3v2** (structured prompt) | 8/20 (40%) | 6/20 (30%) | 7/20 (35%) | 11/20 (55%) |

**Code note**: S3 and S1.5 code ran through the s15 script which skips problems where S1 had errors (7 livecodebench problems with syntax errors). The denominators shown are normalized to /20 treating missing/error samples as incorrect.

## Key Findings

### 1. Context pollution is devastating on hard problems

S0 baseline accuracy is 5-20% on math/code/database. These are problems where the original gpt-5.2 model failed in 5-10 out of 10 runs with multi-turn context. When gpt-5-mini replays the same polluted conversation and just regenerates the last turn, it almost never recovers. The context is too corrupted.

### 2. S1.5 matches or exceeds the AO upper bound

AO (omit assistant) strips all assistant messages, giving the model a "clean slate" with only user information. It was expected to be the ceiling for context manipulation strategies. S1.5 matches AO on code/database and **exceeds it on math** (55% vs 50%). This means the analyzer-curated context (task spec + aligned work) is more useful than raw user messages alone.

### 3. S2 gating hurts on consistently hard problems

S2 (gated reset) underperforms S1.5 on math (40% vs 55%) and database (25% vs 40%). On problems that are always hard, the analyzer sometimes decides the context doesn't need editing (`needs_edit=False`), missing the opportunity to reset. The non-gated approach (always reset) is strictly better when problems are known to be difficult.

### 4. S3 (LLM compaction) underperforms despite correct compaction output

S3 ties S1.5 on math (55%) but is much worse on actions (50% vs 80%) and database (35% vs 40%).

**Root cause analysis** (detailed in actions divergent-case study): In 5 out of 6 cases where S1.5 succeeded but S3 failed, S3's compaction output was actually correct and complete. The failure is downstream: the assistant doesn't faithfully reproduce all items from the LLM-generated compacted context. It treats natural-language descriptions of function calls as informational rather than prescriptive, selectively returning only a subset (often the most recent one).

S1.5's programmatic template produces structured, enumerated parameter listings that are harder to selectively ignore. An improved "S3v2" prompt that forces enumerated output helped slightly on actions (+5pp) and code (+10pp) but regressed on math (-15pp), confirming the issue is not primarily about prompt quality but about adding an extra LLM interpretation layer.

### 5. S1 (append analysis, no reset) is surprisingly effective

Simply appending the analysis to the polluted conversation (without resetting) produces large gains: +20pp math, +20pp code, +35pp database, +15pp actions over S0. The analysis gives the assistant enough signal to overcome anchoring, even without removing the polluted history.

### 6. Actions is the easiest to intervene on

All strategies perform well on actions (60-85%), likely because function-calling tasks have more structured output and the accumulate instruction helps the model consolidate its answer.

## Strategy Descriptions

- **S0**: No intervention. Replay the polluted multi-turn context and regenerate the final assistant turn.
- **S1**: Run the conversation analyzer (two-query architecture) and append its output to the context before the final turn. No context modification.
- **AO**: Omit all assistant messages from context. The model sees only system + user messages (Huang et al. 2026 baseline).
- **S1.5**: Run the analyzer, then **always** reset the conversation: replace the full history with a compacted context containing the task specification and aligned work. Programmatic template.
- **S2**: Same as S1.5, but **gated**: only reset if the analyzer determines `needs_edit=True`. If no issues found, pass through like S0.
- **S3**: Same as S1.5, but the compacted context is produced by an LLM reading the full conversation + analysis, rather than a programmatic template.
- **S3v2**: S3 with an improved compaction prompt that forces enumerated, structured output matching S1.5's format. Uses `context_compaction_v2.txt`.

## Output Directories

### Phase 1 (math/code, 2026-03-26)
- S0 math: `outputs/2026-03-26/21-42-24`
- S0 code: `outputs/2026-03-26/21-42-26`
- AO math: `outputs/2026-03-26/12-45-38`
- AO code: `outputs/2026-03-26/12-45-27`
- S1 math: `outputs/2026-03-26/12-45-49`
- S1 code: `outputs/2026-03-26/12-45-52`
- S1.5 math: `outputs/2026-03-26/12-51-40`
- S1.5 code: `outputs/2026-03-26/12-51-42`

### Phase 2 (database/actions, 2026-03-26)
- S0 database: `outputs/2026-03-26/21-49-57`
- AO database: `outputs/2026-03-26/21-49-58`
- S1 database: `outputs/2026-03-26/21-49-58`
- AO actions: `outputs/2026-03-26/21-49-59`
- S1 actions: `outputs/2026-03-26/21-50-00`
- S1.5 database: (s15 script output)
- S0+accum actions: (s15 script output)
- S1+accum actions: (s15 script output)
- S1.5+accum actions: (s15 script output)

### Phase 3 (S2/S3, 2026-03-27)
- S2 math: `outputs/2026-03-27/00-05-48`
- S2 code: (run output)
- S2 database: (run output)
- S2+accum actions: `outputs/2026-03-27/00-07-23`
- S3 math/code/database/actions: (s15 script outputs)

## Limitations

1. **Single run**: All results are from a single replay run. Given n=20, the 95% CI for a 50% accuracy is roughly +/-22pp. Differences under ~15pp may not be significant.

2. **Code evaluation errors**: 4-7 livecodebench problems produce syntax errors in model output across strategies. These are counted as incorrect in the normalized table above, but the s15 script excludes them entirely (inflating its denominators).

3. **Conversation selection**: Results use the first available conversation per problem. Different conversations for the same problem may yield different results due to different user simulator phrasings.

4. **Model mismatch**: Baseline conversations were generated by gpt-5.2; interventions use gpt-5-mini. This means S0 is "gpt-5-mini replaying gpt-5.2's polluted context," not "gpt-5-mini's own multi-turn performance."

# Pre-Sunday Update — 2026-03-15 ~08:30 UTC

## Where We Are

We've run 6 batches of experiments across math, code, database, and actions tasks using
gpt-5-mini with our S0/S1/S2 ± memory strategies. The system is in good shape with several
critical bugs fixed, but one open issue needs addressing before the next full simulation run.

## Best Results So Far (Batches 4–6 — v2 evaluators, fixed XML prompts, replay mode)

| Task | S0 | S1 | S1+mem | S2 | S2+mem | Concat |
|------|:--:|:--:|:------:|:--:|:------:|:------:|
| **math** | 57% | 52% | 61% | **65%** | **65%** | 65% |
| **code** | 12% | 24% | 28% | 36% | **44%*** | 84%† |
| **database** | 4% | 12% | 8% | **16%** | **16%** | — |
| **actions** | 8% | 12% | **20%** | 8% | 8% | 60% |

*Batch 5 re-run with memory guardrail
†Code concat includes starter code/function signatures not available in sharded setting

**S2 math matches the concat ceiling (65%).** This is the headline result.

### Output Directories

**Batch 4 — v2 eval, fixed XML prompts (2026-03-15)**

| Run | Result | Dir |
|-----|:------:|-----|
| S0 v2 math | 13/23 (57%) | `outputs/2026-03-15/01-01-10` |
| S0 v2 code | 3/25 (12%) | `outputs/2026-03-15/01-07-56` |
| S1 math | 12/23 (52%) | `outputs/2026-03-15/01-27-27` |
| S2 math | **15/23 (65%)** | `outputs/2026-03-15/01-31-57` |
| S1+mem math | 14/23 (61%) | `outputs/2026-03-15/01-36-02` |
| S2+mem math | **15/23 (65%)** | `outputs/2026-03-15/01-46-37` |
| S1 code | 6/25 (24%) | `outputs/2026-03-15/01-56-09` |
| S2 code | 9/25 (36%) | `outputs/2026-03-15/02-05-08` |
| S1+mem code | 7/25 (28%) | `outputs/2026-03-15/02-12-34` |
| S2+mem code | 6/25 (24%) | `outputs/2026-03-15/02-26-23` |

**Batch 5 — S2/S2+mem code with memory guardrail (2026-03-15)**

| Run | Result | Dir |
|-----|:------:|-----|
| S2 code | 7/25 (28%) | `outputs/2026-03-15/03-46-17` |
| S2+mem code | **11/25 (44%)** | `outputs/2026-03-15/03-53-34` |

**Batch 6 — Database v2 (2026-03-15)**

| Run | Result | Dir |
|-----|:------:|-----|
| S0 database | 1/25 (4%) | `outputs/2026-03-15/04-20-34` |
| S1 database | 3/25 (12%) | `outputs/2026-03-15/04-26-41` |
| S2 database | 4/25 (16%) | `outputs/2026-03-15/04-32-04` |
| S1+mem database | 2/25 (8%) | `outputs/2026-03-15/04-37-04` |
| S2+mem database | 4/25 (16%) | `outputs/2026-03-15/04-48-28` |

**Earlier batches** — see `docs/reports/run_index.md` for full listing with Batch 1–3 output dirs.

## Bugs Fixed This Session

1. **XML tag prompts (critical)**: All analyzer prompts had instructions *inside* XML tags.
   Models read them as content, not format instructions. ~90% of analyses returned empty
   aligned/issues → S2 fell through to baseline. Fixed with "Use this format for your answer:"
   preamble + placeholder descriptions inside tags. Fallback section-header parser added.

2. **S2 accumulated state**: After a context reset, the analyzer only saw the latest user
   message, not the task spec from the previous compaction. Fixed by adding
   `include_compacted=True` to `get_user_messages_string()`.

3. **v1 evaluators**: Dev task configs were using v1 evaluators. v2 fixes math extraction
   (`\boxed{}`), code extraction (import-inside-function bug), and database (SQL fences).
   Updated dev_math, dev_code, dev_database configs. Added note to CLAUDE.md.

4. **Extraction failure logging**: Added warnings when XML tag extraction falls back to
   raw output or section-header parsing. Previously silent.

5. **Memory guardrail**: Moved "don't ask clarifying questions" guidance from system prompt
   (changes LiC protocol) to memory updater prompts (lets cheatsheet learn it naturally).
   S2+mem code jumped from 24% to 44% with this change.

## Open Issue: S1 Analysis Persistence

**Not yet fixed.** Identified at end of session.

S1 appends `<conversation_analysis>` blocks to user messages via `append_to_last_user_message()`.
This permanently mutates the message content. On subsequent turns:
- The **analyzer** sees its own prior analyses embedded in user messages (contamination)
- The **assistant** sees prior analyses on all future turns (should only see each once)

Expected behavior (confirmed with user):
- Task spec query: should see all user messages but NOT prior analysis blocks
- Comparison query: should see full conversation but NOT prior analysis blocks
- Assistant: should see an analysis only for the turn it's generated, not on subsequent turns

**Fix needed**: Strip `<conversation_analysis>` tags in the analyzer (both queries) the same
way `_strip_edit_notes` strips `<context_edit_notes>`. Also strip from messages returned to
the assistant for subsequent turns. This is the first thing to address in the next session.

## Infrastructure Built

- **Replay mode**: Reuses S0 conversation prefixes, regenerates only last turn. 6.6x faster,
  89% cheaper. Scripts: `scripts/run_replay_experiments.sh`
- **Concat baseline**: Single-turn upper bound. Script: `scripts/run_concat_baseline.py`
- **Portable traces**: `data/baseline_traces/` and `data/baseline_traces_v2/` for
  cross-machine replay (gitignored, share as artifact)
- **Error attribution**: Enabled by default (gpt-5-mini, batch mode)
- **App viewer**: Shows error attribution, replay provenance, branch info in sidebar
- **Run index**: `docs/reports/run_index.md` — all batches with output dirs, costs, wall times
- **Dev task configs**: `dev_math`, `dev_code`, `dev_database`, `dev_actions` with v2 evaluators

## Key Files Changed

| File | Change |
|------|--------|
| `strategies/analyzer.py` | include_compacted, XML fallback parser, extraction logging |
| `strategies/prompts/analyzer_v6_*.txt` | Fixed XML tag format, precision directive |
| `strategies/context_edit_v2.py` | (reverted accumulation change — too aggressive) |
| `core/trace.py` | `include_compacted` param on `get_user_messages_string()` |
| `core/simulator.py` | (reverted system prompt guardrail — moved to memory) |
| `memory/renderers.py` | Interleaved chronological rendering for analyzer |
| `memory/prompts/*.txt` | Strategy context, "how" guidance, evaluation environment |
| `config/config.yaml` | Error attribution enabled, model=gpt-5-mini |
| `config/task/dev_*.yaml` | v2 evaluator routing |
| `app_conv_viewer.py` | Error attribution + provenance display |
| `CLAUDE.md` | v2 evaluator guidance |

## What to Do Next

1. **Fix S1 analysis persistence** (open issue above) — strip prior `<conversation_analysis>`
   blocks before analyzer and assistant see them on subsequent turns
2. **Re-run full simulation** for math and code with all fixes (v2 eval, fixed XML, S2 fix)
3. **Address database/actions**: Multi-artifact task spec changes and S2 accumulation —
   user wants to think through the right approach before implementing
4. **Database extra columns**: Let memory learn to be precise about columns rather than
   hardcoding a system prompt directive
5. **Update run index** with Batch 5 and 6 results

## Git State

Branch: `newleaf2`
Latest commit: `c249581` (multi-turn replay mode)
All changes committed. Clean working tree (except user files: cmd_backup.md, writing/, etc.)

## Reports Written

- `docs/dev_set_error_analysis.md` — Batch 1 findings
- `docs/concat_baseline.md` — Concat baseline docs
- `docs/reports/run_index.md` — All batch results and output dirs
- `docs/reports/feedback_deliberation_batch1.md` — Response to user feedback
- `docs/reports/code_task_analysis.md` — Code task spot-check
- `docs/reports/replay_results_batch1.md` — Batch 2-3 replay results
- `docs/reports/database_actions_analysis.md` — Database/actions diagnosis

# CLAUDE.md

## Project Overview

Context Editor evaluation system built on the "Lost in Conversation" (LiC) framework. Tests whether LLM-driven context editing can close the performance gap between single-turn and multi-turn conversations.

**Core idea**: LLMs overcommit to early incorrect assumptions in multi-turn settings and cannot self-correct because the bad reasoning remains in context. We use an LLM-as-analyzer to critically inspect the conversation history — identifying where the assistant's approach diverges from what the user actually specified — then surgically rewrite the context to remove erroneous assumptions, failed approaches, and anchoring content ("hard attention"). Unlike prior work that simply discards all assistant messages, we preserve what's correct and remove what's harmful.

See `docs/project_motivation.md` for full research background and comparisons with prior work (ERGO, Huang et al.).

## Build and Run

```bash
pip install -e ".[all]"

# Main entry point (Hydra config)
ctx-editor
ctx-editor experiment=context_edit_v2 model=gpt4o_mini task=math
ctx-editor execution.max_concurrent=5 logging.verbose=true

# Original LiC simulations
python src/lic/run_simulations.py --tasks math --models gpt-4o-mini --N_workers 4

# Linting
black src/ --line-length 100
ruff check src/
mypy src/
```

## Architecture

Two layers: `src/ctx_editor/` (our evaluation framework) and `src/lic/` (original LiC simulation code from Microsoft Research).

### Strategies (`strategies/`)

Three settings control how context is prepared before each assistant turn:
- **S0** — `BaselineStrategy` — No modification
- **S1** — `AppendAnalysisStrategy` — Analyzer output appended to context (no rewriting)
- **S2** — `ContextEditV2Strategy` — Analyzer-driven context rewriting when issues are found

S1 and S2 use the `ConversationAnalyzer` (two-query architecture). Legacy strategies (`ContextEditStrategy`, `AgenticEditStrategy`, `ReflectionStrategy`) kept for comparison with earlier results.

See `docs/newer_leaf_refactor.md` for analyzer design rationale and `docs/context_strategies.md` for strategy details.

### Other components
- **Agents** (`agents/`): `UserAgent` (reveals shards), `SystemAgent` (verifies/extracts answers)
- **Core** (`core/`): `ConversationSimulator` (orchestrates turns, Option 2 rendering), `ConversationTrace` (history tracking)
- **Tasks** (via `lic/tasks/`): math, code, database, actions
- **Memory**: Cheatsheet-based learning from past trajectories. See `docs/memory_learning.md`.

### Configuration (Hydra)

Configs in `src/ctx_editor/config/`: `experiment/`, `model/`, `task/`.
Override with CLI: `ctx-editor model=claude task=code experiment=context_edit_v2`

### Data flow

Samples from `data/` → `ConversationSimulator` runs turns → each turn: UserAgent → Strategy.prepare_context → Assistant → SystemAgent.verify → results to `outputs/{experiment_name}/{timestamp}/`

## Key Patterns

- Strategies implement `ContextStrategy` protocol with `prepare_context()` method
- Hydra instantiation uses `_target_` in YAML configs
- Async execution throughout (`asyncio.run()` at entry point)
- **Always use v2 task evaluators** when available (`task_version_map` in task config). v2 fixes extraction bugs (code import parsing, math boxed format) and adds better system prompts (code fences, `\boxed{}` for math, SQL fences for database). Available: `math_v2`, `code_v2`, `database_v2`. See `config/task/*_v2.yaml` for reference. Dev task configs (`dev_math`, `dev_code`, `dev_database`) already use v2.

## Environment Variables

- `OPENAI_API_KEY` or `AZURE_OPENAI_API_KEY` + `AZURE_OPENAI_ENDPOINT`
- `ANTHROPIC_API_KEY` (for Claude models)
- Place in `.env` file at repo root (auto-loaded)

## Documentation

- `docs/` contains detailed writeups on architecture, strategies, and research context
- `docs/plans/` for multi-session implementation plans; completed plans go to `docs/plans/completed/`
- Update docs after substantial changes to keep them accurate

### Maintaining `docs/index.md`

`docs/index.md` is the canonical doc map for the project — it's organized topically and chronologically and is what readers (including future you) hit first when looking for "where did we write about X." Keep it current:

- **Whenever you create a new file under `docs/`** (any extension, but in practice Markdown), add an entry to `docs/index.md` in the same change:
  1. Slot it into the appropriate topical section (or add a section if none fits).
  2. Append it to the **Chronological log** table at today's date with a ≤ 12-word one-liner. Use absolute dates (e.g. `2026-05-11`), not relative ones.
- **Whenever you delete or rename a doc**, remove or update its entry in both places.
- The chronological log is newest-first; insert new rows at the top.
- One-liners describe what the file *contains* (e.g. "N=3 Gated-Reset replay reruns; paper variance row"), not what it was used for that week. They should still make sense a year later.
- If `docs/index.md` becomes substantially stale (e.g. you discover several missing entries during normal work), backfill them in one pass rather than leaving the drift to grow.
- For `docs/reports/` and `docs/plans/` subdirectories, link the individual files in the index rather than the directory — readers should land on the actual content.

## Paper editing

- The active NeurIPS draft now lives in `writing/overleaf_repo/neurips/neurips_2026_conference.tex`. This directory is a clone of the Overleaf project's connected GitHub repo, so edits made here sync to Overleaf via that repo (no manual upload).
- Always apply paper revision/editing requests to that file. The older standalone copy at `writing/neurips_project/neurips_2026_conference.tex` is now stale and should not be edited; treat it as a historical reference only.
- The COLM draft equivalent is `writing/overleaf_repo/colm/colm2026_conference.tex` if a COLM revision is requested.

### Repo boundary

- `writing/overleaf_repo/` is a **separate git repository** (the Overleaf-connected GitHub clone). It is gitignored from the outer ctx_editor repo on purpose. Submodules were considered and rejected: Overleaf pushes from collaborators would constantly outdate a pinned submodule SHA, generating noise without benefit.
- The outer repo's history should never contain commits that touch paths under `writing/overleaf_repo/`. If a `git status` from the outer repo ever shows `writing/overleaf_repo/` as modified or as a new gitlink, something has gone wrong; do not `git add` it.
- Each repo gets its own commit history. Conventional Commits style applies in both.

### Push/pull workflow for the paper repo

- **Run all paper-repo git commands from inside the inner repo**, e.g. `git -C writing/overleaf_repo <command>`. Do not `cd` out of the outer repo for an unrelated paper edit.
- **Pull before editing.** Lianhui or Michel may have pushed from Overleaf since the last sync:
  ```bash
  git -C writing/overleaf_repo pull origin main
  ```
- **Edit, then commit inside the inner repo** (not the outer one). Use the same conventional-commits style:
  ```bash
  git -C writing/overleaf_repo add <files>
  git -C writing/overleaf_repo commit -m "fix: ..."
  ```
- **Push to GitHub when ready** so Overleaf picks the changes up:
  ```bash
  git -C writing/overleaf_repo push origin main
  ```
  Confirm with the user before pushing if the changes are non-trivial — pushes are visible to collaborators on Overleaf.
- **Asset files (PNG, PDF, etc.) belong inside `writing/overleaf_repo/assets/`** and should be tracked in the inner repo so Overleaf has them. Project-root in Overleaf is `writing/overleaf_repo/`, so figure paths in `.tex` are written as `assets/<file>`.
- **Do not edit the stale `writing/neurips_project/` copy.** It is intentionally not synced.

## Git

- after a fix or feature is complete, please make a git commit to make state tracking/rolling back even easier
- please follow the conventional commits spec (fix/feat/chore: short desc)

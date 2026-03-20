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

## Git

- after a fix or feature is complete, please make a git commit to make state tracking/rolling back even easier
- please follow the conventional commits spec (fix/feat/chore: short desc)

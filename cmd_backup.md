# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Context Editor evaluation system built on top of the "Lost in Conversation" (LiC) research framework. It evaluates LLM performance in multi-turn conversations and tests various context management strategies to mitigate context degradation.

**Research question**: Can LLM-driven context editing reduce the gap between single-turn and multi-turn settings?

### The Problem

Laban et al. (2025) showed that LLMs suffer a 39% average performance degradation when task instructions are revealed incrementally across turns (mimicking natural user behavior) versus receiving the full instruction at once. This is primarily a **reliability** problem: aptitude (best-case) drops only ~16%, but unreliability (variance between best/worst runs) more than doubles (+112%). All models tested — from 8B to frontier — exhibit similarly catastrophic unreliability in multi-turn settings.

The core failure: **LLMs overcommit to an initial answer attempt and cannot recover from early mistakes.** This manifests as a cascade of four compounding failure modes:
1. **Premature answer attempts with incorrect assumptions** — models jump to full solutions before having enough information, filling gaps with assumptions that become anchored even when contradicted by later user messages
2. **Answer bloat** — rather than starting fresh, models patch/extend previous wrong attempts, producing solutions 20–300% longer than single-turn equivalents
3. **Loss-in-middle-turns** — models disproportionately attend to first and last turns, neglecting middle-turn information (the "lost in the middle" effect applied across turns)
4. **Over-verbosity** — longer responses contain more speculative content that the model treats as established facts in later turns

The gradual sharding experiment shows this is a threshold effect: even 2-turn conversations trigger the full reliability collapse. Known mitigations (reasoning models, lower temperature, agent-like recapitulation within the same conversation) are largely ineffective because the model still anchors on its prior incorrect attempts.

The only effective band-aid is the user manually consolidating conversation state and starting a **new** conversation — effectively converting multi-turn back to single-turn.

### Our Approach: Context Editing

We propose automatic context editing as a "hard attention" mechanism: surgically rewriting the conversation history to remove incorrect assumptions and failed attempts so future generation literally cannot attend to previous bad content.

**Key differentiators from prior work (ERGO, Huang et al.):**
1. **LLM-driven decision making** — ERGO uses an entropy threshold, Huang uses a logistic regression classifier. We use the LLM itself to reason about whether it's lost and what to discard. This is more general (works with any black-box API), provides richer signal (understands *why* there's confusion), and enables finer-grained editing decisions. It's also "bitter-lesson-pilled": if the model can recognize confusion via prompting, this is a natural training target.
2. **Preserving (edited) assistant messages** — Both ERGO and Huang discard all assistant messages, which trivially recovers the single-turn Concat baseline on LiC (an exploit, not a real solution). We surgically edit to remove harmful content while keeping useful partial work. This matters because (a) the assistant may have done correct partial work worth preserving, (b) user messages often reference assistant messages and become meaningless without them, and (c) it avoids the LiC exploit.
3. **Memory-based learning** — All prior approaches use static intervention logic. We incorporate persistent memory so the editing operation improves over time.

See `docs/project_motivation.md` for the full writeup including detailed comparisons with ERGO and Huang et al.

### Memory-Based Learning

Reflect on previous trajectories to record takeaways (what to try, what to avoid) for future instances. This is a form of inference-time learning applicable to any LLM process. The initial implementation follows Dynamic Cheatsheet (Suzgun et al 2025), but we use the term "memory-based learning" since we plan extensions including retrieval to avoid token limits. Key applications:
- Baseline assistant (can memory-based learning discover strategies/pitfalls from past trajectories to improve performance even without editing?)
- The context editor itself (how to edit)
- The agentic decision-maker (when to trigger an edit)

Memory supports three learning modes: **continual** (update after each batch during simulation), **offline** (learn from saved trajectories without running new simulations), and **frozen** (load a pre-built memory snapshot). Batch updates use a Reflect-then-Unify algorithm: parallel per-trajectory reflections → single unify call.

## Build and Run Commands

```bash
# Install package in development mode
pip install -e ".[all]"

# Run experiments with Hydra config (main entry point)
ctx-editor                                    # Uses default config
ctx-editor experiment=context_edit model=gpt4o_mini task=math
ctx-editor execution.max_concurrent=5 logging.verbose=true

# Run original LIC simulations
python src/lic/run_simulations.py --tasks math --models gpt-4o-mini --N_workers 4

# Linting and formatting
black src/ --line-length 100
ruff check src/
mypy src/
```

## Architecture

### Two-Layer Design
- **`src/ctx_editor/`** - New evaluation framework with strategy-based context manipulation
- **`src/lic/`** - Original "Lost in Conversation" simulation code from Microsoft Research

### Core Components (ctx_editor)

**Strategies** (`strategies/`): Control how context is prepared before each assistant turn. Three main settings:
- **S0** — `BaselineStrategy` — No context modification, full conversation passed through
- **S1** — `AppendAnalysisStrategy` (`append_analysis.py`) — Runs the analyzer, appends structured analysis (task spec, aligned content, issues) to the last user message. Append-only, no rewriting.
- **S2** — `ContextEditV2Strategy` (`context_edit_v2.py`) — Runs the analyzer; if substantive issues found, rewrites context using a `[compacted conversation]` role containing the task spec and aligned content (issues are *not* reintroduced). If no issues, passes through like S0.

Both S1 and S2 are powered by the `ConversationAnalyzer` (`analyzer.py`), which uses a two-query architecture (v6):
  1. **Q1 — Task Spec**: sees *only* user messages → extracts a clean task specification (no assistant contamination)
  2. **Q2 — Comparison**: sees task spec + full conversation + optional memory cheatsheet → produces `aligned` (what's right) and `issues` (what contradicts the spec)

  Edit decisions are implicit: the presence of substantive `issues` content triggers editing (no explicit yes/no flag). Prompts are externalized to `strategies/prompts/` for versioning.

Legacy strategies (kept for backward compatibility/comparison with earlier results):
- `ContextEditStrategy` (`context_edit.py`) — Original single-pass context compression
- `AgenticEditStrategy` (`agentic_edit.py`) — LLM-based decision on when/how to edit
- `ReflectionStrategy` (`reflection.py`) — Append reflections (ablation of editing)

**Agents** (`agents/`): Simulate conversation participants
- `UserAgent` - Generates user responses, reveals shards progressively
- `SystemAgent` - Verifies responses, extracts answers for evaluation

**Core** (`core/`):
- `ConversationSimulator` - Orchestrates multi-turn conversations; renders conversation as a tagged string in a single user message (Option 2 format) via `_render_for_assistant()`
- `ConversationTrace` - Tracks conversation history and metadata; `get_user_messages_string()` extracts numbered user-only messages for the analyzer's Q1

**Tasks** (via `lic/tasks/`): 
- the original LiC project defines 7 tasks: math, code, database, actions, data2text, summary, translation
- for this project we are only interested in: math, code, database, actions

### Configuration (Hydra)

Configs in `src/ctx_editor/config/`:
- `config.yaml` - Main config with defaults
- `experiment/` - Strategy configs (baseline, context_edit, etc.)
- `model/` - Model configs (gpt4o, gpt4o_mini, claude, etc.)
- `task/` - Task configs (math, code, all, etc.)

Override with CLI: `ctx-editor model=claude task=code experiment=context_edit_v2`

### Data Flow

1. Samples loaded from `data/` JSON files (sharded instructions)
2. `ConversationSimulator` runs turns until answer or max_turns
3. Each turn: UserAgent → Strategy.prepare_context → Assistant → SystemAgent.verify
4. Results saved to `outputs/{experiment_name}/{timestamp}/`

## Documentation

- The `docs/` folder contains documentation about the codebase to understand structure/intent
- Please update docs after substantial changes to keep them accurate for future contributors.
- If there is no doc for a part of the codebase you've spent some time understanding or working on, consider adding one! Even a brief overview can be very helpful.

- There is a subfolder `docs/plans/` for writing down larger plans for changes that may span multiple sessions. If asked to write a plan file, save it here.
- If a session is associated with implementing part of a plan file, periodically update the file with progress in case future sessions need to pick up where you left off.
- Completed plans can be moved to `docs/plans/completed/`


## Key Patterns

- Strategies implement `ContextStrategy` protocol with `prepare_context()` method
- Tasks extend `Task` base class in `lic/task_base.py`
- Hydra instantiation uses `_target_` in YAML configs
- Async execution throughout (`asyncio.run()` at entry point)

## Environment Variables

- `OPENAI_API_KEY` or `AZURE_OPENAI_API_KEY` + `AZURE_OPENAI_ENDPOINT`
- `ANTHROPIC_API_KEY` (for Claude models)
- Place in `.env` file at repo root (auto-loaded)

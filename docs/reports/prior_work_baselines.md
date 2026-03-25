# Prior Work Baselines: Huang (Omit Assistant) & ERGO (Concatenate User)

**Date**: 2026-03-21
**Branch**: `main`

## Motivation

Reviewers will ask: "Why not just omit assistant messages (Huang et al.) or concatenate user messages (ERGO)?" These are simpler approaches from prior work that don't require an LLM-based analyzer. We implement and evaluate both using the same replay methodology as our main experiments, for direct comparison.

## Setup

### Strategies Implemented

**OmitAssistantStrategy** (`src/ctx_editor/strategies/prior_work_baselines.py`):
- Implements Huang et al. (2026) "omit all assistant messages" approach
- Filters active messages to keep only `system` + `user` roles
- No LLM calls, no consolidation — just message filtering
- The assistant sees the system prompt and all user messages in their original multi-turn format

**ConcatenateUserStrategy** (`src/ctx_editor/strategies/prior_work_baselines.py`):
- Approximates ERGO (Khalid et al., 2025) context reset without entropy-based triggering
- Collects all unique user messages via `trace.get_user_messages_string(all_unique=True)`
- Resets conversation to: system message + single user message containing all numbered user messages
- Prefixed with "Here are all the messages from the user so far. Please provide a complete, correct response based on all of them."
- No LLM calls — just string concatenation and trace reset

### Key Difference Between the Two

- **Omit Assistant**: Preserves the multi-turn structure of user messages (each as a separate turn). The assistant sees `[system, user_1, user_2, ..., user_k]` rendered via Option 2 format.
- **Concatenate User**: Flattens all user messages into a single turn and resets context. The assistant sees `[system, concatenated_user]` — closer to a single-turn setting.

### Model & Replay Configuration

Identical to the main v8 experiments (documented in `docs/reports/v8_batch_results.md`):
- **Assistant**: gpt-5-mini (reasoning_effort: medium, temperature: 1.0 forced)
- **Replay**: depth=1 (final turn only), from pre-computed baseline traces
- **False negative filtering**: enabled (same exclusions as main experiments)
- **Max concurrent**: 8

### Commands Run

```bash
# Math — omit assistant
ctx-editor experiment=omit_assistant task=dev_math model=gpt5_mini \
  execution.max_concurrent=8 execution.replay_turns=1 \
  execution.replay_source=data/baseline_traces_v2/math logging.verbose=false

# Math — concatenate user
ctx-editor experiment=concatenate_user task=dev_math model=gpt5_mini \
  execution.max_concurrent=8 execution.replay_turns=1 \
  execution.replay_source=data/baseline_traces_v2/math logging.verbose=false

# Code — omit assistant
ctx-editor experiment=omit_assistant task=dev_code model=gpt5_mini \
  execution.max_concurrent=8 execution.replay_turns=1 \
  execution.replay_source=data/baseline_traces_v2/code logging.verbose=false

# Code — concatenate user
ctx-editor experiment=concatenate_user task=dev_code model=gpt5_mini \
  execution.max_concurrent=8 execution.replay_turns=1 \
  execution.replay_source=data/baseline_traces_v2/code logging.verbose=false

# Database — omit assistant
ctx-editor experiment=omit_assistant task=dev_database model=gpt5_mini \
  execution.max_concurrent=8 execution.replay_turns=1 \
  execution.replay_source=data/baseline_traces_v2/database logging.verbose=false

# Database — concatenate user
ctx-editor experiment=concatenate_user task=dev_database model=gpt5_mini \
  execution.max_concurrent=8 execution.replay_turns=1 \
  execution.replay_source=data/baseline_traces_v2/database logging.verbose=false

# Actions — omit assistant
ctx-editor experiment=omit_assistant task=dev_actions model=gpt5_mini \
  execution.max_concurrent=8 execution.replay_turns=1 \
  execution.replay_source=data/baseline_traces/actions logging.verbose=false

# Actions — concatenate user
ctx-editor experiment=concatenate_user task=dev_actions model=gpt5_mini \
  execution.max_concurrent=8 execution.replay_turns=1 \
  execution.replay_source=data/baseline_traces/actions logging.verbose=false
```

### Experiment Configs

- `src/ctx_editor/config/experiment/omit_assistant.yaml`
- `src/ctx_editor/config/experiment/concatenate_user.yaml`

## Results

### Prior Work Baselines

| Strategy | Math (n=20) | Code (n=19) | Database (n=25) | Actions (n=23) |
|----------|:-----------:|:-----------:|:---------------:|:--------------:|
| Omit Assistant (Huang) | 85% (17/20) | 78% (14/18 adj) | 32% (8/25) | 83% (19/23) |
| Concatenate User (ERGO) | 84% (16/19 adj) | 68% (13/19) | 32% (8/25) | 87% (20/23) |

Note: "adj" = adjusted for user-sim-induced failures detected during this run. Omit-assistant code had 1 additional user-sim exclusion (14/18 adj = 77.8%); concatenate-user math had 1 additional (16/19 adj = 84.2%).

### Full Comparison Table

| Strategy | Math | Code | Database | Actions | Source |
|----------|:----:|:----:|:--------:|:-------:|-------|
| **Baseline (S0)** | 60% | 16% | 4% | 9% | v8 batch (2026-03-16) |
| **Omit Assistant** | 85% | 78% | 32% | 83% | this report |
| **Concatenate User** | 84% | 68% | 32% | 87% | this report |
| **Append Analysis (S1)** | 80% | 56% | 32% | 22% | v8 batch |
| **Context Edit (S1.5)** | 80% | 69% | 40% | 30% | v8 batch |
| **Gated Context Edit (S2)** | 75% | 72% | 44% | 13% | v8 batch |
| **Append Analysis + Mem** | **90%** | 68% | **44%** | 9% | v8 batch |
| **Context Edit + Mem** | 85% | 68% | **44%** | 30% | v8 batch |

### Provenance of V8 Batch Results

All v8 batch results come from the experiments documented in `docs/reports/v8_batch_results.md`, run on 2026-03-16/17 on branch `newleaf2` (merged to main at `89fa4cc`). Key details:

- **Script**: `scripts/run_replay_v8.sh`
- **Replay sources**: `data/baseline_traces_v2/{math,code,database}`, `data/baseline_traces/actions`
- **Analyzer prompts**: v8 two-query (hard attention — Query 1 sees user msgs only)
- **Memory**: continual learning, batched (batch_size=5), oracle-guided reflection, 1500 word cap
- **Strategy mapping**: "Append Analysis" = S1, "Context Edit" = S1.5 (always-reset), "Gated Context Edit" = S2

**Output directories (v8 batch)**:
- S0: `outputs/2026-03-16/19-13-13` (math), etc.
- S1: `outputs/2026-03-16/20-08-42` (math), etc.
- S1.5: `outputs/2026-03-17/01-21-21` (math), etc.
- S2: `outputs/2026-03-16/21-13-55` (math), etc.
- S0+mem: `outputs/2026-03-16/19-29-11` (math), etc.
- S1+mem: `outputs/2026-03-16/20-33-21` (math), etc.
- S1.5+mem: `outputs/2026-03-17/08-13-54` (math/code), `outputs/2026-03-17/08-19-23` (database)

Full directory listing in `docs/reports/v8_batch_results.md` lines 160-206.

## Analysis

### Where prior work baselines win

**Actions (+53-57pp over our best)**: Both simple baselines massively outperform all our methods. Our best (Context Edit, 30%) is 53pp below omit-assistant (83%) and 57pp below concatenate-user (87%). The actions task requires parallel function calls — the analysis pipeline appears to introduce noise into the structured output format, while simply giving the model clean user messages lets it solve from scratch.

**Code (+10pp over our best)**: Omit-assistant (78%) beats our best no-memory result (Gated Context Edit, 72%) and our best overall (Append Analysis + Memory, 68%). The raw user messages apparently contain enough information for code generation without consolidation.

### Where our methods win

**Database (+12pp)**: Our best (Append Analysis + Memory and Context Edit + Memory, both 44%) outperforms both baselines (32% each). Database tasks require SQL generation against specific schemas — the consolidation step in our task spec extraction helps the model produce correct queries. Raw fragmented user messages about schemas, filters, and joins are harder to work with.

**Math (+5pp)**: Append Analysis + Memory (90%) beats both baselines (84-85%). Memory-trained analysis produces better task specs for math word problems than raw user messages.

### Why actions is so different

The actions result is the most striking. Hypothesis: the actions task (parallel function calls) has the highest structural complexity in its *output format*. Our analysis pipeline processes user messages through an analyzer, which outputs natural language (task spec, aligned, issues). This natural language intermediary may lose critical structural information about function call syntax that the raw user messages preserve. Additionally, our Context Edit strategy on actions (30%) actually performed *worse* than Append Analysis (22%) in the memory condition — suggesting the analysis itself was interfering.

### Interpretation for the paper

These results reshape the narrative:

1. **LiC favors simple approaches** because rederivation is cheap. On 3/4 tasks, just removing assistant messages and solving from scratch matches or beats our analysis pipeline.

2. **Our analysis adds value through consolidation**, not just assistant removal. This is visible on database (where schema-grounded consolidation helps) and math with memory (where learned principles improve spec quality).

3. **The real contribution is the framework for settings where simple removal fails**:
   - Soft-attention decontamination (Section 5.4 in paper) — when you can't hide assistant messages
   - CollabLLM (Section 5.5) — collaborative settings where assistant contributions matter
   - Memory-based learning — cross-instance knowledge that simple baselines can't accumulate

4. **Executive dysfunction finding stands regardless** — it explains *why* omit-assistant works so well and is the theoretical grounding for all approaches including ours.

## Output Directories

| Run | Accuracy | Dir |
|-----|:--------:|-----|
| Omit assistant, math | 85% (17/20) | `outputs/2026-03-21/05-12-15` |
| Concatenate user, math | 84% (16/19 adj) | `outputs/2026-03-21/05-15-02` |
| Omit assistant, code | 78% (14/18 adj) | `outputs/2026-03-21/05-15-03` |
| Concatenate user, code | 68% (13/19) | `outputs/2026-03-21/05-15-04` |
| Omit assistant, database | 32% (8/25) | `outputs/2026-03-21/05-15-06` |
| Concatenate user, database | 32% (8/25) | `outputs/2026-03-21/05-15-07` |
| Omit assistant, actions | 83% (19/23) | `outputs/2026-03-21/05-15-08` |
| Concatenate user, actions | 87% (20/23) | `outputs/2026-03-21/05-15-09` |

## Files Created

- `src/ctx_editor/strategies/prior_work_baselines.py` — OmitAssistantStrategy, ConcatenateUserStrategy
- `src/ctx_editor/config/experiment/omit_assistant.yaml`
- `src/ctx_editor/config/experiment/concatenate_user.yaml`
- `scripts/run_prior_work_baselines.sh`
- `docs/reports/prior_work_baselines.md` (this file)

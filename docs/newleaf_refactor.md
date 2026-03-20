# Newleaf Branch Refactor

Branch: `newleaf`

## Summary of Changes

### 1. Conversation Format (Option 2)

**File**: `src/ctx_editor/core/simulator.py`

Switched from passing conversation as `list[message_dicts]` (alternating user/assistant API messages) to rendering the conversation as a tagged string inside a single user message.

**Before** (Option 1):
```json
[
  {"role": "system", "content": "..."},
  {"role": "user", "content": "first user msg"},
  {"role": "assistant", "content": "first response"},
  {"role": "user", "content": "second user msg"}
]
```

**After** (Option 2):
```json
[
  {"role": "system", "content": "..."},
  {"role": "user", "content": "Here is the current conversation:\n\n[user]\nfirst user msg\n\n[assistant]\nfirst response\n\n[user]\nsecond user msg\n\nPlease respond to the user..."}
]
```

**Motivation**: Full control over rendering for novel components (analysis injection, edited context). API-agnostic format.

**Implementation**: `ConversationSimulator._render_for_assistant()` handles the conversion. Strategies still return `list[Message]` — the rendering is done at the simulator level.

### 2. ConversationAnalyzer (First-Class Component)

**File**: `src/ctx_editor/strategies/analyzer.py`

Central analysis component that both S1 and S2 strategies use. Produces structured output:
- `<user_intent>`: Collated user requirements (from user messages only)
- `<approach_evaluation>`: Critical review of assistant's approach
- `<pivot_decision>`: yes/no on whether fundamental direction change is needed

**Design choices**:
- Framed as independent third-party review (not self-reflection) to reduce model bias
- Previous analyses A_j are NOT included when generating A_i — analyzer always sees raw conversation
- Prompt explains the over-commitment failure mode so the analyzer knows what to look for

### 3. Simplified Settings (S0, S1, S2)

| Setting | Strategy Class | Description |
|---------|---------------|-------------|
| S0 | `BaselineStrategy` | No modification — full conversation passed through |
| S1 | `AppendAnalysisStrategy` | Analysis appended to context, no rewriting |
| S2 | `ContextEditV2Strategy` | Analysis-driven: pivot → rewrite context; no pivot → baseline |

**S1** (`append_analysis.py`): Generates analysis, appends to last user message in `<conversation_analysis>` tags. System message gets a one-time addendum explaining the tags.

**S2** (`context_edit_v2.py`): Runs same analyzer. If `pivot_needed=True`, rewrites context using the analysis output (user intent as user message, approach eval in system notes). If `pivot_needed=False`, passes through like S0.

**Old strategies preserved**: `ContextEditStrategy`, `AgenticEditStrategy`, `ReflectionStrategy` remain in the codebase for backward compatibility and comparison.

### 4. Error Attribution Integration

**Files**: `error_analysis.py`, `run_experiment.py`, `config/config.yaml`

Two modes:
- **batch** (default): After all simulations, analyze incorrect results
- **immediate**: Analyze each incorrect result as soon as it completes

Config:
```yaml
error_attribution:
  enabled: false
  mode: batch  # immediate | batch
  model: gpt-4o-mini
```

### 5. Auto min_turns Computation

**File**: `run_experiment.py`

When strategy config has `min_turns: auto`, computes `min_turns = max(min_shards - 2, 2)` from the loaded task data. Ensures at least 2 analysis passes per conversation.

### 6. Experiment Configs

New configs in `src/ctx_editor/config/experiment/`:
- `append_analysis.yaml` — S1
- `append_analysis_memory.yaml` — S1 + memory
- `context_edit_v2.yaml` — S2
- `context_edit_v2_memory.yaml` — S2 + memory

Usage: `ctx-editor experiment=append_analysis` or `ctx-editor experiment=context_edit_v2`

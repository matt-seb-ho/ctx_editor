# Replay Mode: Fast Evaluation of Context Interventions

## Motivation

Full conversation simulation is expensive: every run re-generates all user messages, all assistant responses across every turn, and all verification/extraction calls. When comparing context intervention strategies (S1, S2) against a baseline (S0), the conversational prefix — everything up to the final assistant response — is identical if we hold the user agent and earlier assistant turns fixed.

Replay mode exploits this by **reusing saved baseline traces**. It loads the full conversation from a previous baseline run, strips the final assistant response, applies a context intervention strategy, and regenerates only the last turn. This gives a controlled comparison (identical conversational prefix) at a fraction of the cost and time.

## How It Works

```
Baseline trace (saved):
  [system] → [user₁] → [assistant₁] → [user₂] → [assistant₂] → [user₃] → [assistant₃✓]
                                                                              ↑ remove this

Replay input:
  [system] → [user₁] → [assistant₁] → [user₂] → [assistant₂] → [user₃]

Replay execution:
  1. Load trace, truncate final assistant message
  2. Apply context strategy (e.g. ContextEditV2) to the prefix
  3. Generate new assistant response
  4. Verify and evaluate
```

### What gets truncated

- The last **visible** assistant message is removed from the trace
- Trailing `verification` and `answer_evaluation` log entries (which corresponded to that removed response) are also stripped
- All earlier messages, logs, and shard revelations are preserved exactly as they were

## Usage

Replay is controlled by the `execution.replay_source` config key. Setting it activates replay mode regardless of execution mode — it composes with `parallel`, `batched`, and `sequential`.

```bash
# S2 replay (parallel, no memory)
ctx-editor experiment=context_edit_v2 \
  execution.replay_source=outputs/2026-03-06/02-22-02/traces/math/baseline/ \
  task=math model=gpt5_mini

# S1 replay
ctx-editor experiment=append_analysis \
  execution.replay_source=outputs/2026-03-06/02-22-02/traces/math/baseline/ \
  task=math model=gpt5_mini

# S2 + memory replay (batched with continual learning)
ctx-editor experiment=context_edit_v2_memory \
  execution.mode=batched execution.batch_size=5 \
  execution.replay_source=outputs/2026-03-06/02-22-02/traces/math/baseline/ \
  memory.enabled=true memory.source=continual memory.save_path=memory_out.json \
  task=math model=gpt5_mini

# S1 + memory replay (sequential learning)
ctx-editor experiment=append_analysis_memory \
  execution.mode=sequential \
  execution.replay_source=outputs/2026-03-06/02-22-02/traces/math/baseline/ \
  memory.enabled=true memory.source=continual memory.save_path=memory_out.json \
  task=math model=gpt5_mini

# The replay_source can be:
#   - A traces subdirectory:  outputs/.../traces/math/baseline/
#   - A parent output dir:    outputs/2026-03-06/02-22-02/
#   - A results file:         outputs/.../results.json  (if traces are embedded)
```

### Key config

| Parameter | Description |
|-----------|-------------|
| `execution.replay_source` | Path to baseline traces (directory or file). If set, activates replay. |
| `execution.mode` | Works as usual: `parallel`, `batched`, `sequential`. Replay composes with all. |
| `execution.max_concurrent` | Parallelism (same as normal mode) |

All other settings (experiment, model, task, memory) work as usual — the only difference is that user messages come from saved traces instead of being generated live.

### How replay composes with execution modes

Replay is implemented as a **factory wrapper**, not a separate execution mode. When `replay_source` is set:

1. Baseline traces are loaded and matched to samples by `task_id`
2. Unmatched samples are filtered out
3. The `make_simulator` factory is wrapped to inject the replay trace into each simulator
4. `ConversationSimulator.run()` detects the pre-loaded trace (via `trace.provenance`) and delegates to `run_final_turn()` instead of the full simulation loop

This means every execution mode works transparently:

- **parallel**: Each replay runs concurrently with frozen memory (identical to normal parallel)
- **batched + continual memory**: Batches of replays run, memory is updated after each batch via `CheatsheetUpdater.batch_update()`, then the next batch uses the updated memory
- **sequential + continual memory**: Each replay runs one at a time with memory updated after each

## Provenance Tracking

Every replayed trace records where its conversational prefix came from. This metadata is stored in three places:

### 1. On the trace object (`trace.provenance`)

```json
{
  "provenance": {
    "source_path": "outputs/2026-03-06/02-22-02/traces/math/baseline/",
    "source_experiment": "baseline",
    "source_sample_id": "sharded-GSM8K/40",
    "source_is_correct": true,
    "source_score": 1.0,
    "source_models": {"assistant": "gpt-5-mini", "user": "unknown", "system": "unknown"},
    "source_timestamp": "2026-03-06 02:22:44"
  }
}
```

This is serialized into each saved trace JSON file via `to_full_trace()`.

### 2. In the result metadata

Each `SimulationResult` from replay mode includes `{"replay_mode": true}` in its metadata.

### 3. In the metrics file

```json
{
  "replay": {
    "source": "outputs/2026-03-06/02-22-02/traces/math/baseline/"
  }
}
```

## Implementation Details

### Core components

| File | What was added |
|------|---------------|
| `core/trace.py` | `provenance` field on `ConversationTrace`; `from_saved_trace()` classmethod for reconstruction with optional truncation |
| `core/simulator.py` | Optional `trace` parameter in `__init__`; `is_replay` property; `run()` auto-delegates to `run_final_turn()` when replay is detected |
| `execution/replay.py` | `load_baseline_traces()`, `build_replay_trace()`, `ReplayRunner` (standalone parallel replay) |
| `run_experiment.py` | Factory wrapper that injects replay traces when `execution.replay_source` is set; composes with all execution modes |
| `config/config.yaml` | `execution.replay_source` config key |

### Matching samples to traces

Problems are matched to traces by `task_id` / `sample_id`. Problems without a matching baseline trace are filtered out with a warning. This means you can point `replay_source` at a directory containing traces for a subset of problems and only those will be replayed.

### Strategy behavior in replay

Strategies see the full conversation history (all prior turns from the baseline) and operate on the final user message exactly as they would in a live run. From the strategy's perspective, replay mode is indistinguishable from a normal run — the only difference is that the conversational prefix was loaded from disk rather than generated live.

Note that strategies with `min_turns` thresholds (like `ContextEditV2Strategy` with `min_turns=3`) will evaluate the number of assistant turns already in the trace to decide whether to activate. Since the replayed trace includes all prior assistant turns from the baseline, the strategy will see the correct turn count.

### Memory injection in replay

Memory injection (via `BaseStrategy._inject_memory_to_trace()`) checks `trace.logs` for a `memory_injected` log entry. Since baseline traces never had memory injected, the check returns `False` and memory is injected on the first `prepare_context()` call. This works correctly for both `target="system"` and `target="analyzer"`.

## Limitations

- Replay only regenerates the **final** assistant turn. If the intervention would have changed behavior at earlier turns (e.g., an earlier context edit might have led to different user responses), replay won't capture that effect.
- The approach assumes the baseline used the same system prompt and task configuration. Mismatches between the replay config and the baseline config (e.g., different system prompts) will produce invalid comparisons.
- Replay does not re-run the user agent, so `user_mode` settings are irrelevant in replay mode.

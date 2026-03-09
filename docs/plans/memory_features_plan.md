# Plan: Memory Learning Features — Off-policy, Batched, Offline

## Current State

The memory system has been refactored from `cheatsheet/` to `memory/` with clean ABCs (`MemoryModule`, `MemoryUpdater`) and one concrete implementation (`CheatsheetMemory`, `CheatsheetUpdater`).

**What exists today:**
- `CheatsheetUpdater.update_from_trajectory()` — reflects on one trajectory, rewrites the full memory
- `CheatsheetUpdater.batch_update()` — dumps ALL trajectories into one LLM call, rewrites memory (the "insane" approach)
- `BatchedRunner` calls `batch_update()` after each batch
- `BatchedRunner.run_sequential()` calls `update_from_trajectory()` after each problem
- Memory can target `assistant` or `context_editor` (config: `memory.target`)
- A single `CheatsheetUpdater` with one reflection prompt handles all cases
- Strategies already accept `memory` in `prepare_context()` and can inject it to system message or use it in editor prompts

**What's missing:**
- No target-specific update logic (same reflection prompt regardless of what we're improving)
- No target-specific trajectory rendering (context edit traces need special handling)
- `batch_update()` is a single-LLM-call approach that doesn't scale
- No offline mode (memory update always interleaved with trajectory generation)
- No off-policy support (updater assumes trajectories come from the same strategy)

---

## Change 1: Target-Aware Memory Updates ✅ COMPLETE

### 1.1 Multiple update targets with different source trajectories

**Problem:** Currently one `CheatsheetUpdater` with one prompt. We need different reflection behaviour depending on what we're improving (assistant, context editor, decision-maker) and the trajectories may come from any strategy.

**Design:** Introduce a `target` parameter on `CheatsheetUpdater` (or subclass) that controls:
1. **Reflection prompt** — what questions to ask about the trajectory
2. **Trajectory rendering** — how to present the conversation to the reflector
3. **Grounding framing** — how to explain the full-spec question / ground truth

Concrete targets:
- **`assistant`** — "How could the assistant have responded better? What patterns/pitfalls should it watch for?"
- **`context_editor`** — "How could the context edit have been better? What should be preserved/removed?"
- **`edit_decision`** — "Was the decision to edit (or not) correct? What signals indicate editing is needed?"

**Implementation options:**

Option A: Single class with target-based dispatch
```python
class CheatsheetUpdater(MemoryUpdater):
    def __init__(self, target: str = "assistant", ...):
        self.target = target
        self.reflection_prompt = PROMPTS_BY_TARGET[target]
        self.trajectory_renderer = RENDERERS_BY_TARGET[target]
```

Option B: Subclasses per target
```python
class AssistantMemoryUpdater(CheatsheetUpdater): ...
class ContextEditorMemoryUpdater(CheatsheetUpdater): ...
class EditDecisionMemoryUpdater(CheatsheetUpdater): ...
```

**Recommendation:** Option A (single class, dispatch by target). Simpler, less boilerplate, easy to add targets. The differences are in prompts and rendering, not control flow.

### 1.2 Target-specific trajectory rendering

**Problem:** When targeting the context editor, we need to show the full conversation *including* context edit operations — the resets, the condensed context, etc. The current `_extract_conversation()` just dumps role/content pairs and loses edit boundaries.

**Design:** A `TrajectoryRenderer` (or just a function per target) that:

- **For `assistant` target:** Standard role/content rendering (current behaviour). Omit internal edit operations.
- **For `context_editor` target:**
  - Render the full conversation with clear markers for context edits
  - Mark where new threads begin after edits
  - Include the editor's condensed output at each edit point
  - Frame: "The memory should help the context editor do its job better, not the assistant directly"
- **For `edit_decision` target:**
  - Show conversation state at each decision point
  - Include the decision made and its outcome
  - Frame: "The memory should help decide *when* editing is beneficial"

Source for edit operations: `trace.logs` already contains `context_edit_output` and `edit_decision` entries with full details.

### 1.3 Target-specific reflection prompts

Each target needs a different reflection prompt. Key differences:

| Target | Reflection focus | Grounding framing |
|--------|-----------------|-------------------|
| `assistant` | Response quality, strategy, pitfalls | "The full-spec question is what the assistant should have eventually understood" |
| `context_editor` | What to preserve/remove, edit quality | "The full-spec question shows what information matters; the editor should make it easier for the assistant to reach this understanding" |
| `edit_decision` | When to trigger edits, false positives/negatives | "Did editing at this point help or hurt? What conversation signals predicted the outcome?" |

**Common frounding framing across all targets:** The full-spec question and ground truth answer represent what should have been understood/produced by the end of the conversation. These are not cheats — they're the "answer key" for reflection.

### 1.4 Combined memory update for coupled operations (agentic edit)

**Problem:** The agentic edit strategy has two tightly coupled steps: (1) decide whether to edit, (2) perform the edit. These could have separate memories, but updating them independently wastes context — the LLM reflecting on one step has already understood the other.

**Design:** Allow a single LLM reflection call to produce updates for multiple memory targets simultaneously.

```python
class CombinedMemoryUpdater(MemoryUpdater):
    """Updates multiple memory modules from a single reflection."""

    async def update_from_trajectory(
        self,
        memories: dict[str, MemoryModule],  # e.g. {"edit_decision": ..., "context_editor": ...}
        trajectory: SimulationResult,
        model_client: ModelClient,
    ) -> dict[str, MemoryModule]:
        # Single LLM call, structured output with sections per target
        ...
```

The reflection prompt asks the LLM to produce separate sections:
```
<decision_memory_update>...</decision_memory_update>
<editor_memory_update>...</editor_memory_update>
```

**Note:** This is a later addition — implement single-target updaters first, then add this as an optimization for agentic edit.

---

## Change 2: Fix Batched Memory Updates

**Problem:** `batch_update()` dumps all trajectories into one LLM call. This doesn't scale (token limits) and produces low-quality reflections (too much to process at once).

**New algorithm — Reflect-then-Unify:**

```
Step 1: REFLECT (parallelizable across trajectories)
  For each trajectory:
    - Render trajectory for the target
    - Generate per-trajectory takeaways (independent LLM calls)

Step 2: UNIFY (single LLM call)
  - Input: current memory + all per-trajectory takeaways
  - Output: updated memory that integrates all takeaways consistently
```

**Why this is better:**
- Step 1 is embarrassingly parallel — all reflections can run concurrently
- Each reflection sees one trajectory in full detail (no token budget competition)
- Step 2 is a synthesis task that's much simpler than analyzing N raw trajectories
- The unify step can deduplicate, resolve conflicts, and maintain coherence

**Implementation:**

```python
class CheatsheetUpdater(MemoryUpdater):
    async def _reflect_on_trajectory(self, trajectory, model_client) -> str:
        """Generate takeaways from a single trajectory. (Step 1)"""
        ...

    async def _unify_takeaways(self, memory, takeaways, model_client) -> str:
        """Merge takeaways into a coherent memory update. (Step 2)"""
        ...

    async def batch_update(self, memory, trajectories, model_client) -> MemoryModule:
        """Reflect-then-Unify batch update."""
        # Step 1: parallel reflection
        takeaways = await asyncio.gather(*[
            self._reflect_on_trajectory(t, model_client) for t in trajectories
        ])
        # Step 2: unify
        new_content = await self._unify_takeaways(memory, takeaways, model_client)
        memory.update(new_content)
        return memory
```

**Prompt for Step 1 (reflect):** Target-specific (from Change 1.3), but ends with "Produce a bullet list of takeaways" rather than "Rewrite the full memory."

**Prompt for Step 2 (unify):**
```
Here is the current memory and a set of takeaways from recent trajectories.
Integrate these takeaways into an updated memory. Deduplicate, resolve
contradictions (prefer newer evidence), and keep the result concise and actionable.

<current_memory>...</current_memory>
<takeaways>
- From trajectory 1: ...
- From trajectory 2: ...
</takeaways>

Updated memory:
```

---

## Change 3: Offline Learning Mode

**Problem:** Currently, memory updates are interleaved with trajectory generation (online learning). We also want offline learning: initialize memory from a fixed set of pre-existing trajectories without generating new ones.

**Design:** A new execution mode (or a standalone script) that:
1. Loads a set of trajectories from saved results (JSON files in `outputs/`)
2. Runs the memory update pipeline (using the Reflect-then-Unify approach from Change 2)
3. Saves the resulting memory to disk

This composes naturally with off-policy learning (Change 1.1) — the trajectories can come from any strategy.

**Implementation:**

```python
# New file: src/ctx_editor/execution/offline.py

class OfflineMemoryLearner:
    """Learn memory from pre-existing trajectories without running new simulations."""

    def __init__(self, updater: MemoryUpdater, model_client: ModelClient):
        self.updater = updater
        self.model_client = model_client

    async def learn(
        self,
        trajectories: list[SimulationResult],
        memory: Optional[MemoryModule] = None,
        batch_size: int = 5,
    ) -> MemoryModule:
        """Run memory updates over saved trajectories.

        Processes trajectories in batches using Reflect-then-Unify.
        """
        if memory is None:
            memory = CheatsheetMemory()

        for batch in batches(trajectories, batch_size):
            memory = await self.updater.batch_update(memory, batch, self.model_client)

        return memory
```

**Config addition:**
```yaml
# config.yaml
memory:
  enabled: false
  source: null          # null | path to frozen memory | "continual" | "offline"
  offline_trajectories: null  # path to saved results for offline learning
  target: assistant
```

**CLI usage:**
```bash
# Offline: learn memory from baseline trajectories, targeting the context editor
ctx-editor memory.source=offline \
  memory.offline_trajectories=outputs/baseline_run/results.json \
  memory.target=context_editor \
  memory.save_path=memories/editor_from_baseline.json
```

Alternatively, a standalone script entry point:
```bash
ctx-learn-memory \
  --trajectories outputs/baseline_run/ \
  --target context_editor \
  --output memories/editor_v1.json
```

---

## Progress Notes

### Change 1 — completed
- `memory/prompts/assistant_reflection.txt` — target-specific prompt
- `memory/prompts/context_editor_reflection.txt` — target-specific prompt
- `memory/prompts/edit_decision_reflection.txt` — target-specific prompt
- `memory/renderers.py` — `render_for_assistant`, `render_for_context_editor`, `render_for_edit_decision`, `RENDERERS` registry
- `memory/cheatsheet.py` — `CheatsheetUpdater` now accepts `target` param (default `"assistant"`); loads prompt from `memory/prompts/` by default; uses target-specific renderer in `_render_trajectory`; fixed pre-existing f-string syntax bug in `batch_update`
- `memory/.__init__.py` — exports `RENDERERS`
- Section 1.4 (CombinedMemoryUpdater) deferred to Phase 4 per plan

---

## Implementation Order & Parallelism

```
Phase 1: Foundation (sequential — later phases depend on this)
├── 1a. Target-specific trajectory renderers        ← can be parallel with 1b
├── 1b. Target-specific reflection prompts          ← can be parallel with 1a
└── 1c. Wire target param into CheatsheetUpdater    ← depends on 1a, 1b

Phase 2: Batch algorithm (depends on Phase 1)
├── 2a. Implement _reflect_on_trajectory()          ← uses Phase 1 renderers/prompts
├── 2b. Implement _unify_takeaways()                ← independent of 2a
└── 2c. Rewrite batch_update()                      ← depends on 2a, 2b

Phase 3: Offline learning (depends on Phase 2)
├── 3a. Trajectory loader (read saved results)      ← independent
├── 3b. OfflineMemoryLearner class                  ← depends on 2c, 3a
└── 3c. Config/CLI integration                      ← depends on 3b

Phase 4: Combined updater for agentic edit (depends on Phase 1)
├── 4a. CombinedMemoryUpdater class                 ← depends on 1c
├── 4b. Multi-section reflection prompt             ← can be parallel with 4a
└── 4c. Wire into agentic edit config               ← depends on 4a, 4b
```

**What's parallelizable:**
- 1a ∥ 1b (renderers and prompts are independent artifacts)
- 2a ∥ 2b (reflect and unify are independent methods)
- 3a ∥ anything in Phase 2 (just file I/O)
- Phase 4 can start after Phase 1 (independent of Phases 2–3)
- **Phase 3 and Phase 4 are fully independent of each other**

**Estimated file changes:**

| File | Changes |
|------|---------|
| `memory/cheatsheet.py` | Add `target` param, renderers, new prompts, rewrite `batch_update` |
| `memory/renderers.py` | **New** — trajectory rendering functions per target |
| `memory/prompts/` | **New** — prompt templates per target (reflection + unify) |
| `memory/combined.py` | **New** — `CombinedMemoryUpdater` for agentic edit |
| `execution/offline.py` | **New** — `OfflineMemoryLearner` |
| `execution/batched.py` | Minor — switch from old `batch_update` to new one (should be transparent) |
| `config/config.yaml` | Add offline config options |
| `config/experiment/*.yaml` | Add target-specific memory configs |
| `run_experiment.py` | Add offline mode branch |

---

## Open Questions

1. **Memory format:** Should different targets use different memory formats? (e.g., structured sections vs. free-form text) For now, keep free-form text for all — revisit if needed.

2. **Trajectory filtering for offline:** Should we filter trajectories before offline learning? (e.g., only failures, only certain tasks) Probably yes — add filter options to config.

3. **Memory size management:** As memory grows across many trajectories, how do we keep it concise? The unify step naturally compresses, but we may want explicit token budgets. Punt for now.

4. **Evaluation of memory quality:** How do we know if memory is helping? Compare with/without memory on held-out problems. This is already possible with the existing experiment framework.

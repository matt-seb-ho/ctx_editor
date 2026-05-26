# tau2 Overnight Plan — fill the mega-table tau2 row

**Status**: draft, pending user sign-off.
**Predecessors**: `docs/post_may18_tau2_plan.md` (original scoping doc), `docs/post_may18_tau2_followups.md` (Phase 0+1 findings).

## Goal

Fill the tau2 row of the mega-table with **Baseline, AO, AC3-Augment, AC3-Gated-Reset, AC3-Rewrite (v11)** numbers on `telecom_small` (20 tasks), on at least one model and ideally two. Demonstrate that AC3 variants improve over Baseline + AO.

## Design principle (per user message)

Two competing constraints to balance:

1. **Method consistency** — same general recipe across benchmarks: LLM-reflects-on-turns with siloed analyzer, identify task spec + pollution, produce a cleaned-up context for continuation.
2. **Task-fit adjustments** — tau2 is agentic (tool-calls, backend state), so verbatim ports of LiC prompts won't work. Adapt where necessary while keeping the recipe intact.

Concretely: keep v8's analyzer-centered framing, open-ended `<new_context>` output, role-boundary clause, and reviewer-trust framing. Layer in tau2-specific bits: environment-state preamble, tool-list block, exact-data-preservation language.

## The gating question (your raised concern)

In LiC / CollabLLM / WildChat we used **last-turn replay** — the context-edit pipeline fires exactly once per task (on the last user turn). In tau2 we run **full trajectories** with no last-turn-replay infrastructure (deferred per `docs/notes/literature/tau2_replay_scoping.md`, ~2 dev-days). So we'd potentially fire the pipeline many times per task.

### What we'd do without gating

Tau2 trajectories have ~10-50 turns each, with most being tool-call / tool-result loops. Triggering the analyzer on every turn would mean ~20-30 analyzer calls per task × 20 tasks × 3 AC3 strategies × 2 models = O(7k) analyzer calls overnight. With `gpt-5-mini` analyzer at ~1-2s per call, that's wall-tractable but wasteful — most turns don't need editing.

### Existing tau2 gating (already present in `ContextEditAgent`)

The current S2/S3 code has three gating signals stacked:

1. `min_turns` (user-turn count, default 2) — don't run analyzer until the user has actually spoken twice.
2. `assistant_turns ≥ 3` — don't run until the agent has had time to act. Prevents premature reset during the agent's first tool-calling sequence.
3. `max_resets` (default 3) — cap total context-resets per task.
4. `needs_edit` from the analyzer itself — even if we run the analyzer, we only re-build the context when analyzer flags `needs_edit=True` (length-based heuristic + explicit "None" check on the issues section).

This is already conservative and analogous to the LiC paper's gated-reset framing. It's not "every turn" — it's "every turn after warm-up, only if analyzer says editing helps."

### Proposed gating across AC3 variants (mirrors LiC paper)

| Variant | Gating policy |
|---|---|
| **AC3-Augment** (new) | After `min_turns=2`, run analyzer **every user turn** (no `needs_edit` gate). Append analyzer notes to the user message. This is the low-risk variant — analogous to LiC's `AppendAnalysisStrategy` which always fires. |
| **AC3-Gated-Reset (S2)** | After `min_turns=2`, run analyzer; **only reset context when `needs_edit=True`**. Cap at `max_resets=3` per task. Existing tau2 behavior. |
| **AC3-Rewrite (S3)** | Same gating as S2 (`needs_edit` + `min_turns` + `max_resets`). The v11 prompt is what changes — not the gate. |

This matches the LiC paper: Augment is light/always-fire, Reset/Rewrite are gated. The fact that tau2 lets multiple gated fires happen per task is just the consequence of running full trajectories — but the gating math (only fire when analyzer says so) is the same as LiC's "fire only on the last turn."

### Skip "always-on Reset" / "every-k-turn fire"

I considered an "every k turns" periodic fire and an "always-on Reset" variant. Recommendation: skip both.

- **Periodic-fire (every k turns)** breaks consistency. LiC/CollabLLM/WildChat never had a periodic trigger; the LiC paper headline is the *gated* variant. Adding a periodic mode would muddy the cross-benchmark story.
- **Always-on Reset** would fire too aggressively in tau2 (every turn after warm-up). The LiC paper reports gated, not always-on. The plan's original §4 already marks always-on as low priority.

If foundry/wall budget is a concern, the right knobs are `min_turns` and the `needs_edit` heuristic — not periodic gating.

### Analyzer caching (efficiency, not gating)

Tau2's analyzer does NOT use `AnalysisCache` today (it's an LiC-side feature). Most analyzer calls within a task are on slightly-different conversation states, so even with caching the hit rate would be modest. **Skip cache wiring this cycle**; revisit if cost becomes binding.

## Phase plan

### Phase 2 — port v8 → CONTEXT_REWRITE_PROMPT_V11 (~1.5h dev)

Read `src/ctx_editor/strategies/prompts/context_compaction_v8.txt`. Port to `tau2_ctxe/ctx_edit/analyzer.py` as a new constant `CONTEXT_REWRITE_PROMPT_V11`. Inheriting from v8:

- Analyzer-centered framing ("the reviewer's notes are your primary source").
- Open-ended `<new_context>...</new_context>` output (replaces the V10 `CONTEXT_REWRITE_PROMPT` two-section structure).
- Role-boundary clause ("selective attention, not solving the task").
- Removed: "trust user messages over analyzer" framing (v8's wart 1 fix).

Tau2-specific additions:

- **Environment state preamble**: the analyzer also produces an `environment_state` field (CRM/phone snapshot from tool calls). v11 must instruct preservation of these state values exactly. v10 already does this; keep that language.
- **Tool-list footer**: keep the V10 `{tool_names}` block at the end so the rewriter knows what's available.
- **Exact-data preservation**: keep V10's "preserve all concrete data exactly: customer IDs, line IDs, status values, plan details, tool result JSON" instruction.

Add a CLI flag `--rewrite-prompt-version=v10|v11` in `tau2_ctxe/ctx_edit/run_parallel.py` so we can compare. Default = v11.

**Acceptance**: smoke test 1 telecom_small task with `--workers 1 --strategy s3 --rewrite-prompt-version=v11`; eyeball the briefing for sensible structure.

### Phase 3 — implement AugmentAgent (~1h dev)

New class in `tau2_ctxe/ctx_edit/agents.py`:

```python
class AugmentAgent(HalfDuplexAgent[ContextEditAgentState]):
    """Analyzer fires every turn (after min_turns); output appended to last user message.

    Mirrors LiC's AppendAnalysisStrategy. Does not compact / reset; lower
    risk than S2 in agentic tool-call settings. No needs_edit gate.
    """
    def __init__(self, analyzer_model="openai/gpt-5-mini", min_turns=2, **kwargs):
        ...

    def generate_next_message(self, message, state):
        # append incoming, increment turn counter
        # if isinstance(message, UserMessage) and self._should_analyze(state):
        #   result = analyze_conversation(... mode="s2")  # reuse S2 Q2 (richer)
        #   append <analysis>...</analysis> note to the last UserMessage
        # call assistant LLM with augmented context
        ...
```

Reuses `ContextEditAgentState` (analysis log + turn counter). Register in `run_parallel.py` as `--strategy s1` (matches LiC's AC3-Augment label).

**Acceptance**: smoke test on 1 task; inspect rendered conversation to confirm the analyzer note is visible to the agent.

### Phase 4 — skip always-on Reset (per gating decision above)

### Phase 5 — sweep (5 strategies × 2 models × 20 tasks)

**Models** (per user sign-off — three models, foundry sequenced after Azure):

| Priority | Model | Endpoint | Notes |
|---|---|---|---|
| 1 | gpt-5.4 | Azure OAI | No foundry contention; safest first |
| 2 | DeepSeek-V4-Flash | Foundry | Run after gpt-5.4 finishes |
| 3 | Kimi-K2.6 | Foundry | Run after DSV4F finishes (sequential to avoid 429-cascade) |

User decision: include all three (the LiC mega-table set). Strategy: run gpt-5.4 first (Azure, safe), then sequence the two foundry models one after another (not in parallel) to reduce 429-cascade risk.

**Strategies**:

| Label | Variant | Source |
|---|---|---|
| s0 | Baseline | tau2 `LLMAgent` (already) |
| ao | AssistantOmit | tau2 `AssistantOmitAgent` (already) |
| s1 | AC3-Augment | NEW (Phase 3) |
| s2 | AC3-Gated-Reset (V10) | tau2 `ContextEditAgent` (already) |
| s3 | AC3-Rewrite (V11) | tau2 `ContextRewriteAgent` with V11 prompt (Phase 2) |

**Cells**: 5 strategies × 2 models = 10 cells × 20 tasks = **200 task-runs**.

**Run settings**: `--max-steps 50 --min-turns 2 --max-resets 3 --workers 10 --seed 42`. Matches the March-2026 protocol so the new cells are directly comparable to historic gpt-5-mini cells.

**Wall estimate**: ~25–35 min per cell at `--workers 10`. With 2 cells in parallel (paired by model), ~2.5–3h total.

**Launch order**:

1. **gpt-5-mini cells first** (s0, ao, s1, s2, s3) — sanity vs March-2026 paper numbers. If s2/s3 results drift materially from existing baseline, *stop* and investigate before burning gpt-5.4 budget.
2. **gpt-5.4 cells second**, parallelized 2 at a time.

### Phase 6 — mega-table integration (~30min)

1. Extend `scripts/build_mega_table.py` to read tau2 output dirs (different layout from LiC: `tau2_ctxe/ctx_edit/outputs/...`).
2. Write `docs/reports/post_may18_tau2_summary.md` with the per-strategy accuracies, cost/time, takeaways.
3. Update the progress HTML with the new tau2 row.
4. Commit.

## Estimated total

| Phase | Wall |
|---|---|
| Phase 2 (port v11) | ~1.5h dev |
| Phase 3 (AugmentAgent) | ~1h dev |
| Phase 5 (sweep) | ~2.5–3h |
| Phase 6 (docs) | ~30min |
| **Total** | **~5.5h** |

Within a single overnight window. Cost: ~$15-25 in OAI calls (gpt-5.4 cells), gpt-5-mini cells are cheap.

## Open decisions for your sign-off

1. **Skip foundry models (DSV4F, Kimi-K2.6) this cycle?** → recommend **yes** (foundry has been flaky; skip until R6-class workloads drain). Run them in a follow-up cycle.
2. **Single-seed N=1?** → recommend **yes**. Directional read first; multi-seed (3 seeds × headline cells) deferred to follow-up if numbers are informative.
3. **AugmentAgent uses S2's Q2 prompt (richer) or S3's Q2 (terser)?** → recommend **S2's Q2** since Augment doesn't pass through a downstream Q3 LLM, and richer notes will be visible to the agent directly. Matches LiC's Augment using the direct analyzer output.
4. **gpt-5.4 included this cycle, or also defer to a follow-up?** → recommend **include**. Azure OAI doesn't share quota with foundry. Two-model cross-check makes a stronger story.
5. **v11 prompt: include CHAIN-of-thought scratchpad freedom?** v8 says "you may think through your approach in free text first if it helps." → recommend **keep** for v11. Open-ended is the point of the v8 design.
6. **Gated-Reset (S2): re-run with the v10 prompt as-is, OR also upgrade to a "v11 S2 prompt"?** → recommend **re-run as-is (v10)**. Only the Rewrite-prompt port is the R6 winner; S2's prompt is its own thing and changing it now would conflate variables. If S2 needs an upgrade it's a separate cycle.

If you sign off, I'll execute Phases 2-6 in order and have results by morning. Defaults above unless you flag specific deviations.

# tau2 Execution Plan (telecom_small)

**Author**: Claude (drafted 2026-05-22 during R6 LiC Rewrite work)
**Status**: **plan only — do not execute** until R6 work in
`docs/post_may18_r6_plan.md` lands a stable Rewrite configuration.
**Predecessors**:
- `docs/notes/literature/tau2_replay_scoping.md` (why tau2 last-turn
  replay is ~2 dev-days)
- `docs/post_may18_r3_followups.md` (Python 3.13 → tau2 needs 3.12;
  inventory of what's missing in `tau2_ctxe/ctx_edit/agents.py`)
- `docs/analyzer_parity_finding.md` and
  `docs/post_may18_r5_analyzer_parity_plan.md` (the LiC analyzer bug
  whose tau2 analog this plan must guard against)
- `docs/tau2_absorption_decision.md` (option C — federated:
  experiments live in `~/tau2_ctxe/ctx_edit/`, code imports from
  ctx_editor)

## Background — what we're doing and why now

The mega table (`docs/reports/post_may18_r3_mega_table.md`) has the
**tau2 row almost entirely empty**. Existing tau2 numbers are from
March 2026 on `gpt-5-mini` only (Experiments 1–6 in
`tau2_ctxe/ctx_edit/EXPERIMENT_LOG.md`). The user's R3 ask was
"where are the tau2 experiments? With at least augment, reset, and
gated reset." We did not run them in R3 (deferred to scoping) or R5
(env block — `audioop` removed in Python 3.13). This plan removes
both blockers and lays out a concrete execution sequence.

We deliberately wait for R6 to finish because:

1. **Analyzer parity**. tau2 has its own analyzer (`tau2_ctxe/ctx_edit/analyzer.py`)
   with prompt templates `TASK_SPEC_PROMPT_V10`, `COMPARE_PROMPT_V10_S2`,
   `COMPARE_PROMPT_V10_S3`. **S2 and S3 share Q1 (task spec)** but use
   **different Q2 templates** — the same architectural-asymmetry class
   as the LiC bug (`docs/analyzer_parity_finding.md`). We should not
   port the LiC Rewrite winner to tau2 until we've decided whether
   the same parity fix is warranted on the tau2 side.
2. **Strategy parity**. R6 is producing a new Rewrite variant
   (v8 / v9_no_conv / GEPA-optimized v7+) that is meaningfully
   different from the v1 currently encoded in tau2's
   `ContextRewriteAgent`. Porting v1 now would freeze a known-stale
   prompt into tau2.
3. **Foundry coordination**. R6 (and possibly R7) is actively using
   the foundry endpoint. tau2's planned cross-model expansion to
   Kimi-K2.6 (foundry-routed) would contend on the 250 RPM / 250k
   tok/min cap, repeating the R3 429-cascade failure. Sequencing
   tau2 after R6 keeps foundry pressure predictable.

## Scope

- **Benchmark**: tau2-bench `telecom_small` only (20 tasks). Matches
  the user's clarification and existing March-2026 baseline runs.
- **Strategies** (in priority order, see § 3 for what's already
  implemented vs missing):
  1. `s0` Baseline (already in tau2 — `LLMAgent`)
  2. `ao` AO (already — `AssistantOmitAgent`)
  3. `s2` Gated-Reset (already — `ContextEditAgent` *is* the gated
     variant; only compacts on `needs_edit=True`)
  4. `s3` Rewrite (already — `ContextRewriteAgent`; **needs the R6
     prompt port + parity fix before re-running**)
  5. **Augment** — *not in tau2 yet*; § 4 has the implementation
     sketch
  6. **Always-on Reset** — *not in tau2 yet*; lower priority
     because the gated version is what the paper reports
- **Models**: priority order
  1. `openai/gpt-5-mini` — baseline reference (matches March-2026
     paper-config row)
  2. `openai/gpt-5.4` — Azure OAI; **does not contend with foundry**.
     Safest extra model to add while concurrent LiC work is using
     foundry.
  3. `Kimi-K2.6` (foundry) — only after the R6 foundry workload
     drains.
  4. `DeepSeek-V4-Flash` (foundry) — optional; if cost/time budget
     remains.
- **Settings**: `--max-steps 50 --min-turns 2 --max-resets 3
  --workers 10 --seed 42`. Matches the March-2026 protocol so the
  new cells are directly comparable to the historic gpt-5-mini cells.
- **Replays / multi-rep**: single-seed initial pass. Multi-seed
  (3 seeds × headline cells) is a follow-up bullet if the directional
  finding is informative.
- **Last-turn replay**: **deferred** per
  `docs/notes/literature/tau2_replay_scoping.md`. Two dev-days of
  state-snapshot work; not justified until tau2 cell costs become
  the binding constraint.

## Phase plan

### Phase 0 — Python 3.12 venv for tau2 (isolated, ~10 min)

The shared `base` conda env runs Python 3.13.11, which removed
`audioop`. `tau2.voice.synthesis.audio_effects.effects` imports
`audioop` unconditionally, so any `import tau2.agent.llm_agent`
fails. Two reasons not to downgrade the shared env:

1. The other Claude is mid-flight on Python 3.13 with installed
   wheels and possibly in-memory state.
2. tau2's full dep list (loguru, fastapi, uvicorn, deepdiff,
   audioop-shims, …) is heavy and stays better isolated.

```bash
# In ctx_editor cwd is fine; we use absolute paths into the venv.
python3.12 -m venv /home/v-homatthew/tau2_ctxe/.venv
/home/v-homatthew/tau2_ctxe/.venv/bin/pip install --upgrade pip
/home/v-homatthew/tau2_ctxe/.venv/bin/pip install -e /home/v-homatthew/tau2_ctxe

# Also install ctx_editor for shared abstractions (per
# docs/tau2_absorption_decision.md Option C).
/home/v-homatthew/tau2_ctxe/.venv/bin/pip install -e /home/v-homatthew/ctx_editor

# Smoke
/home/v-homatthew/tau2_ctxe/.venv/bin/python -c \
  "from tau2.agent.llm_agent import LLMAgent; print('tau2 ok')"
/home/v-homatthew/tau2_ctxe/.venv/bin/python -c \
  "from ctx_edit.agents import AssistantOmitAgent, ContextEditAgent, ContextRewriteAgent; print('ctx_edit ok')"
```

Acceptance: both smoke imports succeed without `audioop` errors.

### Phase 1 — Analyzer parity audit on the tau2 side (≤ 1 h)

This is the equivalent of `docs/analyzer_parity_finding.md` for the
tau2 fork. The setup is:

- `tau2_ctxe/ctx_edit/analyzer.py::analyze_conversation` is called
  by both `ContextEditAgent` (s2, `mode="s2"`) and `ContextRewriteAgent`
  (s3, `mode="s3"`).
- Q1 (task-spec extraction) uses the same `TASK_SPEC_PROMPT_V10`
  template for both modes. ✅ parity here.
- Q2 (compare-and-classify) uses **different templates**:
  `COMPARE_PROMPT_V10_S2` for s2, `COMPARE_PROMPT_V10_S3` for s3.
  ⚠ asymmetry — same class as the LiC bug.

The legitimate reason an asymmetry *might* be ok here: S2's Q2
output goes directly into the compacted context (assistant reads
it), while S3's Q2 feeds into Q3 (the rewriter LLM). Different
downstream consumers can justify different framing. But that needs
to be verified, not assumed.

**Action items**:

1. `diff -u` the two prompts. Are they functionally the same with
   only the framing differences a downstream consumer dictates? Or
   has Q2_S3 drifted in ways that make it a worse task-grounding
   signal (e.g., lossier on tool-call state, more interpretive)?
2. If the prompts diverge in problematic ways, propose a parity
   refactor analogous to R5's: have S3 use the S2 Q2 output and
   only invoke the rewriter (Q3) on top of it. Document as a
   separate doc (`docs/tau2_analyzer_parity_finding.md` if it's
   bad enough to warrant the same caveat-banner treatment R5 added
   to all LiC reports).
3. **Stop and check with the user before refactoring tau2's
   analyzer.** This plan as written assumes parity is fine and runs
   with the existing prompts; only refactor if the diff is damning.

Acceptance: a one-paragraph entry in
`docs/post_may18_tau2_followups.md` (created by this phase) saying
either "parity is acceptable, proceeding" or "parity needs fix,
deferring sweep".

### Phase 2 — Port R6 Rewrite-prompt winner to tau2 (≤ 1.5 h)

Once R6 has a clean winner (likely v8 or GEPA-optimized v7+):

1. Identify the prompt file in
   `src/ctx_editor/strategies/prompts/`. Read the R6 summary in
   `docs/reports/post_may18_r6_summary.md` (if written by then) for
   the chosen variant + accuracy delta over Baseline.
2. The tau2 fork's `CONTEXT_REWRITE_PROMPT` in
   `tau2_ctxe/ctx_edit/analyzer.py` is a *separate* string (paper-era,
   adapted for tool-call conversations). It will need a
   tau2-flavored port of the R6 winner — *not* a verbatim copy —
   because:
   - tau2's Q3 ingests `AnalysisResult.environment_state` which LiC
     doesn't have (CRM database + phone state).
   - tau2's downstream consumer is an agent that calls tools next
     turn; LiC's is a text-answer assistant.
3. Port heuristics, in order: keep R6's framing (no spec-derivation
   second-guessing, open-ended output mode if applicable), add the
   tau2-specific environment-state preamble, keep
   `CONTEXT_REWRITE_PROMPT`'s tool-list block at the end.

Acceptance: one new prompt-version constant in
`tau2_ctxe/ctx_edit/analyzer.py` (e.g., `CONTEXT_REWRITE_PROMPT_V11`)
+ a CLI flag in `run_parallel.py` so we can run both v10 (old) and
v11 (R6-aligned) side by side. Smoke test on 1 telecom_small task
with `--workers 1` and verify the briefing looks sensible.

### Phase 3 — Implement AugmentAgent (≤ 1 h)

Closest existing code in tau2 is the "no issues → inject strategic
hint" branch inside `ContextEditAgent.generate_next_message`
(`agents.py:340`-`377`). An Augment variant:

- Runs the same analyzer every turn after `min_turns` (the
  `_should_analyze` gate).
- Never compacts. Just *always* appends a structured summary of the
  analyzer output (`task_spec`, `valid_progress`,
  `corrective_direction`) to the most recent `UserMessage` before
  calling the LLM.
- Reuses `ContextEditAgentState` (analysis log + turn counter; no
  resets).

Suggested class:

```python
class AugmentAgent(HalfDuplexAgent[ContextEditAgentState]):
    """Analyzer fires every turn; output appended to last user message.

    Mirrors the LiC AppendAnalysisStrategy (AC3-Augment). Does not
    compact / reset; lower risk than S2 in agentic tool-call settings.
    """
    def generate_next_message(self, message, state):
        # ... append message, increment turn ...
        if isinstance(message, UserMessage) and self._should_analyze(state):
            result = analyze_conversation(..., mode="s2")  # reuse Q2_S2 framing
            state.analysis_log.append({...})
            # append `<analysis>...</analysis>` block to last user msg
        # send through assistant LLM ...
```

Acceptance: `AugmentAgent` registered in `run_parallel.py`
`--strategy` choices (e.g., `s1` to match LiC's AC3-Augment label).
Smoke test on 1 task. Inspect that the analyzer's output is visible
to the agent in the rendered messages.

### Phase 4 — Optional: always-on ResetAgent (≤ 1 h, low priority)

The paper reports the gated variant (`s2`). An always-on reset would
just be `ContextEditAgent` with the `if result.needs_edit:` branch
forced True. Worth implementing only if the gated and always-on
configurations diverge meaningfully on telecom_small — which we
don't have evidence for yet. Mark as a stretch task; skip unless
Phases 0–3 finish ahead of schedule.

### Phase 5 — Sweep (~2–3 h wall, depending on parallelism)

**Cells** (priority order, parallelize where possible):

| # | Model | Strategy | Tasks | Wall (est) |
|---|---|---|---|---|
| 1 | gpt-5-mini | s0 | 20 | ~25 min |
| 2 | gpt-5-mini | ao | 20 | ~25 min |
| 3 | gpt-5-mini | s2 (gated-reset, v10) | 20 | ~30 min |
| 4 | gpt-5-mini | s3 (rewrite, **v11** R6-ported) | 20 | ~30 min |
| 5 | gpt-5-mini | s1 (augment, new) | 20 | ~30 min |
| 6 | gpt-5.4 | s0 | 20 | ~30 min |
| 7 | gpt-5.4 | ao | 20 | ~30 min |
| 8 | gpt-5.4 | s2 | 20 | ~35 min |
| 9 | gpt-5.4 | s3 (v11) | 20 | ~35 min |
| 10 | gpt-5.4 | s1 | 20 | ~35 min |

10 cells. With `--workers 10` per cell and 2 cells in parallel,
~2.5 h wall total. Cost estimate: ~$10–20 in OAI calls for the
gpt-5.4 half (gpt-5-mini half is cheap, foundry side is unbilled).

**Launch order**:

1. gpt-5-mini cells first (sanity vs March-2026 paper numbers; if
   `s2`/`s3` numbers drift materially from the existing baseline,
   *stop* and investigate before burning gpt-5.4 budget).
2. gpt-5.4 cells second, parallelized 2 at a time.
3. Foundry models (Kimi, DeepSeek) only after R6 foundry workload
   completes — coordinate by checking `outputs/post_may18_r6_*`
   for an "all done" marker, or by talking to the other Claude.

### Phase 6 — Mega-table + docs (~30 min)

1. Extend `scripts/build_mega_table.py` with tau2 rows. tau2 cells
   have a different output layout (`tau2_ctxe/ctx_edit/outputs/...`)
   so the aggregator needs a new dir spec.
2. Write `docs/reports/post_may18_tau2_summary.md` with the cells,
   per-strategy accuracies, cost/time, takeaways. Apply caveat
   banners if the analyzer parity audit (Phase 1) revealed issues
   on the tau2 side.
3. Update `docs/index.md`'s topical + chronological sections.
4. Commit. Suggested message:
   `results: tau2 cross-model + cross-strategy (telecom_small)`

## Coordination with the parallel LiC Rewrite Claude

The other Claude is iterating on Rewrite for LiC (R6+). To avoid
stepping on each other:

- **Different working dirs**. They edit `/home/v-homatthew/ctx_editor`,
  I edit `/home/v-homatthew/tau2_ctxe/ctx_edit` + a handful of files
  under ctx_editor for shared abstractions only (e.g., aggregator,
  index, summary). Before editing any shared file I'll `git log -p
  <file>` to see if R6 just touched it.
- **Different Python env**. Phase 0's separate `.venv` ensures we
  don't fight over installed package versions.
- **Different model endpoints**. gpt-5.4 (Azure OAI) and gpt-5-mini
  (Azure OAI, dl-openai-3) are mostly orthogonal to the foundry
  endpoint where DeepSeek / Kimi LiC work is happening. Kimi /
  DeepSeek tau2 cells are explicitly deferred until R6 completes.
- **Reads**. I'll re-read the R6 summary doc right before launching
  Phase 5 to make sure no late-breaking R6 finding changes the
  prompt I'm porting in Phase 2.

## Trigger / preconditions for executing this plan

This plan executes when **all** of:

1. R6 / R7 has a stable LiC Rewrite variant documented as the
   recommended Rewrite configuration (i.e., a clean "Rewrite-vN beats
   Baseline by Xpp on LiC" claim is in the canonical resume doc).
2. Foundry endpoint load drops back to baseline — no concurrent
   foundry-routed LiC experiments running.
3. The user (or the other Claude) explicitly hands off, OR enough
   time has passed (≥ 24 h since the last R6 commit) that we can
   assume the LiC track is parked.

If those are satisfied, this doc + the existing
`tau2_ctxe/ctx_edit/run_parallel.py` are enough to execute end-to-end
without further design questions.

## Open questions (resolve before / during Phase 0)

1. **Which R6 Rewrite variant do we port?** Likely the GEPA-optimized
   winner if it materially beats v8/v9_no_conv; otherwise the
   stronger of v8 vs v9_no_conv. Final answer should be in
   `docs/reports/post_may18_r6_summary.md` (does not exist yet as of
   this writing). If two variants are close, port the simpler one.
2. **Do we re-run gpt-5-mini cells from scratch, or trust March-2026
   numbers?** Recommendation: re-run. The March-2026 cells were
   pre-analyzer-parity-discovery, and we want directly comparable
   numbers under the (potentially re-fixed) tau2 prompts.
3. **What N for confidence?** Single-seed N=1 across 20 tasks
   gives a directional read but no error bars. If the directional
   read is informative, plan a follow-up with seeds 42/43/44.
4. **Should AugmentAgent's analyzer output go into the user
   message or into a new system message?** LiC's
   `AppendAnalysisStrategy` puts it into a user-role message; tau2's
   tool-call rich format may handle that differently. Smoke test
   both; pick the one whose rendered conversation makes sense.

## Out of scope for this plan

- Last-turn replay infrastructure for tau2 — still deferred per
  `docs/notes/literature/tau2_replay_scoping.md`.
- Multi-seed error bars beyond the optional follow-up bullet.
- gpt-5.5 — Phase 2 of the AC3 batch deferred it on cost/throughput
  grounds; same argument holds here.
- Other tau2 domains (retail, airline). Telecom-small only.

## Estimated total wall time + cost

- Phase 0: ~15 min, no LLM calls
- Phase 1: ~45 min, no LLM calls (audit/diff work)
- Phase 2: ~1.5 h, ~5 LLM smoke calls (~$0.05)
- Phase 3: ~1 h, ~5 smoke calls
- Phase 4: ~1 h (skip if behind)
- Phase 5: ~2.5 h wall, ~$10–20 OAI cost (foundry unbilled)
- Phase 6: ~30 min, no LLM calls

**Total**: ~6.5 h wall (skipping Phase 4) / ~7.5 h (with Phase 4).
Cost: ~$10–20 in OAI calls. Fits a single overnight window.

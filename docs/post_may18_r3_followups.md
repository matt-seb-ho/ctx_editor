# Follow-ups from the R3 overnight batch (post 2026-05-20 R3)

Tracked items that should be addressed in the next session.

## Engineering / data integrity

- **Reset × bigcodebench × {gpt-5.4, Kimi-K2.6} content-filter
  blocker**: ALL 20 samples in each cell were filtered out with
  `jailbreak: detected` on the Reset analyzer's prompt. Same
  false-positive pattern as the AC3 batch — but the `s1` fallback
  prompt escalation wasn't wired up for this run. Fix: when Reset's
  v8 prompt trips Azure content filter, automatically fall back to
  `s1` (or `v13` per the original analyzer-prompt design doc). Cells
  to re-run after fix: 4 (gpt-5.4 + Kimi × Reset × bigcodebench).
- **Foundry rate-limit (429) cascade** when too many parallel cells
  share `mgalley-foundry2`. Tonight had 8+ concurrent cells each at
  max_concurrent=12, which saturated the 250k tokens/min cap and
  caused 30–49 of 50 samples per cell to be excluded as errors.
  The R3 throttled re-run at max_concurrent=4 × 4 parallel cells
  produced clean data. Bake a default cap into the launcher
  templates and/or add an automatic retry loop on 429.

## Experimental — mega table holes

- **Gated-Reset on gpt-5.4 + Kimi (LiC)**: would complete the Gated
  row of the mega table. Cheap last-turn replay; ~30 min total.
- **Gated-Reset on CollabLLM**: never tested anywhere. Phase 3a's
  rev.2 deferred this. Probably the right next step for the
  deployment-realism story.
- **CollabLLM × Rewrite (compaction) cross-model**: tonight we
  filled DeepSeek (math-hard 90%, bigcodebench 10%). gpt-5.4 + Kimi
  would complete the Rewrite row. Mild interest; expect similar
  pattern to LiC (Rewrite drags below Baseline/Reset).
- **CollabLLM multi-rep error bars**: tonight is N=1 across all R3
  cells. At least the headline cells should get N=3 once the gating
  + Rewrite questions resolve. ~90 min/model for the priority cells.
- **WildChat Gated-Reset (s2)** and **WildChat Rewrite (s3) error
  bars**: tonight is single seed. Multi-seed (3 seeds) would tighten
  the ±1.4pp / ±1.3pp envelopes from Phase 3b.
- **tau2 cross-model fresh-sim**: replay infrastructure deferred
  (~2 dev-days). Fresh-sim on gpt-5.4 + Kimi via the
  `tau2_ctxe/ctx_edit/` fork is feasible (~2h per model). See
  `docs/notes/literature/tau2_replay_scoping.md`.

## Rewrite analysis follow-ups

- **GEPA-based Rewrite prompt optimization** (Task 1.2c). Tonight
  hand-iterated v2→v3→v4 with progressively worse results. GEPA
  could search the prompt space more systematically with
  reflection-based gradient signal. Plan in
  `docs/notes/literature/gepa_notes.md`.
- **v3-style intervention with the SAME analyzer as Reset**.
  Currently Rewrite uses `compaction_analysis.txt` while Reset uses
  `ConversationAnalyzer` (`v8`). Forcing parity at the analyzer
  step would isolate "is rewrite's failure the rewriter or the
  upstream analyzer?". 27% of failures already attribute to
  analyzer_output, so this might recover a meaningful chunk.
- **Rewrite on WildChat = good, on LiC = bad** is now the most
  surprising paper-level finding. Worth a section explaining
  *why*: LiC's strict-format tasks (math `\boxed{}`, SQL syntax,
  function-call format) penalize the rewriter's drift; WildChat's
  open-ended conversational tasks reward its flexibility.

## Paper narrative items

- The **appropriate-intensity-by-task** framing from R2 is
  *partially* false. CollabLLM bigcodebench: Reset was 20% on
  DeepSeek (winner), but on gpt-5.4/Kimi AO leads (and Reset is
  filter-broken). So Reset isn't reliably the winner on hard tasks —
  it's the winner for *DeepSeek* on hard tasks, suggesting
  per-model interaction effects.
- **Rewrite negative-result paragraph** for the paper: hand-iterated
  v1→v2→v3→v4 prompts all underperform Baseline on LiC. The 1.1
  failure-mode analysis pinpoints LLM hallucination (63%) as the
  dominant cause and explains why prompt instructions can reduce
  but not suppress it.

## tau2 blocker (logged 2026-05-21)

**Cannot run tau2 in the current shared Python env (3.13.11).** The
`tau2-bench` upstream package requires Python `>=3.12,<3.14`, but
its `tau2.voice.synthesis.audio_effects.effects` module
unconditionally imports the stdlib `audioop` module which was
**removed in Python 3.13**. So a fresh `import tau2.agent.llm_agent`
fails with `ModuleNotFoundError: No module named 'audioop'`.

Options for next session:

1. **Set up a dedicated Python 3.12 venv for tau2** (e.g.,
   `uv venv --python=3.12 ~/tau2_ctxe/.venv && uv pip install -e .`)
   and run all tau2 commands inside it. Cleanest.
2. **Vendor an `audioop` shim** or monkey-patch the voice module to
   defer the import. Brittle.
3. **Drop the voice dependency** if our work doesn't need it.
   The `effects.py` is only imported transitively when the voice
   subsystem is touched; we never hit it directly. A small upstream
   patch to make the import lazy would fix this.

I did **not** modify the env tonight (the user denied `pip install
-e .`). All other R3 tau2 work — implementing Augment + always-on
Reset agents, launching cross-model — depends on resolving this
blocker first.

### Inventory of what's available + what's missing in `tau2_ctxe/ctx_edit/agents.py`

- **`LLMAgent`** (built-in): Baseline (s0).
- **`AssistantOmitAgent`**: AO.
- **`ContextEditAgent`** (s2): **already Gated-Reset** — it only
  compacts when `analyze_conversation()` returns `needs_edit=True`.
  In LiC terminology this is `context_edit_v2_gated`, not
  `context_edit_v2_no_gate`.
- **`ContextRewriteAgent`** (s3): Rewrite (extra LLM compaction call).
- **Missing**: an Augment variant that appends the analyzer's
  `task_spec / valid_progress / corrective_direction` to the most
  recent user message without ever compacting. Could be derived
  from the "no issues → inject strategic hint" branch in
  `ContextEditAgent.generate_next_message`.
- **Missing**: an always-on Reset variant (compact every turn
  regardless of `needs_edit`).

Both new agents are 30–60 min of code each but require the env
unblocked first.

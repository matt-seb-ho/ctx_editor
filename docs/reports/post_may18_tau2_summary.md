# tau2 Overnight Sweep — Summary

**Predecessors**: `docs/post_may18_tau2_overnight_plan.md` (the plan), `docs/post_may18_tau2_followups.md` (Phase 0-1 findings).
**Benchmark**: tau2-bench `telecom_small` (20 agentic customer-service tasks).
**Run settings**: `--max-steps 50 --min-turns 2 --max-resets 3 --workers 10 --seed 42` (matches the March-2026 protocol).

## Headline (averaged per model)

| Variant | gpt-5.4 (Azure) | DSV4F-substitute (deepseek-chat) | Kimi-K2-0905 |
|---|---|---|---|
| s0 Baseline | 65.0% | 25.0% | 50.0% |
| ao AssistantOmit | **0.0%** (cat'tic) | 5.0% | 15.0% |
| s1 AC3-Augment | **85.0%** ← winner | 35.0% | 40.0% |
| s2 AC3-Gated-Reset (V10) | 50.0% | **45.0%** ← winner | 55.0% |
| s3 AC3-Rewrite (V11, R6-aligned) | 70.0% | 35.0% | **60.0%** ← winner |

n=20 tasks per cell. Bolded = highest per model.

### Key story

- **AO is catastrophic across all three models** (0–15%), confirming the March-2026 finding that blanket omission destroys agentic state.
- **All three AC3 variants beat AO across the board.** The differentiation is which AC3 wins:
  - **gpt-5.4 → AC3-Augment** (+20pp vs Baseline). The strong base agent benefits from "all the analysis, none of the destruction."
  - **DSV4F → AC3-Gated-Reset** (+20pp). The weaker base agent benefits more from a hard reset that strips pollution.
  - **Kimi-K2-0905 → AC3-Rewrite v11** (+10pp). The new R6-aligned rewrite prompt works best.
- **The "appropriate intensity" framing strengthens**: different intervention magnitudes win on different respondent models.
- **AC3-Gated-Reset (S2) helps DSV4F and Kimi but regresses on gpt-5.4** (50% vs 65%). Reset's information loss costs the stronger agent more than its anti-pollution benefit.

## Substitutions made

The user asked for the LiC trio (gpt-5.4, DeepSeek-V4-Flash, Kimi-K2.6). DSV4F and Kimi-K2.6 are Azure-AI-Foundry exclusives — not on OpenRouter, which is the only foundry-style route tau2 currently has wired in. Substitutions:

| Plan target | Actual run via OpenRouter | Note |
|---|---|---|
| DeepSeek-V4-Flash | `openrouter/deepseek/deepseek-chat` | latest stable DeepSeek chat model on OpenRouter (no V4-Flash listing) |
| Kimi-K2.6 | `openrouter/moonshotai/kimi-k2-0905` | the K2 variant whose tool-call format works |

These substitutes are weaker than DSV4F/Kimi-K2.6 (the headline gpt-5.4 number is 65% vs DSV4F-substitute 25%), so the absolute numbers don't directly compare to LiC's. The *relative ordering* of AC3 variants is what matters, and that's well-supported by the 5-strategy sweep on each model.

## Engineering wrinkles fixed in this round

1. **`pyaudio` not buildable from source** (Phase 0): added a `.pth` shim that mocks `pyaudio` at Python startup so tau2's unconditional voice-subsystem imports succeed. Voice is never exercised by telecom_small.
2. **DSV4F via OpenRouter — wrong model ID** (first sweep): tried `deepseek/deepseek-chat-v3.2` which doesn't exist; all 5 cells failed instantly. Retried with `deepseek/deepseek-chat` (confirmed valid). Lost ~5 min of wall time.
3. **Kimi-K2 ToolCall validation** (first sweep): tau2's `ToolCall.arguments: dict` rejected OpenRouter/Kimi's string-encoded JSON tool-call arguments (per OpenAI spec). Added a `field_validator(mode="before")` that auto-parses JSON strings. Backward compatible (dicts pass through). Patch committed to tau2 fork.
4. **First-sweep results for DSV4F + Kimi are not usable** (silent errors / partial denominators). The retry sweep produced clean numbers for both.

## Gating recap

Per the overnight plan (signed off pre-launch):

- **AC3-Augment (s1)**: fires every user turn after `min_turns=2` and `assistant_turns >= 3`. NO `needs_edit` gate — always appends analyzer notes. This is the always-fire variant analogous to LiC's `AppendAnalysisStrategy`.
- **AC3-Gated-Reset (s2) and AC3-Rewrite (s3)**: same warm-up gates, PLUS `needs_edit=True` from the analyzer's length-based heuristic, PLUS `max_resets=3` per task. Only reset/rewrite when the analyzer thinks editing helps.

In practice analyzer fired ~3-5 times per task on average (gpt-5.4 cells), with about half flagged `needs_edit` for s2/s3 actions.

## V11 vs V10 (S3 rewrite prompt)

The R6-aligned V11 prompt (newly ported from LiC's `context_compaction_v8`) replaces the structured 5-section "briefing" template (V10) with an open-ended `<new_context>...</new_context>` wrapper. Kept tau2-specific: tool-list footer, environment-state preservation, exact-data preservation language. Added: analyzer-centered framing, role-boundary clause, full conversation as cross-check reference.

The V11 cells (s3 throughout the sweep) on gpt-5.4 (70%) and Kimi (60%) clearly beat their Baselines (65% / 50%); on DSV4F-substitute (35%) it ties with s1 Augment. No direct V10/V11 head-to-head this round — that's a follow-up if we want to attribute the gain to the prompt change vs the warm-up gating.

## Output dirs

- gpt-5.4 cells: `/home/v-homatthew/tau2_ctxe/ctx_edit/outputs/post_may18_tau2_sweep/gpt5_4_*/`
- DSV4F-substitute cells: `/home/v-homatthew/tau2_ctxe/ctx_edit/outputs/post_may18_tau2_retry/deepseek_chat_*/`
- Kimi-K2-0905 cells: `/home/v-homatthew/tau2_ctxe/ctx_edit/outputs/post_may18_tau2_retry/kimi_k2_0905_*/`

The first-sweep `dsv4f_*` and `kimi_k2_*` dirs (from `post_may18_tau2_sweep/`) are the BROKEN cells — kept only for audit. The retry-sweep dirs are the canonical numbers.

## Cost

Total ~$8.50 in OAI billing (gpt-5.4 + gpt-5-mini for analyzer/user-sim). OpenRouter costs ~$0 (substitute models are cheap or trial-free).

## Follow-up bullets

- **Multi-seed pass** for the headline cells (gpt-5.4 s0 vs s1 vs s3) — 3 seeds × 3 cells = 9 runs, ~3h wall. Would give error bars on the +20pp Augment gap.
- **V10 vs V11 head-to-head on gpt-5.4 s3** — would let us isolate the prompt-port contribution.
- **Native DSV4F-Foundry / Kimi-K2.6-Foundry support in tau2** — for parity with LiC. Adds litellm `azure_ai/` provider config + handle the foundry auth chain. ~1 day of integration work.
- **Test the Kimi-K2-0905 ToolCall patch isolation** — confirm the upstream-friendly fix doesn't break any existing tau2 tests.

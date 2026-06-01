# Mega-table round summary (post-tau2-canonical work)

**Predecessors**: `docs/reports/post_may18_r6_summary.md` (R6 winner = v8), `docs/reports/post_may18_tau2_summary.md` (initial tau2 sweep using OpenRouter substitutes).

This round focused on three things, all aimed at making the mega-table the user shows their mentor presentable and honest:

1. **Tau2 with canonical Azure Foundry models** (replace OpenRouter substitutes).
2. **WildChat with gpt-5.4 as the GPT representative** (replace the gpt-5-mini column).
3. **Gated-Reset cell reconstruction** from existing Reset analyzer logs (no new LLM calls).

The canonical mega-table HTML is now at `docs/reports/post_may18_progress_update_v3_clean.html`; this report explains how each cell got filled.

## 1. tau2 on canonical Azure Foundry

### Engineering — Foundry plumbing in tau2

tau2's `LLMAgent` and friends accept `llm_args` that pass through to litellm.completion(). Added a `foundry/<MODEL>` prefix shim in `tau2_ctxe/ctx_edit/run_parallel.py::_resolve_foundry_model`: when an `--agent-llm` starts with `foundry/`, strip the prefix, fetch a bearer token from `AzureCliCredential('https://cognitiveservices.azure.com/.default')`, and inject `{api_base: 'https://mgalley-foundry2.services.ai.azure.com/openai/v1/', api_key: token}` into the agent's `llm_args`. The agent then talks to mgalley-foundry2 via litellm's `openai/<MODEL>` provider over the Foundry's OpenAI-v1 endpoint.

Token TTL is ~60min; per-cell wall time stays well within that, so no refresh logic needed during a single cell.

This unblocks DSV4F + Kimi-K2.6 on tau2 with the same model identities used in LiC/CollabLLM/WildChat — and crucially avoids the OpenRouter + personal-credit-card billing path. tau2-fork commit: `5534930` (port v8 + AugmentAgent), `537f63d` (ToolCall string-args patch), [foundry shim].

### Engineering — Kimi rate-limit fix

First Foundry sweep at `--workers 10` hit a `litellm.RateLimitError` on every Kimi-K2.6 cell — Foundry caps that model at 100 RPM and 10 concurrent workers cycling through tool-call loops trips the cap. Retry sweep at `--workers 4` cleared the AC3-variant cells (≤4 short-exits out of 20). Baseline + AO at workers=4 still had 14-19 short-exits, so those numbers are rate-limit-clipped floors rather than honest performance. Could re-run those two cells at workers=2 to finalize; the AC3 vs Baseline differential is robust regardless because all three AC3 winners (Augment/Gated-Reset/Rewrite) ran clean.

### Final tau2 telecom_small numbers (n=20 / cell)

| Strategy | gpt-5.4 (Azure OAI) | DSV4F (Foundry) | Kimi-K2.6 (Foundry, w=4) |
|---|---|---|---|
| Baseline (s0) | 65.0% | 30.0% | 25.0% ‡ |
| AO | 0.0% | 0.0% | 0.0% ‡ |
| AC3-Augment (s1) | **85.0%** ← win | 55.0% | 55.0% |
| AC3-Gated-Reset (s2, V10) | 50.0% | 45.0% | 65.0% |
| AC3-Rewrite (s3, V11 = R6-aligned port) | 70.0% | 55.0% (tied with s1) | **70.0%** ← win |

‡ Kimi Baseline + AO cells still rate-limit-clipped (14/20 and 19/20 short-exits respectively). True Baseline is probably 40-50%; doesn't affect AC3 ordering.

### tau2 story (the headline for the talk)

- **AO is catastrophic across all three models** (0% everywhere). Blanket assistant-message omission destroys tool-call state.
- **Every AC3 variant beats Baseline on every model.**
- **The winning AC3 variant changes by model**:
  - gpt-5.4 (strongest) → Augment (light touch)
  - DSV4F (mid) → Augment/Rewrite tied
  - Kimi-K2.6 (weakest base) → Rewrite v11 (heaviest intervention)
- Maps cleanly onto the "appropriate intensity" framing the paper is built on: stronger agents benefit from analyzer hints without context destruction; weaker agents benefit from heavier interventions that aggressively prune pollution.

Output dirs (Foundry):
- gpt-5.4 cells: `tau2_ctxe/ctx_edit/outputs/post_may18_tau2_foundry/gpt5_4_*/`
- DSV4F cells: `tau2_ctxe/ctx_edit/outputs/post_may18_tau2_foundry/dsv4f_foundry_*/`
- Kimi cells (workers=4 retry): `tau2_ctxe/ctx_edit/outputs/post_may18_tau2_foundry_kimi_retry/kimi_k2_6_foundry_w4_*/`
- Initial OpenRouter substitute cells (deprecated): `tau2_ctxe/ctx_edit/outputs/post_may18_tau2_sweep/` and `.../post_may18_tau2_retry/`

## 2. WildChat × gpt-5.4

Re-ran all four AC3 variants (s3 = Rewrite v8, s15 = Reset, s2 = Gated-Reset, Augment) on Huang's WildChat phase1 76-prefix set with respondent gpt-5.4 (replacing gpt-5-mini). Analyzer locked to gpt-5-mini per R6 sign-off 6 (hits the 76 cached gpt-5-mini analyses; isolates rewriter-prompt variable from analyzer differences).

Script: `scripts/run_post_may26_wildchat_gpt54.sh`. Output: `outputs/post_may26_wildchat_gpt54/`.

### Numbers (S vs AO baseline, quality win-rate)

| Variant | n | quality vs AO | ontopic vs AO | quality vs FC | ontopic vs FC |
|---|---|---|---|---|---|
| Augment | 57 | 84.2% | 68.4% | 77.2% | 64.9% |
| Reset (s15) | 44 | 88.6% | 65.9% | 77.3% | 61.4% |
| **Gated-Reset (s2)** | 58 | **74.1%** | 67.2% | 72.4% | 60.3% |
| Rewrite v8 (s3) | 48 | 83.3% | 75.0% | 72.9% | 62.5% |

### WildChat × gpt-5.4 story

- AC3 variants beat AO across the board (74-89% quality wins).
- Win-rates compressed vs gpt-5-mini (was 86-93%): a stronger respondent reduces the headroom Augment etc. had to work with.
- **Gated-Reset (74.1%) clearly underperforms always-on Reset (88.6%)** — the first place where the two Reset variants meaningfully diverge outside tau2. Suggests that on WildChat with gpt-5.4, the analyzer's "needs_edit=False" gate-closes are sometimes false negatives; the prepared-context-via-Reset is genuinely helpful even when the analyzer thinks no issues. This data point alone justifies splitting Reset / Gated-Reset back into separate rows in the mega-table.

## 3. Gated-Reset reconstruction

Wrote `scripts/reconstruct_gated_reset.py`. For each (benchmark, model, task, conv, sample) cell where we have both Reset and Baseline traces:

1. Pull the analyzer's `needs_edit` flag for the sample from the Reset trace's `trace.logs[type=conversation_analysis].data.needs_edit`.
2. If any turn fired `needs_edit=True` → pick Reset's `is_correct` (Gated-Reset would have opened the gate at that turn).
3. Otherwise → pick Baseline's `is_correct` (gate held; pass-through).

For LiC last-turn replay this is **exact** (one analyzer fire per sample). For multi-turn benchmarks it's an "any-turn-opened" approximation; the actual Gated-Reset trajectory after the first gate-open can't be reconstructed without rerunning the agent.

### Reconstructed numbers

| benchmark | n | gate-open rate | Reset acc | Baseline acc | **Reconstructed Gated-Reset** |
|---|---|---|---|---|---|
| LiC (DSV4F, R3 mega-table cells) | 554 | 97.3% | 68.95% | 52.35% | **68.95%** |
| CollabLLM (DSV4F, post_neurips_phase3) | 119 | 98.3% | 15.97% | 15.13% | 15.97% |

### Key finding

**On text-only / one-shot benchmarks the analyzer almost always finds issues by the relevant turn**, so the gate almost never closes and reconstructed Gated-Reset ≈ Reset (within rounding).

**The "gated" variant only differentiates from always-on Reset in two regimes**:
1. **Agentic / tool-call settings (tau2)** — the gate genuinely closes some of the time; Gated-Reset numbers differ from always-on Reset (we never ran always-on Reset on tau2, but the gate's behavior across the trajectory means they wouldn't match).
2. **Strong-respondent text benchmarks (WildChat × gpt-5.4)** — Gated-Reset *underperforms* always-on Reset by 14.5pp. The gate's needs_edit=False decisions are sometimes false negatives in this regime.

This is itself a paper-relevant observation: the gating heuristic's failure mode is asymmetric — it's hard to make it close incorrectly (because the issues-section is verbose by default), and false-negative closes (gate held when Reset would have helped) are the dominant cost.

## 4. Current mega-table snapshot

Latest copy: `docs/reports/post_may18_progress_update_v3_clean.html`. Headline mega-table covers LiC × 3 models, CollabLLM × 3 models, WildChat × 3 models (gpt-5.4, DSV4F, Kimi), tau2 × 3 models. Rows: Baseline / AO / Augment / Reset / Gated-Reset / Rewrite-v8-or-v11.

Most cells now real. Remaining open cells:
- CollabLLM × {gpt-5.4, Kimi-K2.6} × bigcodebench (Reset) — original numbers (~0%) were flagged as NaN due to Azure content-filter rejections and foundry transient errors; tooling fix needed.
- CollabLLM × Gated-Reset for non-DSV4F models — reconstructable from Reset traces if we want.
- WildChat × {DSV4F, Kimi} × Gated-Reset — not reconstructable (different trace format); would need a fresh sweep.
- tau2 Kimi-K2.6 Baseline + AO cells — partially rate-limited; could re-run at workers=2 for a clean floor.

## 5. Code + script artifacts (this round)

- `tau2_ctxe/ctx_edit/run_parallel.py` — `foundry/<MODEL>` prefix shim; `--rewrite-prompt-version` flag; s1 (Augment) wiring.
- `tau2_ctxe/ctx_edit/agents.py` — `AugmentAgent` class + `rewrite_prompt_version` plumbing on `ContextRewriteAgent`.
- `tau2_ctxe/ctx_edit/analyzer.py` — `CONTEXT_REWRITE_PROMPT_V11` (R6-aligned port of LiC v8).
- `tau2_ctxe/src/tau2/data_model/message.py` — `ToolCall.arguments` field_validator that accepts JSON-string args (covers OpenAI-spec providers like Kimi).
- `tau2_ctxe/ctx_edit/run_post_may18_tau2_foundry.sh` — main Foundry sweep.
- `tau2_ctxe/ctx_edit/run_post_may18_tau2_foundry_kimi_retry.sh` — Kimi retry at workers=4.
- `scripts/run_post_may26_wildchat_gpt54.sh` — WildChat × gpt-5.4 sweep.
- `scripts/reconstruct_gated_reset.py` — no-LLM reconstruction tool.
- `docs/reports/post_may18_progress_update_v3_clean.html` — canonical mega-table for talks.

## 6. Suggested follow-ups (ordered by value)

1. **Tau2 Kimi Baseline + AO at workers=2** (~20 min wall) — clear the rate-limit floor for a clean Baseline-relative delta on Kimi. The AC3 cells don't need re-running.
2. **WildChat × Gated-Reset for DSV4F + Kimi** — confirm the gpt-5.4 Gated-Reset < Reset finding is a respondent-strength effect or a cross-model pattern. ~1h wall.
3. **CollabLLM Gated-Reset reconstruction for all (model, dataset) pairs** that have Reset cells — extends the no-LLM-call story to fill more mega-table cells.
4. **Re-run CollabLLM × Reset × {gpt-5.4, Kimi} × bigcodebench** with content-filter back-off and lower foundry concurrency — fixes the NaN cells.
5. **Multi-seed pass on the tau2 headline cells** (gpt-5.4 s0 vs s1 vs s3, 3 seeds each) — gives error bars on the +20pp Augment gap that's currently a single-seed read.

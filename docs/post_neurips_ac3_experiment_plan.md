# Post-NeurIPS AC3 Experiment Plan (rev. 2)

**Date**: 2026-05-16
**Status**: revised after first round of feedback (see "Changes from rev.1" at the bottom). Awaiting approval to launch.

## Pre-deliberation context (the questions the user raised)

Re-statement of what I checked in the code:

- **Current default analyzer prompt**: `DEFAULT_ANALYZER_VERSION = "v8"`
  (`src/ctx_editor/strategies/analyzer_prompts.py:143`).
- **Paper prompt correspondence** (`docs/paper_experiments_provenance.md`):
  LiC = `v8`, CollabLLM = `s1`, Huang/WildChat = `v8` (Reset/Rewrite) + `v11` (Gated-Reset), τ² = `v10`.
- **Cost reporting**: pricing comes from `src/ctx_editor/models/openai_pricing.py`. **gpt-5.4, gpt-5.5, and all Foundry-hosted models are not in that table**, so they report `$0`. Token counts (`usage_stats`) are recorded regardless, so any model can be cost-backfilled by editing the pricing table.
- **Cached input**: `openai_model.py` already extracts `usage.prompt_tokens_details.cached_tokens` from Azure responses and `_calculate_cost` applies a `cached_input` rate when present. So filling in cached-input pricing actually matters for long-prefix replay (every variant cell re-uses the same prefix; the second variant on a prefix should be mostly cached server-side).
- **Content filter risk**: `v8` analyzer tripped Azure's `jailbreak` filter at 60-70% on gpt-5-mini through Azure OAI in May 2026 (`docs/archive/v12_attempt/azure_jailbreak_filter_triggers.md`). `s1` was the May workaround — content-filter-safe but with weaker numbers (it never made the paper, was a defensive fallback). **Foundry is still part of Azure**, so non-OAI Foundry models *might* still trip the filter; we don't have data either way yet.

## Decision points, revised

### 1. Prompt strategy — use `v8` across all conversation benchmarks

User confirmed in rev.1 feedback: "v8 prompts for all conversational benchmark experiments... I think this makes sense."

**Decision**: `v8` is the default for LiC (Phase 1+2) AND for CollabLLM / WildChat / Huang in any cross-benchmark consistency study (Phase 4 if we get there). `s1` is held in reserve as a **content-filter fallback** only; we expect to NOT use it for headline numbers.

- For LiC Phase 1+2 this matches the published paper directly (Table 1(a) used `v8`).
- For CollabLLM the headline paper row used `s1` because `v8` tripped the filter then. If `v8` works for us now (different models, different prompts in the analyzer's input from rev'd `v8` text), we report `v8` and treat the original `s1` cell as historical.
- For Huang the paper used `v8` for Reset/Rewrite and `v11` for Gated-Reset — we'll use `v8` everywhere here and keep `v11` documented as a comparison if we revisit gating-prompt design.

If Phase-2 Azure OAI calls (gpt-5.4 / gpt-5.5 analyzer paths) trip the filter > 10% on any cell, we fall back to `s1` for THAT cell only and log the trip rate alongside the score.

### 2. Single-model exploration → scale-up — DeepSeek-V4-Flash

Unchanged from rev.1. Phase 1 uses DeepSeek-V4-Flash (cheapest, fastest, no Azure-OAI content filter in the path). Phase 2 promotes Augment unconditionally + the better of Reset/Rewrite (with the 3pp tiebreak going to Reset).

### 3. Gating — promoted to a first-class phase

User feedback: "in setting where we are not just replaying the last turn, I think we want to use the gated mode... Please make sure to consider gating properly (and plan experiments around this piece because I genuinely think it's important for realistic deployment)."

This is the right call. Phase 1+2 are last-turn replay, where gating collapses ("we always intervene on the final turn or we don't"). The deployment-realistic question — "should we intervene every turn, or selectively?" — only surfaces in **multi-turn fresh simulation**, which we haven't done since the paper batch.

#### Phase 3 — Multi-turn gating study

Run fresh multi-turn LiC simulations (no replay) with the winning AC3 variant from Phase 1, comparing **gated vs ungated** behavior:

- **Model**: DeepSeek-V4-Flash (same as Phase 1, for fastest iteration). Worth re-running on one slower model (e.g. gpt-5.4) once we trust the design.
- **Tasks**: math + database. These had the largest sharded-vs-STQ gap, so gating decisions are most likely to matter. (Code + actions are saturated either at the low or high end and would give weaker signal.)
- **Strategies**:
  - **AC3-Reset (always-on)**: analyzer runs every turn, edits every turn. `min_turns=1`, `max_resets=1000` (effectively unbounded).
  - **AC3-Gated-Reset**: analyzer runs every turn, gate decides whether to edit. `min_turns=3, max_resets=3` (the paper's setting).
  - **Baseline + AO** as references.
- **Sample size**: full 50 problems per task, N=3 fresh sims each (the paper's N=3 setting). The 3 sims here are *sampling* reps on the same problem — no shared prefix, because each fresh sim creates its own conversation. This is consistent with the variance decomposition the prefix-decision doc outlines (Phase 1+2 measure cross-prefix variance; Phase 3 measures cross-sampling-rep variance).
- **What we measure**:
  - Final accuracy.
  - **Edit rate** — fraction of turns where the gate fired. Critical context-dependent metric.
  - **Cost per conversation** — gated should be cheaper if it's edit-rate <100%.
  - **Latency per conversation** — gated should also be faster.
- **Decision rule**: gated wins if accuracy is within −2pp of always-on AND edit rate is ≤ 50%. Otherwise always-on is the recommended deployment. We report both numbers either way.

Multi-turn fresh sims are slower per problem than replay (we re-do the whole conversation). Estimated wall time for Phase 3 on DeepSeek: 50 problems × 3 reps × 2 strategies × 2 tasks × ~2 min/sim = ~10-12 hours. Run overnight as a separate batch after Phase 1+2.

Phase 1 / Phase 2 do NOT vary gating — they treat the single-turn-replay scenario where it's a no-op.

### 4. Content filter mitigation, deeper

User flagged Foundry-being-part-of-Azure ambiguity. Concrete plan:

- **Phase 1 on Foundry DeepSeek**: monitor `content_filter_errors.jsonl` (the log already exists). Trip rate of zero is expected but not assumed.
- **Phase 2 cells on gpt-5.4 / gpt-5.5 OAI endpoints**: same monitoring. If trip rate on any cell exceeds 5% of analyzer calls, fall back to `s1` analyzer for that cell.
- **`s1` reminder**: looking at `src/ctx_editor/strategies/prompts/s1_analysis.txt`, `s1` is a single-query, header-format prompt with no XML wrappers and no nested-instruction patterns. It's literally the workaround for the May 2026 Azure CF crisis — your recollection is right; numbers were marginally weaker than `v8` on the CollabLLM cells. Acceptable fallback for cells that wouldn't run otherwise.
- **What we will NOT do**: redesign the analyzer prompt mid-flight just to dodge the filter. If `s1` doesn't work either, we document the cell as `partial coverage (CF skips: N)` and move on — keeping prompt design changes for a future targeted pass rather than poisoning the data pool.

### 5. Analysis reuse + registry

User feedback: "if we're testing the same model and are only changing the intervention between (augment/reset/rewrite) then we can reuse the same analysis and save the LLM query cost… let's make sure that in addition to being able to reuse conversation prefixes (from replaying), we can also reuse analysis outputs."

**This is the most consequential infra change in the rev.2 plan.** Today the analyzer is called fresh inside each strategy invocation. Across Phase-1 cells `{augment, reset, rewrite}` × same `(prefix, analyzer model)` we are paying for the same analyzer query 3 times — and worse, the three "shared" cells get *different* analyzer outputs because the analyzer call is non-deterministic, which adds noise to the variant comparison.

#### Design

A two-layer cache:

1. **Cache backend** (`src/ctx_editor/strategies/analysis_cache.py`): content-addressable filesystem cache.
   - Key inputs: hash of the trace's message list (system + user + assistant content), analyzer model name, prompt version, plus the call-time knobs (`spec_only`, `memory_target_query`, `enforce_compliance`, presence/absence of memory).
   - Cache key = `sha256(json_dumps_canonical(key_inputs))`.
   - Storage: `outputs/analysis_cache/{key[:2]}/{key}.json` (one shard byte to keep dir sizes reasonable).
   - Each cache file holds `{"key_inputs": {...}, "result": {...AnalysisResult fields...}, "raw_query_outputs": {...}, "created_at": "...", "experiment_origin": "<exp_name>"}`.

2. **Registry** (`outputs/analysis_cache/registry.json`): an index file with one line per cache entry. Append-only. Lets us:
   - Quickly see how many cached analyses exist per (analyzer_model, prompt_version).
   - Find the original experiment that produced each (for provenance).
   - Sanity-check "would my upcoming run hit the cache?" before launch.

A `scripts/inspect_analysis_cache.py` tool prints summary stats (count by analyzer_model × prompt_version, age distribution) and supports `--invalidate-by-prompt-version v8 --before 2026-05-01` to bulk-evict stale entries.

#### Integration

`ConversationAnalyzer.analyze(...)` gets a `cache` param:

```python
async def analyze(self, trace, model_client, memory=None, *, cache: Optional[AnalysisCache] = None, ...):
    if cache is not None:
        hit = cache.lookup(...)
        if hit is not None:
            return hit
    result = await self._analyze_impl(...)
    if cache is not None:
        cache.store(..., result, experiment_origin=...)
    return result
```

The strategies (`AppendAnalysis`, `AC3Reset`, `AC3Rewrite`) accept an `analysis_cache` constructor arg (defaulting to `None`). The Hydra runner instantiates one cache at the top of the experiment and threads it through.

A CLI knob `experiment.analysis_cache=outputs/analysis_cache` (or `=null`) controls whether to read/write. Set to a real path → reuse + extend. Set to null → recompute every time. The Phase-1 launcher uses the same cache dir across all 5 strategies, so:

- The first variant that runs on each (prefix, analyzer-model, prompt-version) populates the cache.
- The subsequent variants find the same key and skip the analyzer call entirely.
- Total analyzer-call savings: roughly **2/3** of analyzer queries in Phase 1 (5 strategies, but 2 — Baseline, AO — don't analyze; among the 3 that do, only 1 actually runs, the other 2 hit cache).

#### What invalidates a cached analysis

Cache is keyed on the inputs; **any change to the prefix or the analyzer prompt invalidates it automatically**. Things that do NOT change the key (so they DON'T trigger re-compute):

- The downstream strategy (cache is shared across Augment/Reset/Rewrite).
- The assistant model (we're caching analyses, not last-turn outputs).
- Sampling reps (cache is deterministic by design — that's the point).

Things that DO trigger re-compute:

- Switching analyzer model (e.g. Phase 2 with gpt-5.4 as analyzer).
- Switching `prompt_version` (`v8` → `s1` fallback).
- A user edit to the prefix conversation.
- A user `--invalidate ...` via the inspect script.

#### Registry sketch

```json
{
  "entries": [
    {
      "key": "a4f9...3b2",
      "analyzer_model": "DeepSeek-V4-Flash",
      "prompt_version": "v8",
      "task": "math_v2",
      "sample_id": "sharded-GSM8K/1011",
      "prefix_source": "data/valid_prefixes_htn50_52/deepseek_v4_flash_foundry/math_v2/conv0/sharded-GSM8K_1011.json",
      "spec_only": false,
      "created_at": "2026-05-17T01:14:33-07:00",
      "experiment_origin": "phase1_append_analysis_deepseek_math_v2_conv0_<ts>",
      "file": "outputs/analysis_cache/a4/a4f9...3b2.json"
    },
    ...
  ]
}
```

Future work the registry enables:

- Cross-cell consistency check ("did Augment and Reset really see the same analysis?").
- Cheap re-aggregation when a new variant is introduced (no analyzer cost if cache hits).
- Audit trail for the paper appendix (Did we run analyzer N times or 3 times? Registry knows.).

## Phase summary (rev.2)

| Phase | What | Model(s) | Strategies | Mode | Est. wall time | Notes |
|---|---|---|---|---|---|---|
| **1** | Variant exploration | DeepSeek-V4-Flash | S0, AO, Augment, Reset, Rewrite | Last-turn replay (3 prefixes/problem) | ~1 h | Analysis cache populates here. |
| **2** | Scale-up | gpt-5.4, Kimi-K2.6, gpt-5.5 | S0, AO, Augment, + best of Reset/Rewrite | Last-turn replay | ~5-6 h | Each model is a fresh analyzer-model cache namespace. |
| **3** | Gating study | DeepSeek-V4-Flash (+ gpt-5.4 if time) | Winning AC3 variant ± gating, S0, AO | Multi-turn fresh sims | ~10-12 h overnight | Measures edit rate + accuracy + cost-per-conversation. |
| **4** (optional) | Cross-benchmark consistency | One model | Winning AC3 variant with v8 prompt | LiC, CollabLLM, WildChat | TBD per benchmark | Tests "is the LiC prompt portable?" |

Phase 1 alone is overnight-safe and self-contained. Phase 2 fires after Phase 1's aggregator picks the winner. Phase 3 fires after Phase 2.

## Phase 1 cell math (unchanged from rev.1)

- 4 tasks × 5 strategies (S0, AO, Augment, Reset, Rewrite) × 3 prefixes (conv0/1/2) = 60 invocations.
- Each invocation: last-turn replay on ~50 problems (≤44 for code), wall time 30-90s on DeepSeek.
- Analyzer calls saved by cache: ~2/3 of analyzer queries in the three AC3 cells.

## Phase 2 cell math (unchanged from rev.1)

- 3 models × 4 strategies (S0, AO, Augment, + 1 winner from Reset/Rewrite) × 4 tasks × 3 prefixes = 144 invocations.
- gpt-5.4 dominates cost (~$0.85/run, ~$50 total).
- Kimi + gpt-5.5 dominate wall time (Kimi 100 RPM, gpt-5.5 reasoning).
- Cache hits for Augment + winning variant on the same prefix.

## Phase 3 cell math (new)

- 1 model × 4 strategies (S0, AO, Reset always-on, Reset gated — substituting the Phase-1 winner for "Reset" if it's Rewrite) × 2 tasks × 50 problems × 3 fresh sampling reps.
- = 1200 multi-turn fresh sims if every cell goes the full 50; smaller if we trim.
- Wall time on DeepSeek: ~2 min per fresh sim × 1200 ≈ 40 hours of single-process work, but parallelized at mc=20 → ~2-3 hours per task per condition. So ~10-12 h overnight.
- A second-model pass (gpt-5.4) on Phase 3 is desirable if time permits — would roughly double overnight.

## Ready-to-launch checklist (rev.2)

Engineering deliverables before Phase 1 kicks off:

- [ ] **Pricing file** `src/ctx_editor/models/foundry_pricing.yaml` — already scaffolded, awaits user-filled prices. Token counts log regardless; cost numbers will fill in retroactively as soon as the file is populated. (DONE — file scaffolded; user to fill in prices.)
- [ ] **Cost-merge wiring** `src/ctx_editor/models/base.py` — already merges the foundry pricing on top of the OpenAI table. (DONE.)
- [ ] **Analysis cache backend** `src/ctx_editor/strategies/analysis_cache.py` — new file. Synchronous JSON write/read on the filesystem, content-addressed. Lightweight; no DB.
- [ ] **Registry helper** `scripts/inspect_analysis_cache.py` — list/summarize/invalidate.
- [ ] **ConversationAnalyzer integration** — add optional `cache=` kwarg; thread through strategies.
- [ ] **Hydra knob** `experiment.analysis_cache=...` — defaults to a session-shared path under `outputs/analysis_cache/`.
- [ ] **Phase 1 launcher** `scripts/run_phase1_ac3_deepseek.sh` — 5 strategies × 4 tasks × 3 convs; uses the cache.
- [ ] **`context_edit_v2_no_gate.yaml` experiment config** for the always-on Reset variant (already explained in rev.1).
- [ ] **`ac3_rewrite_lic.yaml` experiment config** adapting `collabllm_compaction.yaml` for LiC tasks.
- [ ] **One-cell smoke test** end-to-end with cache enabled — confirm cache hit happens on second variant.

After Phase 1:

- [ ] **Phase 2 launcher** `scripts/run_phase2_ac3_other_models.sh` (depends on Phase 1 winner).

After Phase 2:

- [ ] **Phase 3 launcher** for the multi-turn gating study.
- [ ] **`context_edit_v2_no_gate_fresh.yaml`** or equivalent config (sets `min_turns=1, max_resets=1000` to make every turn an edit).

## Changes from rev.1

| Topic | rev.1 | rev.2 |
|---|---|---|
| Prompts | Use paper-specific prompt per benchmark; v8 normalization deferred to Phase 4 | v8 default for all conversation benchmarks (LiC, CollabLLM, WildChat); s1 only as CF fallback |
| Gating | Mentioned briefly as "collapses in 1-turn replay" | Promoted to **Phase 3**, dedicated multi-turn fresh-sim study comparing always-on Reset vs Gated-Reset on DeepSeek (and maybe gpt-5.4) |
| Cost reporting | Noted as "unknown for Foundry models" | Scaffolded `foundry_pricing.yaml` for user to fill; `get_model_pricing()` already merges it; token counts saved regardless |
| Content filter | Mitigation plan v8 → s1 → degraded | Same plan but stronger callout that Foundry IS Azure and could trip CF; we monitor `content_filter_errors.jsonl` per cell from Phase 1 onward |
| Analysis reuse | Not addressed | **New** caching backend + registry, integrated into ConversationAnalyzer; saves ~2/3 of analyzer calls in Phase 1 and removes noise across the variant comparison |

## Risks and contingencies (unchanged from rev.1 unless noted)

- Content filter on Phase 2 OAI cells — mitigation chain above.
- Phase 1 winner is benchmark-specific — we promote 2 variants (Augment + best Reset/Rewrite) to hedge.
- AC3-Rewrite LLM compaction adds noise — caching the analysis removes one source of noise, but the rewrite step is its own LLM call (also cacheable on (prefix, rewrite-model, rewrite-prompt) — **TODO**: extend cache to cover rewrite outputs if Phase 1 shows the rewrite step is high-variance).
- Cost unknown for Foundry models — pricing-file scaffolded, user-fillable; token counts always logged.
- Output-dir collision — all launchers use unique `logging.output_dir=outputs/<runtag>/<exp>_<ts>` (≥ 2 levels deep).
- **New**: cache poisoning — a buggy analyzer commit lands and writes wrong analyses to disk. Mitigation: cache key includes `prompt_version` and `analyzer_model`; in addition, the registry entry records `experiment_origin`, so we can `--invalidate-by-experiment-origin <bad_exp>` if needed. The cache directory can also be force-reset by `rm -rf outputs/analysis_cache/` between major prompt revisions.

Pending your sign-off — happy to adjust any of the decisions or scope further. If approved, I'll execute the checklist top-to-bottom and kick off Phase 1.

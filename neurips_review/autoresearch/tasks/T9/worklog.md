# T9 — Analyzer-model sensitivity (Reviewer Vg97 Q3, the half we never answered)

**Question:** hold the assistant fixed, swap only the analyzer. Does AC3's gain degrade
gracefully as the analyzer weakens, or collapse? Does a non-gpt analyzer work at all?

**Status:** in progress (2026-07-29 overnight session). Operator asleep — no questions asked;
every ambiguity resolved here.

---

## 0. TRAP CHECK #1 — is `analysis_cache` safe under an analyzer swap?

**Verdict: the key DOES include the analyzer model identity. I disabled the cache anyway.**

Evidence:

- `src/ctx_editor/strategies/analysis_cache.py:83-107` — `AnalysisCache.make_key()` builds its
  SHA-256 over a payload containing `"analyzer_model"` (line 92), alongside `trace_hash`,
  `prompt_version`, `spec_only`, `memory_target_query`, `enforce_compliance`, `memory_present`.
- `src/ctx_editor/strategies/analyzer.py:585-593` — the only call site:
  ```python
  cache_key = AnalysisCache.make_key(
      trace_hash=trace_hash,
      analyzer_model=self.model,        # <-- analyzer.py:587
      prompt_version=self.prompt_version,
      ...
  )
  ```
  `self.model` is the live analyzer model, set from the strategy's `analyzer_model` ctor arg
  (`context_edit_v2.py:41,54`; `append_analysis.py:53,68`), which Hydra binds to
  `${model.ctx_editor.model}` (`config/experiment/context_edit_v2_no_gate.yaml:9`).
  So `model.ctx_editor.model=X` propagates into the cache key. A cross-analyzer stale hit is
  **not** possible.
- `analyzer.py:620-628` also re-writes `analyzer_model` into the stored `key_inputs`, so any
  cached entry can be audited after the fact.

**Decision D0:** despite the key being correct, every T9 run passes
`experiment.strategy.analysis_cache_dir=null`. Rationale: (a) the cost of a cache miss on a
~90-sample replay is a couple of dollars, (b) belt-and-braces beats a subtle key bug in an
experiment whose entire point is that the analyzer output differs per arm, (c) a shared cache
also removes analyzer-sampling variance in a way that would *flatter* the comparison.
Recorded so the deliverable is not contingent on trusting the cache.

RECON's Unknown #9 ("cache-key logic was not read; assume unsafe") is hereby **closed: key is
model-aware**. Prior runs that used `outputs/analysis_cache` with a *different* analyzer than
the one that filled it were therefore not corrupted.

---

## 1. Venue selection

Requirement from the task: a venue with real headroom, not near-ceiling math.

Chosen: **LiC `code_v2` and `database_v2`, last-turn replay, `conv0` prefix pool**, i.e. exactly
the design of the paper's phase-1 LiC matrix.

- Prefix pool on disk: `data/valid_prefixes_htn50_52/deepseek_v4_flash_foundry/{code_v2,database_v2}/conv0`
  (41 and 50 prefix files).
- The paper's own phase-1 numbers on this exact pool (recovered from the snapshot at
  `~/ac3/recovered_t2c/ctx_editor/outputs/post_neurips_ac3_phase1/`, raw accuracy):

  | task | n | Baseline | AC3-Reset (`context_edit_v2_no_gate`) | Δ |
  |---|---|---|---|---|
  | code_v2 conv0 | 40 | 30.0% | 50.0% | +20.0 |
  | database_v2 conv0 | 49 | 14.3% | 51.0% | +36.7 |
  | (math_v2 conv0) | 48 | 56.3% | 72.9% | +16.7 |

  Baseline ≈ 21% pooled on code+db — enormous headroom, and a +29pp effect to degrade.
  This is the opposite of the `rebuttal_random` math cell (87.5% baseline) that killed T5.

**Decision D1 — assistant = `DeepSeek-V4-Flash` (Foundry), not gpt-5.4-mini.** Reasons:
1. It is the model that *generated* these prefixes, so the replay is self-consistent (a
   gpt-5.4-mini assistant resuming a DeepSeek prefix adds a confound orthogonal to the question).
2. It is the paper's phase-1 headline LiC assistant, so the T9 arms drop straight into an
   existing table.
3. It is far from ceiling here; gpt-5.4-mini on math is not.
4. It frees the TRAPI quota that other overnight agents are using.
The assistant is held **fixed across all arms** — that is the only thing the design requires.

**Decision D2 — strategy = `context_edit_v2_no_gate` (AC3-Reset, always-on).** `min_turns: 1`,
`max_resets: 100`, so the analyzer fires on **every** sample. A gated arm would let a weak
analyzer duck the question by simply not firing; always-on maximises the analyzer's causal
share and is therefore the right probe for analyzer sensitivity. (Gate-behaviour under a weak
analyzer is a separate, secondary question — added as a Gated arm only if budget allows.)

---

## 2. The analyzer ladder

Deliberately spans strength AND family, per the task's "include a genuinely weaker analyzer".

| Arm | Analyzer model | Endpoint | Family | Intended rung |
|---|---|---|---|---|
| `ref` | `DeepSeek-V4-Flash` | mgalley-foundry2 | DeepSeek | reference (= phase-1 default, self-analyzer) |
| `gpt54mini` | `gpt-5.4-mini_2026-03-17` | TRAPI redmond/interactive | OpenAI (reasoning) | strong; the paper's default analyzer elsewhere |
| `kimi` | `Kimi-K2.6` | mgalley-foundry2 | Moonshot | cross-family control |
| `gpt4omini` | `gpt-4o-mini` | dl-openai-3 | OpenAI (non-reasoning) | clearly weaker |
| `llama70b` | `Llama-3.3-70B-Instruct` | mgalley-foundry2 | Meta | genuinely weak + cross-family (budget permitting) |
| `baseline` | — (no analyzer) | — | — | floor |

Note this ladder gives **three** non-gpt families (DeepSeek, Moonshot, Meta), so the
"AC3 is not a gpt-specific artifact" claim is answerable independently of the sensitivity curve.

---

## 3. TRAP CHECK #2/#3/#4 — endpoints, overrides, FN analysis

- **#2 reasoning_effort:** `model/deepseek_v4_flash_foundry.yaml` has **no**
  `ctx_editor.reasoning_effort` key, and `context_edit_v2_no_gate.yaml:10` reads it via
  `${oc.select:model.ctx_editor.reasoning_effort,null}` → resolves to `null`. So the gpt-4o
  reasoning_effort trap does **not** apply to this model config. No override needed.
  (It *would* apply if I had used `gpt5_4_mini_trapi.yaml` as the base — noted, avoided.)
- **#3 load balancer:** `load_balancer=multi_endpoint_foundry` already serves DeepSeek-V4-Flash,
  Kimi-K2.6, Llama-3.3-70B-Instruct (mgalley-foundry2) and gpt-4o-mini / gpt-5-mini
  (dl-openai-3, gpt-4o-mini re-listed by T8 earlier tonight). It does **not** serve TRAPI.
  → new file `src/ctx_editor/config/load_balancer/t9_foundry_trapi.yaml` = multi_endpoint_foundry
  + the TRAPI `redmond/interactive` block. Edits recorded in §4.
- **#4 FN analysis:** this experiment does **not** touch TRAPI for the assistant/system roles, so
  the TRAPI-only FN model rule does not bind. `false_negative_analysis.model` default is
  `gpt-5-mini`, which **is** served (dl-openai-3, quota 150) — same as the phase-1 runs it is
  being compared against. Left at the default deliberately, for comparability.
- **#5 seed:** no `seed=` overrides anywhere. Replicates (if any) are sampling replicates at
  `temperature: 1.0`.
- **#6 sample count:** not used — replay mode takes its n from the prefix pool.

---

## 4. Infrastructure changes made

**New file: `src/ctx_editor/config/load_balancer/t9_foundry_trapi.yaml`.**
Strict superset of `multi_endpoint_foundry.yaml` as of 2026-07-29 (i.e. including T8's
gpt-4o-mini re-listing on `dl-openai-3`) **plus** the `trapi-redmond-interactive` block copied
verbatim from `trapi.yaml`. Also dropped `gpt-4o-mini` from the dead `fxdata-shared` block so
nothing can route to the 401'ing endpoint. No existing config file was modified — the T8 fix was
already in place. Verified at startup:
```
Load balancer initialized with 4 endpoints, supporting models: [... 'DeepSeek-V4-Flash', ...
 'Kimi-K2.6', 'Llama-3.3-70B-Instruct', ... 'gpt-4o-mini', 'gpt-5-mini', ...
 'gpt-5.4-mini_2026-03-17', 'gpt-4o_2024-11-20']
```

**New files under `neurips_review/autoresearch/tasks/T9/`:** `run_t9_sweep.sh` (the sweep driver,
idempotent — skips arms whose `run_summary.json` already exists) and `analyze_t9.py` (paired
analysis; statistical core lifted from `T2c/paired_split.py`).

## 5. Smoke test (2026-07-29 11:00)

5-sample code replay, analyzer = DeepSeek-V4-Flash, cache disabled. Completed in 1m58s,
$0.0013, 1/5 correct. Trace audit of
`outputs/T9/smoke/traces/code/context_edit_v2_no_gate/sharded-HumanEval_128.json` confirms the
swap is observable per-sample:
```
conversation_analysis {'needs_edit': True, 'analyzer_model': 'DeepSeek-V4-Flash'}
context_edit_output  {'analyzer_model': 'DeepSeek-V4-Flash'}
conversation_reset   {'label': 'context_edit', 'total_resets': 1}
provenance {'source_path': '.../code_v2/conv0', 'source_experiment': 'baseline',
            'source_models': {'assistant': 'DeepSeek-V4-Flash'}, 'replay_turns': 1}
```
So every arm can be verified post hoc to have actually used the analyzer it claims — this is the
audit trail that closes the "did the swap take effect?" question independently of the cache
argument.

## 6. Launch

```bash
bash neurips_review/autoresearch/tasks/T9/run_t9_sweep.sh code     rep1   # 6 arms, n=40
bash neurips_review/autoresearch/tasks/T9/run_t9_sweep.sh database rep1   # 6 arms, n=49
```
Both launched 2026-07-29 11:02 UTC, in parallel, `execution.max_concurrent=5` each (10 in
flight total, shared with other overnight agents). Per-arm command (baseline arm drops the
last two overrides and uses `experiment=baseline`):
```bash
ctx-editor experiment=context_edit_v2_no_gate \
  model=deepseek_v4_flash_foundry \
  load_balancer=t9_foundry_trapi \
  model.ctx_editor.model=<ANALYZER> \
  experiment.strategy.analysis_cache_dir=null \
  task=code_v2 task.data_file=data/htn50_52_code_subset.json \
  execution.replay_source=data/valid_prefixes_htn50_52/deepseek_v4_flash_foundry/code_v2/conv0 \
  execution.replay_turns=1 execution.max_concurrent=5 \
  experiment_name=T9_rep1_code_<ARM> logging.output_dir=outputs/T9/rep1/code_<ARM>
```
Observed rate: ~4 s/sample for the replay pass + ~9 s/sample for FN analysis ⇒ ~8-12 min/arm.

## 7. Raw results, rep1 (appended as each arm lands)

Raw accuracy (`Accuracy:` in `summary.txt`). Artifact root `outputs/T9/rep1/<task>_<arm>/`.

| task | arm | analyzer | raw acc | correct/n | wall clock |
|---|---|---|---|---|---|
| code | baseline | — | 30.00% | 12/40 | 11:02→11:11 |
| code | ds_v4_flash | DeepSeek-V4-Flash | 55.00% | 22/40 | 11:11→11:22 |
| code | gpt54mini | gpt-5.4-mini_2026-03-17 | 45.00% | 18/40 | 11:22→11:32 |
| database | baseline | — | 18.37% | 9/49 | 11:02→11:11 |
| database | ds_v4_flash | DeepSeek-V4-Flash | 42.86% | 21/49 | 11:11→11:25 |
| database | gpt54mini | gpt-5.4-mini_2026-03-17 | 48.98% | 24/49 | 11:25→11:32 |

**Sanity check against the paper's phase-1 cell (same prefixes, same assistant, 2026-05 run):**
code baseline 30.0% vs 30.0% today, code Reset 50.0% vs 55.0% today; database baseline 14.3% vs
18.4% today, database Reset 51.0% vs 42.9% today. Reproduction is within sampling noise at
temperature 1.0 for n=40/49 — the harness is behaving, and the phase-1 numbers replicate.

**⚠ Note on `adjusted_accuracy` in this venue.** The FN classifier flags 17-19 of ~40-49 samples
as "user-sim-induced" on the AC3 arms but only 0-5 on Baseline, so adjusted accuracy jumps to
80-96% on AC3 arms and is **not comparable across arms** — the denominators differ wildly and in
a strategy-correlated way. **Headline metric for T9 is therefore raw accuracy on the full,
identical sample set**, which keeps the pairing exact. Adjusted numbers are recorded per run in
`run_summary.json` but are not used for the sensitivity claim.

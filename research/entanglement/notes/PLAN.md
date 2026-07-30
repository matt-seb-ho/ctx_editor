# Plan: The Entanglement Knob — a single-benchmark simulator for context-pollution methods

**Date:** 2026-07-30 · **Status:** executing (autonomous overnight) · **Owner:** Matthew Ho
**Origin:** `neurips_review/philippe_discusion.md`. Design inputs:
`research/entanglement/notes/concept_exploration.md`, `.../impl_map.md`.

## Thesis (what the experiment must show)

On a *single* benchmark, expose **entanglement** — how much each user turn depends on the
assistant's prior reply — as an explicit knob `e ∈ {0,1,2,3}`, holding the task (and its
ground-truth answer) fixed. Then plot **methods × entanglement**. Predicted shape
(concept §5):

| Method \ e | e0 indep | e1 | e2 | e3 corrections |
|---|---|---|---|---|
| Accumulate (S0) | low (polluted) | low | low | low |
| **Drop-assistant** (Huang/ERGO) | **high (exploit)** | high– | **mid ↓** | **low ↓↓ collapse** |
| Naive summarize | high | mid–high | mid | low–mid |
| **Decontextualize-then-edit (ours, ctx_edit_v2)** | high | high | high–mid | **mid–high (holds)** |

Money shots: (a) drop-assistant collapses left→right (kills "just delete the assistant"); (b) ours
stays flat-high, esp. e3. e0 is the credibility check (ours ties drop; drop beats accumulate =
reproduces the known LiC exploit).

## Design decisions [DECISION]

1. **Knob = 4 ordinal levels folded into the UserAgent** (`EntanglementUserAgent`), not a post-hoc
   rewrite — avoids double-paraphrase drift (concept threat #5). Level 0 delegates to the stock
   `UserAgent` so it reproduces standard LiC exactly. Levels from the severity taxonomy (concept §3):
   0 independent · 1 light-anaphora · 2 referential (assistant entities/ordinals) · 3
   relative-elliptical/corrections.
2. **Faithfulness by gold-pinning** (concept §2, threat #4): the simulated user is *competent* —
   it knows the gold shard and references the assistant only for FORM/deixis, never composing on an
   assistant-produced VALUE. Every turn must be **recoverable-with-context** (informed) yet
   **unrecoverable-without** (blinded). Each turn emits a `decontextualized` self-report.
3. **Validate the knob, don't assert it.** `recoverability.py` measures, per level, informed vs
   blinded recoverability against the TRUE gold shard, using a *different* model family
   (gpt-5.4-mini) than the generator (gpt-4o) to avoid circularity (threat #3). Success =
   informed high & flat across levels (faithful); blinded falls as level rises (entanglement grows).
4. **Method rows map to existing strategies** (no new strategy code needed):
   `baseline` (S0/accumulate) · `omit_assistant` (drop) · `summarize_v1` (naive compaction) ·
   `context_edit_v2` (ours). Ceiling (single-turn Full) added later if time.
5. **Benchmark:** start with LiC **math** (dev_math_subset, N=23; pipeline proven, cheap). Caveat
   discovered in pilot: math shards are *independent factual reveals*, so faithful high-entanglement
   is harder than for artifact-editing tasks (code/database). If math can't carry e3 faithfully
   (informed recoverability drops), pivot benchmark to **code** or **database** (concept §6 threat
   #8 also wants a 2nd task as robustness). Record the finding either way.
6. **Model:** TRAPI `gpt5_4_mini_trapi` (assistant/editor = gpt-5.4-mini, user/system = gpt-4o) via
   `load_balancer=trapi`, `az login` auth. No static keys on this box.

## Execution steps

- [x] Build `EntanglementUserAgent` + prompt + `user_mode/entangled.yaml` + run_experiment wiring.
- [x] Smoke test (e0 == LiC, e3 realized). Found + fixed level-3 vagueness (informed-recoverability).
- [x] Build `recoverability.py` validation instrument.
- [~] **Validation pass**: baseline × {e0,e1,e2,e3}, N≈5, run recoverability → confirm knob valid.
      If informed recoverability at e3 is low on math → pivot benchmark; else proceed.
- [ ] **Main sweep**: {e0,e1,e2,e3} × {baseline, omit_assistant, summarize_v1, context_edit_v2},
      N≈8. Collect accuracy per cell → matrix + figure.
- [ ] **Figure**: accuracy vs entanglement, one line/method (the figure Philippe described).
- [ ] **Analysis + write-up** in `docs/`, update `docs/index.md`. Commit incrementally.

## Artifacts

- Code: `src/ctx_editor/agents/entanglement_user_agent.py`, `prompts/entanglement_user_agent.txt`,
  `config/user_mode/entangled.yaml`; analyzer `research/entanglement/src/recoverability.py`.
- Runs: `research/entanglement/artifacts/<name>/` (metrics.json, traces/).
- Log/state: `research/entanglement/WORKLOG.md`, `state/progress.json`.

## Risks / stop conditions

- Difficulty confound (biggest): guard with recoverability instrument; if informed recoverability
  falls with level, the knob is leaking difficulty → fix prompt or pivot benchmark.
- Ceiling/floor compression: if baseline≈floor and Full≈100%, methods can't separate → pick
  mid-difficulty samples (htn50-style failure-selected pools exist).
- Cost: each run ≈ $0.18/75s; full sweep ≈ $25. Acceptable. Keep N modest first, scale if signal.

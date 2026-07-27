# Work Log — NeurIPS Rebuttal (Sub. 27902)

Running log of decisions, progress, findings, and artifact locations for the autonomous rebuttal-prep session. Newest entries appended at the bottom of each section. All artifacts live under `neurips_review/`.

**Session start:** 2026-07-27 ~10:20. User asleep ~6h; work autonomously, don't block.

## Objective (this session)
1. Prepare paste-ready per-reviewer + AC rebuttal comment drafts.
2. Run new experiments via TRAPI (gpt-5.4-mini_2026-03-17, `redmond/interactive`) **if they help** the rebuttal.
3. Write a `strategy.md` (rebut-for-NeurIPS vs withdraw-for-ICLR); default = rebut NeurIPS.
4. Keep this work log.

## Artifacts produced (first turn, pre-sleep)
- `neurips_review/ac3_reviews_raw.md` — original OpenReview paste (moved).
- `neurips_review/ac3_reviews_clean.md` — cleaned/reformatted reviews + cross-review map.
- `neurips_review/01_problem_summary.md` — deduped problems A–J, mapped to AC's 3 pillars.
- `neurips_review/02_triage.md` — severity × addressability tiers + experiment ranking.
- `neurips_review/03_rebuttal_plan.md` — per-concern battle plan w/ post-NeurIPS numbers.
- `neurips_review/04_rebuttal_response.md` — first-pass Global + per-reviewer response draft.
- Committed on `main`: `dbdab2d`.

## Key evidence already in hand (from post-NeurIPS docs, verified by sub-agent digest)
- LiC scaled to n≈113–150/cell (from 18–25). Mean±std (Gated-Reset N=3): math 80.0±5.0, code 64.4±7.2, db 38.7±6.1, actions 61.3±6.1 — all clear FC baseline.
- Full-pool (non-difficulty-selected) LiC Reset gain: +13–17pp across 3 models (proxy answer to iNYK Q1).
- tau2 (n=19, 3 models): AO→0% everywhere; best AC3 op beats baseline +15.8/+26.3/+24–34pp. Gated-Reset loses on gpt-5.4 (52.6<68.4).
- CollabLLM user-sim swap: AC3-Augment 100% math-hard, AC3-Reset 20% leads bigcodebench (earlier regression was a weak-user-sim artifact).
- WildChat N=3: Reset 89.8±1.4, Augment 92.1±1.3 win-rate vs AO. Honest range 72–92%.
- Traps to avoid: "robust across spectrum" (retired), "every operator beats baseline" (false, 6 sub-baseline cells), +47pp Kimi (use +24–34).

## Decisions

### D1 — Which experiments are worth running
Ranked in `02_triage.md`. Two are genuinely net-new and decisive:
- **Exp1 (iNYK Q1):** random-subset LiC Reset vs Baseline, selected *independently* of baseline failure. We have a proxy (full-pool +13–17pp) but a clean random draw is the exact thing iNYK asked for. HIGH value.
- **Exp2 (Vg97 Q3):** equal-compute self-reflection baseline at AC3's matched call count + latency. Directly tests "gains = decontamination, not more compute." Net-new, no existing proxy. HIGH value.
Others (multi-seed tau2, span-annotation P/R) are compute-heavy or nice-to-have → camera-ready commitments.

## Progress

### TRAPI connectivity — DONE
- Guide: `~/misc/trapi-llm-queries.md`; example `~/misc/trapi_example.py`.
- Smoke test `neurips_review/experiments/smoke_trapi.py`: **all combos OK**. `redmond/interactive` works with the **active az identity, no subscription pinning needed** (model `gpt-5.4-mini_2026-03-17` returns completions). gcr/shared also works.
- Env: no pre-existing venv; bootstrapped `.venv` via `uv venv --python 3.12` + `uv pip install -e ".[all]" azure-identity`. Repo deps OK (openai 2.48.0). Use `. .venv/bin/activate` before any run.
- Repo has no native `type: trapi`, but `type: azure_foundry` (AsyncOpenAI + base_url + AAD token as api_key + **configurable `aad_scope`**) matches TRAPI's OpenAI-v1 path. Plan: reuse azure_foundry pointed at `https://trapi.research.microsoft.com/redmond/interactive/openai/v1/` with `aad_scope: api://trapi/.default`.

<!-- append below -->

## Progress (cont.) — experiments launched

### D2 — Experiment redesign (IMPORTANT)
Discovered while wiring up:
- **`htn50_52` is baseline-failure-selected** (top-N by true-negative count vs gpt-5.2). So running on it does NOT answer iNYK Q1 (they want a subset selected *independently* of baseline results). Confirmed via `docs/htn50_52_subset.md`.
- Prefix pools (`data/valid_prefixes_htn50_52/`) exist only for 4 models — **no gpt-5.4-mini pool** — so a *replay* run isn't directly available for the new model.
- Default `ctx-editor` mode is **fresh end-to-end multi-turn sim** (`execution.replay_source=null`), which the prefix-pool absence pushes us toward anyway.
- LiC "math" in this repo = **sharded GSM8K** entirely (all pools). So a random draw from `math_full_subset.json` (103, NOT hard-selected) is representative.

**Redesigned Exp1** to kill three birds at once: fresh END-TO-END LiC math on a **random, non-baseline-selected N=40** subset (`data/rebuttal_random_math40.json`, seed 42), assistant = **gpt-5.4-mini via TRAPI** (a fresh model absent from the mega-table). This answers **iNYK Q1** (random subset) + concern **G** (end-to-end, not replay) + adds **fresh-model generalization** in one run. Conditions: baseline / reset / gated.

**Exp2** = equal-budget control for **Vg97 Q3**: `ReflectionStrategy` (legacy) makes a matched extra LLM call per turn over the FULL polluted context but does NOT structurally decontaminate. If Reflection≈Baseline while Reset>Baseline → the gain is decontamination, not compute. Same N=40 subset.

### Infra wired
- `src/ctx_editor/config/load_balancer/trapi.yaml` — azure_foundry type → TRAPI v1 endpoint, scope `api://trapi/.default`, models gpt-5.4-mini_2026-03-17 + gpt-4o_2024-11-20.
- `src/ctx_editor/config/model/gpt5_4_mini_trapi.yaml` — assistant/ctx_editor=gpt-5.4-mini, user/system=gpt-4o.
- Env deps added to `.venv`: python-dotenv, sqlparse (were missing; sqlparse ImportError was masking task registry → "Task math_v2 not found").
- Smoke tests: baseline 2/2 OK ($0.05, 4 turns), reset 2/2 OK ($0.06, 7 turns). Pipeline confirmed end-to-end on TRAPI.

### Launched (background, ~10:34)
- Exp1: `neurips_review/experiments/run_exp1.sh` → `outputs/rebuttal_random/full_{baseline,reset,gated}` ; summary → `neurips_review/experiments/exp1_results.txt`.
- Exp2: chained to start after Exp1 (`run_exp2.sh`) → `outputs/rebuttal_random/full_reflection` ; summary → `exp2_results.txt`.
- Kept sequential (not concurrent) so per-condition wall-clock stays a clean relative-latency signal for Vg97 Q3.

### NOTE / caveat to self
- gpt-5.4-mini baseline solved the 2 smoke GSM8K in multi-turn (ceiling risk on easy items). N=40 includes harder items + LiC degradation, so expect spread. If baseline is near-ceiling and Reset shows ~0 gain, report honestly (it would still show "no harm" + the existing +13–17pp full-pool evidence stands). Single seed — report as such.

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

## RESULTS (incoming)

### Exp1 (random N=40 GSM8K, end-to-end, gpt-5.4-mini) — partial
- **Baseline: 90.0% (36/40)** raw; adjusted 90.0%. wallclock 205s, $1.74, 5.2 turns.
- **AC3-Reset: 97.5% (39/40)** raw; adjusted 100% (39/39, 1 user-sim-induced excluded). wallclock 547s.
- **→ +7.5pp raw (90.0→97.5) on a uniformly random, non-baseline-selected subset, END-TO-END.** Positive answer to iNYK Q1 even with baseline near ceiling. Reset closed 3/4 of the remaining gap.
- Gated running; reflection (Exp2) + database (Exp3) chained.
- Fair headline = RAW (same n=40 denominator): 90.0 vs 97.5. Adjusted denominators differ (excludes user-sim-induced), so lead with raw.

### Paper edit applied (inner repo b1a629a, local only, NOT pushed — remote down)
- Softened "the only method robust across the spectrum" → "the only method that improves over full context across the entire spectrum" in abstract + intro. Directly answers the overclaim all 3 reviewers cited. Handoff: `neurips_review/paper_edits_needed.md`.

### Exp1 FINAL (random N=40 GSM8K, end-to-end, gpt-5.4-mini, seed 42)
| Condition | Raw acc | FN-adjusted | Δ raw vs base | wallclock | avg turns |
|---|---|---|---|---|---|
| Baseline | 90.0% (36/40) | 90.0% | — | 205s | 5.2 |
| AC3-Reset | 97.5% (39/40) | 100% (39/39) | **+7.5pp** | 547s | 8.5 |
| AC3-Gated-Reset | 95.0% (38/40) | 100% (38/38) | **+5.0pp** | 266s | 6.6 |

**Headline for iNYK Q1 + concern G:** on a uniformly random, non-baseline-selected subset, run END-TO-END (not replay) with a fresh model, both AC3 operators improve over baseline (+7.5 / +5.0pp raw; 100% adjusted). Gains survive off the difficulty-selected subset. Latency: Reset ~2.7× baseline wall-clock, Gated ~1.3× (gating cut turns 8.5→6.6). Single seed — reported as such.
- Task 9 (Exp1) complete. Exp1 placeholders filled in `05_comment_drafts.md`.
- Chain waiters for Exp2/Exp3 died (killed with launcher pgroup); re-running directly as tracked bg tasks. Exp2 (reflection) running now; Exp3 (database) next.

### Exp2 FINAL (equal-budget reflection control, random N=40 math)
- **Reflection: 97.5% (39/40)** raw = adjusted; 231s; 5.2 turns; $1.89.
- **= AC3-Reset (97.5%)** on this task. Baseline 90.0%. So on near-ceiling GSM8K, equal-budget reflection and Reset TIE — the task has too little *harmful* pollution to separate "compute" from "decontamination."
- **Honest handling (in 05 Vg97 Q3):** don't overclaim from this. Lean on the existing **contagious-pollution (Table 5)** result, which IS discriminating (extra compute in a contaminated stage drops *below* baseline). Commit a matched-budget control on a high-pollution benchmark (database/tau2) for camera-ready.
- **Latency:** reflection +13% wall-clock over baseline at equal turns (231 vs 205s, both 5.2 turns) — the clean per-call cost. Reset's 547s conflates with turn inflation (8.5 turns). Gated 266s/6.6 turns = deployment default.

### Exp3 (database) — SCRAPPED
- Spider SQLite DBs (`data/spider/databases/`) not present anywhere on disk; execution eval unrunnable without a large external download. No code-exec sandbox either. iNYK Q1 is already answered positively by Exp1 math, so database was only "nice-to-have discriminating." Removed `run_exp3_database.sh`.

## SESSION SUMMARY (for the user)
**Deliverables in `neurips_review/`:** cleaned reviews, problem summary, triage, rebuttal plan, full rebuttal response (04), **paste-ready per-reviewer comment drafts (05)** with real experiment numbers, strategy note (rebut-vs-ICLR), paper-edits handoff, this worklog, and `experiments/` (TRAPI harness + result txts).

**Experiments run (gpt-5.4-mini via TRAPI, redmond/interactive):**
- Exp1 answers iNYK Q1 + concern G: random, non-baseline-selected, END-TO-END LiC-math on a fresh model → Baseline 90.0 → Reset 97.5 (+7.5pp) / Gated 95.0 (+5.0pp). Gains survive on an unbiased subset.
- Exp2 answers Vg97 Q3: equal-budget reflection ties Reset on easy math (honest null); real discrimination comes from the contagious-pollution result.

**Paper:** softened the "robust across the spectrum" overclaim in abstract+intro (inner-repo commit b1a629a, NOT pushed — Overleaf remote down).

**Strategy call:** proceed with NeurIPS rebuttal (drafted), but treat it as the ICLR-revision spine; realistic p(NeurIPS accept) is low given 3× borderline-reject + AC leaning reject. See `strategy.md`.

**Open items for the user:** push the paper edit when Overleaf reachable; coordinate with co-authors before posting; decide whether to run the discriminating equal-budget test (needs Spider DBs / tau2 harness) and MT-OSC/U-Fold baselines for camera-ready/ICLR.

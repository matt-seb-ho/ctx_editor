# T2B — Counterfactual span ablation (causal, non-circular pollution labels)

**Design source:** `neurips_review/experiment_todos.md` §T2, Tier B ("the gold standard").
**Reviewer prompt:** 5YHP W5, plus the circularity objection to judge-based pollution labels.
**Status:** in progress (2026-07-29 overnight session, operator asleep). Every ambiguity resolved here.

**What T2B adds over T2A.** T2A established a detector-free causal effect for *injected* spans
(harmful −11.1pp, useful +15.1pp on an unedited context) and a 2×2 against AC3-Reset / AC3-Rewrite.
Its stated limitation is that injected pollution is plausibly more salient than natural pollution.
T2B keeps the causal design and swaps constructed spans for **naturally occurring** ones:
**natural spans, causal labels.**

---

## 0. Reconnaissance (t+0 .. t+25 min, 15:45–16:10)

Read, as instructed: `experiment_todos.md` §T2; `tasks/T2A/{RESULTS.md,worklog.md,run_matrix.sh,run_factorial.sh,make_single_arms.py}`;
`src/ctx_editor/execution/replay.py`.

### 0.1 Trap 3 — is the `seed=` fix present?

Checked in this tree exactly as T2A did:

```
grep -rn "seed" src/ctx_editor/run_experiment.py src/ctx_editor/execution/*.py
```

(result recorded in §0.1a below). **Decision D0: T2B does not rely on `seed=`.** T2B's whole
design is repeated sampling at temperature 1.0 — replicates are the measurement instrument, not a
nuisance. I therefore call them "replicate runs at temperature 1.0" throughout, as the brief
permits, and never claim bit-for-bit reproducibility of an individual replicate.

### 0.2 Venue (brief + TODO)

LiC **database_v2** and **code_v2**. No math (ceiling + T2c analyzer answer-leakage confound).
Replay prefixes: `data/valid_prefixes_htn50_52/deepseek_v4_flash_foundry/{database_v2,code_v2}/conv0`
— the paper's own phase-1 prefixes, same source T2A used. Spider DBs restored (`data/spider/databases/`).

### 0.3 Harness facts confirmed by reading the code

* `build_replay_trace(..., replay_turns=1)` → `truncate_final_assistant=True`. So the **prefix that
  the ablation acts on** is messages `0 .. n-2`, i.e. system + all user turns + all assistant
  messages **except the last one**. Spans therefore live in assistant messages at indices
  `2, 4, …, n-3`.
* `load_baseline_traces()` keys by `sample_id` and `rglob`s the directory, so **one variant per
  directory** — ablation conditions must be separate directories. (Also: it picks up
  `false_negatives.json` for user-sim skipping; I copy only trace files, as T2A did, so no
  condition-dependent skipping.)
* Run invocation copied verbatim from `T2A/run_matrix.sh`, including
  `false_negative_analysis.model=gpt-5.4-mini_2026-03-17` (trap 1) and
  `model=gpt5_4_mini_trapi load_balancer=trapi execution.max_concurrent=5` (trap 6).
* Output dir is **T2B-scoped** (`outputs/T2B/...`), trap 5.
* **Metric = raw accuracy** (trap 2). `adjusted_accuracy` excludes 50–78% of editing-arm failures
  vs 9% for baseline, so it is not comparable across arms; and for the ablation arms specifically
  the whole point is to measure the assistant's raw success rate under a fixed prefix. Stated
  explicitly in RESULTS.

### 0.4 Timing budget (from `T2A/run_matrix.log`)

Baseline replay cells of 40–80 samples took 1.5–2.5 min at `max_concurrent=5`, i.e. ≈ 2–3.5 s of
wall clock per sample. A T2B condition-run of ~25 conversations is therefore ≈ 1–1.5 min. This is
what makes N replicates per condition affordable.

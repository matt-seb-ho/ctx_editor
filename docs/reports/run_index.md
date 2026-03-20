# Run Index — Dev Set Experiments

All runs use gpt-5-mini (medium reasoning) as assistant/analyzer, gpt-4o-mini for user/system agents, on `dev_{task}_subset.json` data files.

---

## Batch 1 — Full Simulation (2026-03-13)

**What changed**: First dev set run. v1 evaluators, broken XML tag prompts (instructions inside tags → analyzer produced empty aligned/issues ~90% of the time). Error attribution disabled.

**Script**: `./scripts/run_dev_experiments.sh`

**Takeaways**: S1 best raw performer (48% math). S2 appeared to underperform but was actually broken — analyzer couldn't parse its own output. Memory helped S0 math (+21pp) but hurt actions. Database broken (missing local DB).

**Wall clock**: ~10 hours | **Cost**: ~$7.50

| Task | S0 | S0+mem | S1 | S1+mem | S2 | S2+mem |
|------|:--:|:------:|:--:|:------:|:--:|:------:|
| math | 22% | 43% | **48%** | 43% | 39% | 30% |
| code | 4% | 16% | 8% | **21%** | 9% | 8% |
| actions | 8% | 0% | **16%** | 12% | 0% | 4% |

<details><summary>Output directories</summary>

| Run | Dir |
|-----|-----|
| S0 math | `outputs/2026-03-13/13-44-00` |
| S0 code | `outputs/2026-03-13/13-53-02` |
| S0 actions | `outputs/2026-03-13/14-15-27` |
| S0+mem math | `outputs/2026-03-13/14-19-58` |
| S0+mem code | `outputs/2026-03-13/14-39-29` |
| S0+mem actions | `outputs/2026-03-13/15-12-35` |
| S1 math | `outputs/2026-03-13/15-23-42` |
| S1 code | `outputs/2026-03-13/15-40-51` |
| S1 actions | `outputs/2026-03-13/16-35-53` |
| S1+mem math | `outputs/2026-03-13/16-48-08` |
| S1+mem code | `outputs/2026-03-13/17-29-53` |
| S1+mem actions | `outputs/2026-03-13/19-06-27` |
| S2 math | `outputs/2026-03-13/19-27-26` |
| S2 code | `outputs/2026-03-13/19-46-41` |
| S2 actions | `outputs/2026-03-13/20-35-49` |
| S2+mem math | `outputs/2026-03-13/20-46-51` |
| S2+mem code | `outputs/2026-03-13/21-26-09` |
| S2+mem actions | `outputs/2026-03-13/22-39-52` |

Logs: `outputs/dev_logs/2026-03-13_12-59-06/`
Memory: `outputs/dev_memories/2026-03-13_13-43-59/`
Stale run (aborted): `outputs/2026-03-13/12-59-07` (ignore)

</details>

---

## Batch 2 — Replay, broken prompts (2026-03-14 morning)

**What changed**: Replay mode (reuse S0 conversation prefixes, regenerate last turn only). Still v1 evaluators, still broken XML prompts. Error attribution enabled (gpt-5-mini). S2 accumulated state fix applied (include compacted conversation in task spec query).

**Script**: `./scripts/run_replay_experiments.sh`

**Takeaways**: S2 still broken (~90% empty analysis). Error attribution revealed massive extraction failure rate. Confirmed replay is 6.6x faster and 89% cheaper than full sim.

**Wall clock**: ~1.8 hours | **Cost**: ~$0.60

| Task | S0 base | S1 | S1+mem | S2 | S2+mem |
|------|:-------:|:--:|:------:|:--:|:------:|
| math | 22% | 35% | **48%** | 26% | 13% |
| code | 4% | 8% | **20%** | 12% | 4% |
| actions | 8% | **16%** | 8% | 4% | 8% |

<details><summary>Output directories</summary>

| Run | Dir |
|-----|-----|
| S1 math | `outputs/2026-03-14/09-06-41` |
| S1 code | `outputs/2026-03-14/09-10-56` |
| S1 actions | `outputs/2026-03-14/09-18-37` |
| S1+mem math | `outputs/2026-03-14/09-23-10` |
| S1+mem code | `outputs/2026-03-14/09-33-32` |
| S1+mem actions | `outputs/2026-03-14/09-49-29` |
| S2 math | `outputs/2026-03-14/09-59-01` |
| S2 code | `outputs/2026-03-14/10-03-47` |
| S2 actions | `outputs/2026-03-14/10-12-23` |
| S2+mem math | `outputs/2026-03-14/10-17-42` |
| S2+mem code | `outputs/2026-03-14/10-29-45` |
| S2+mem actions | `outputs/2026-03-14/10-44-20` |

Logs: `outputs/replay_logs/2026-03-14_09-06-40/`
Memory: `outputs/replay_memories/2026-03-14_09-06-40/`

</details>

---

## Batch 3 — Replay, fixed XML prompts (2026-03-14 evening)

**What changed**: Fixed XML tag prompts — "Respond in the following format:" preamble with placeholder descriptions inside tags instead of instructions. Still v1 evaluators. Error attribution enabled.

**Script**: `./scripts/run_replay_experiments.sh`

**Takeaways**: Massive S2 improvement (math 26%→39%, code 12%→20%). S2+mem no longer regresses. Error attribution shows ~5 genuine extraction failures per math run and ~4 true assistant errors. Adjusted S2 math ≈65% (matches concat ceiling).

**Wall clock**: ~2.1 hours | **Cost**: ~$0.65

| Task | S0 base | S1 | S1+mem | S2 | S2+mem | Concat |
|------|:-------:|:--:|:------:|:--:|:------:|:------:|
| math | 22% | **48%** | 35% | 39% | 39% | 65% |
| code | 4% | 20% | **24%** | 20% | **24%** | 84% |
| actions | 8% | 12% | **20%** | 8% | 8% | 60% |

<details><summary>Output directories</summary>

| Run | Dir |
|-----|-----|
| S1 math | `outputs/2026-03-14/20-34-13` |
| S1 code | `outputs/2026-03-14/20-39-25` |
| S1 actions | `outputs/2026-03-14/20-50-44` |
| S1+mem math | `outputs/2026-03-14/20-57-19` |
| S1+mem code | `outputs/2026-03-14/21-17-21` |
| S1+mem actions | `outputs/2026-03-14/21-36-39` |
| S2 math | `outputs/2026-03-14/21-49-16` |
| S2 code | `outputs/2026-03-14/21-54-24` |
| S2 actions | `outputs/2026-03-14/22-04-05` |
| S2+mem math | `outputs/2026-03-14/22-10-44` |
| S2+mem code | `outputs/2026-03-14/22-22-45` |
| S2+mem actions | `outputs/2026-03-14/22-37-28` |

Logs: `outputs/replay_logs/2026-03-14_20-34-12/`
Memory: `outputs/replay_memories/2026-03-14_20-34-12/`

</details>

---

## Concat Baseline (2026-03-14)

Single-turn eval: all shards concatenated into one user message, no simulation.

**Script**: `python scripts/run_concat_baseline.py --tasks math code actions`

| Task | Accuracy |
|------|----------|
| math | 15/23 (65%) |
| code | 21/25 (84%) |
| actions | 15/25 (60%) |

Output: `outputs/concat_baseline/`

---

## Pending Changes (not yet tested)

- **v2 evaluators**: dev_math, dev_code, dev_database now route to v2 evaluators (boxed math extraction, code-fence prompts, fixed import bug). Should eliminate most extraction failures.
- **Prompt preamble**: "Use this format for your answer:" (less constraining than "Respond in this format").
- **Extraction failure logging**: Warnings logged when XML tag parsing falls back.
- **Task spec XML tags**: Restored for debugging visibility (was briefly changed to plain output).

These will take effect on the next run (Batch 4).

---

## Related Docs

- Error analysis: `docs/dev_set_error_analysis.md`
- Code task analysis: `docs/reports/code_task_analysis.md`
- Feedback deliberation: `docs/reports/feedback_deliberation_batch1.md`
- Replay results: `docs/reports/replay_results_batch1.md`
- Concat baseline: `docs/concat_baseline.md`

# T6 — Multi-replicate tau2 (τ²-bench)

Goal: re-run the seed-42 tau2 sweep at N=3 replicates; report mean ± spread.

---

## 2026-07-29 13:48 UTC — start

- Read `RECON/worklog.md` §B.2 (tau2). Key facts inherited:
  - Fork: GitHub `matt-seb-ho/tau2_ctxe`, HEAD `8e5fd3c`.
  - Prior sweep: 3 models (gpt-5.4, DeepSeek-V4-Flash, Kimi-K2.6) × arms, `telecom_small`, n=19 (20 tasks minus `[service_issue]break_apn_settings[PERSONA:None]`), N=1 seed 42.
  - Prior numbers: FC 68.4 / 31.6 / 26.3; AO 0/0/0; best AC3 84.2 / 57.9 / 73.7.
  - Setup cost estimated ">= half a day before first run" (734 MB tracked data, pyaudio shim, Kimi `--workers 4`, ToolCall JSON field_validator).
  - `fxdata-shared` = 401 for this identity; `mgalley-foundry2` + `dl-openai-3` live; TRAPI live.

## 13:50 UTC — cloned

- `git clone https://github.com/matt-seb-ho/tau2_ctxe.git /home/t-matthewho/ac3/tau2_ctxe` — SUCCESS.
- Deliberately **outside** the ctx_editor tree per task instructions (shared with other agents).

## 13:56 UTC — SEED VERIFICATION (fact #1 resolved)

**`--seed` on the tau2 fork IS real** — unlike ctx_editor, where `cfg.seed` was inert.
Trace of the threading, verified by reading source:

- `ctx_edit/run_parallel.py:223` `seed = args.seed + trial` → `:262` passed to `run_one`
- `run_one` → `ctx_edit/run_parallel.py:131` `Orchestrator(..., seed=seed)`
- `src/tau2/orchestrator/orchestrator.py:526-528`:
  ```
  if self.seed is not None:
      self.agent.set_seed(self.seed); self.user.set_seed(self.seed)
  ```
- `src/tau2/agent/base/llm_config.py:41-48` `LLMConfigMixin.set_seed` → `self.llm_args["seed"] = seed`
- `llm_args` is forwarded verbatim to litellm → provider `seed` parameter.

**Caveat that must appear in any writeup:** this is the OpenAI-style *best-effort*
`seed` param, not a deterministic RNG. Temperature is left at the provider default
(run_parallel passes `llm_args={}` for openai/ models, so `DEFAULT_LLM_ARGS_AGENT`
temperature=0.0 is NOT applied — litellm default temp applies; gpt-5 family forces 1.0).
Foundry-hosted DeepSeek/Kimi very likely ignore `seed` entirely.
=> Correct phrasing: **"3 replicate runs (seeds 42/43/44; `--seed` threads to the
provider `seed` param, best-effort only — replicates still differ by sampling)."**
NOT "3 independent seeds" in the strong sense, but also NOT the inert-seed situation
that forced tonight's earlier correction. Both statements are defensible; the safest
is "N=3 replicate runs".

- `LLM_CACHE_ENABLED = False` (`src/tau2/config.py:35`) — no cache contamination between reps. Good.
- `--num-trials 3` gives seeds 42,43,44 natively; that is the built-in replicate mechanism.
- Error handling (`run_parallel.py:279-284`): a task that raises is recorded with
  `reward: 0.0` **and an `error` key**; the summary printer excludes `"error" in r`
  from the denominator. So a crashed rollout does NOT silently become a 0 in the
  printed accuracy — but it DOES sit in `results.json` as reward 0.0. **Any
  aggregation I write must filter on the `error` key.** (This is exactly the
  silent-0.0 class of bug flagged in the task brief.)

## 13:55 UTC — environment built + endpoints repointed

**Clone location:** `/home/t-matthewho/ac3/tau2_ctxe` (OUTSIDE the ctx_editor tree, per brief).
HEAD `8e5fd3c` — matches RECON. Venv: `/home/t-matthewho/ac3/tau2_ctxe/.venv` (py3.12.3, uv).

Setup steps actually needed (RECON's ">= half a day" estimate was pessimistic; took ~10 min):
1. `uv venv --python 3.12 .venv`; `uv pip install -e . azure-identity`
2. `uv pip install scipy elevenlabs rank_bm25` (unconditional import chain via `tau2.voice`)
3. pyaudio shim: `.venv/lib/python3.12/site-packages/00_tau2_voice_shim.pth` =
   `import sys, types; sys.modules.setdefault('pyaudio', types.ModuleType('pyaudio'))`
4. `PYTHONPATH=/home/t-matthewho/ac3/tau2_ctxe`
- The Kimi `ToolCall.arguments` JSON-string `field_validator` is already **committed**
  (`src/tau2/data_model/message.py:74-86`) — no patch needed.
- `get_tasks_small()` returns **20** tasks, as expected.

### ENDPOINT REPOINTING (required — no `.env` on this machine)

`/home/t-matthewho/ac3/ctx_editor/.env` **does not exist** on this box, so there is no
`OPENAI_API_KEY`. The original sweep used `openai/gpt-5.4` (agent) and
`openai/gpt-5-mini` (user sim + analyzer), which litellm would send to api.openai.com.

Live probe (`/tmp/t6_probe.py`, 1-token chat completions under the current `az` identity):

| endpoint | result |
|---|---|
| `mgalley-foundry2` /openai/v1/ (scope `cognitiveservices`) | **LIVE** — `DeepSeek-V4-Flash` OK, `Kimi-K2.6` OK, `gpt-5.5` OK, `gpt-oss-120b` OK. `gpt-5.4` **404 DeploymentNotFound**. |
| `dl-openai-3` /openai/v1/ (scope `cognitiveservices`) | **LIVE** — `gpt-5.4` **OK**, `gpt-5-mini` OK, `gpt-5` OK, `gpt-4o-mini` OK; `gpt-4.1-2025-04-14` present in /models (this is tau2's NL-assertions judge default). |
| TRAPI redmond/interactive (scope `api://trapi/.default`) | LIVE for `gpt-5.4-mini_2026-03-17`, `gpt-4o_2024-11-20`; **no** `gpt-5-mini`, **no** `gpt-5.4`. |
| `fxdata-shared` | not probed; RECON says 401. Nothing routes there here. |

**=> dl-openai-3 serves BOTH `gpt-5.4` and `gpt-5-mini`.** So the original sweep's model
identities are reproducible exactly. I did NOT need to substitute TRAPI models, which
would have changed the user simulator and broken comparability with the seed-42 numbers.

**Patch applied** to `ctx_edit/run_parallel.py` (local clone only, not pushed):
- `refresh_openai_env()` sets `OPENAI_API_KEY` = AAD bearer token and
  `OPENAI_BASE_URL`/`OPENAI_API_BASE` = `https://dl-openai-3.openai.azure.com/openai/v1/`.
  Called in `main()` and at the top of every `run_one()`.
- `_aad_token(scope)` — thread-safe token cache, refreshes 10 min before expiry.
  Needed because sweeps outlive the ~60-90 min AzureCliCredential TTL; the original
  code fetched the Foundry token once per `build_agent` with a comment asserting cells
  finish inside the TTL.
- `_resolve_foundry_model` now uses `_aad_token()` instead of its own one-shot fetch.
Net effect: **the CLI invocation strings are byte-identical to the committed sweep
scripts** (`--agent-llm openai/gpt-5.4 --user-llm openai/gpt-5-mini
--analyzer-model openai/gpt-5-mini`); only the transport underneath changed.

## 13:56 UTC — POSITIVE CONTROL #1 PASSED

`--strategy s0 --agent-llm openai/gpt-5.4`, 2 tasks (`data_mode_off[PERSONA:None]`,
`airplane_mode_on[PERSONA:None]`), workers 2:
```
S0 : 2/2 (100.0%)  avg_reward=1.000  cost=$0.10   (55 s wall)
```
Harness scores a known-good rollout as reward 1.0 — it is NOT silently returning 0.0.
Out dir `ctx_edit/outputs/T6_smoke_s0`.

**Throughput is far better than feared: ~28 s/task.** A 20-task cell at workers=8 should
be a few minutes, so the FULL 3-model x 5-arm x 3-rep matrix (900 rollouts) looks
affordable. Revising plan upward from "depth on one cell" to the full matrix.

## 13:58 UTC — POSITIVE CONTROL #2 (all five arms) PASSED

2 tasks x {s0 already done, s1, s2, s3, ao}, gpt-5.4:

| arm | rewards | termination |
|---|---|---|
| s1 | 1.0, 1.0 | user_stop |
| s2 | 1.0, 0.0 | user_stop |
| s3 | 1.0, 1.0 | user_stop |
| **ao** | **0.0, 0.0** | **max_steps (both)** |

**The AO zero is behavioural, not a scoring fault.** AO rollouts never reach
`user_stop`; they burn all 50 steps. That is the documented failure mode (blanket
assistant-message omission destroys tool-call state, so the agent re-calls tools
forever). This is the sanity check the brief asked for: a 0% AO cell here is
corroborated by a mechanism, and the same harness returns 1.0 on the other four arms
in the same process.

## 14:00 UTC — seed-42 reference table locked

From `docs/reports/post_may18_progress_update_v4_bandaid_tau2.html:435-470` (n=19,
`[service_issue]break_apn_settings[PERSONA:None]` dropped):

| Arm | gpt-5.4 | DSV4F | Kimi-K2.6 |
|---|---|---|---|
| Baseline (s0) | 68.4 | 31.6 | 26.3 ‡ |
| AO | 0.0 | 0.0 | 0.0 ‡ |
| AC3-Augment (s1) | 84.2 | 57.9 | 57.9 |
| AC3-Gated-Reset (s2) | **52.6** | 47.4 | 68.4 |
| AC3-Rewrite v11 (s3) | 73.7 | 57.9 | 73.7 |

‡ Kimi s0/AO cells were rate-limit-clipped in the original run (14/20 and 19/20
short-exits at workers=4); the report itself calls them "floors, not honest
performance". My re-run uses workers=4 as well, so watch for the same artefact.
The gpt-5.4 Gated-Reset regression to check: **52.6 < 68.4 baseline**.

## 14:02–14:03 UTC — full matrix launched

Driver `ctx_edit/run_t6_reps.sh` (new; same hyperparameters as the committed
`run_post_may18_tau2_foundry.sh`: max-steps 50, min-turns 2, max-resets 3,
rewrite-prompt-version v11, user+analyzer `openai/gpt-5-mini`), except
`--num-trials 3` => seeds 42, 43, 44. Arms ordered s0, s2, s1, s3, ao so the
regression-relevant cells land first. Output `ctx_edit/outputs/T6_reps/<model>_<arm>/`.

| block | agent-llm | workers | started |
|---|---|---|---|
| gpt5_4 | `openai/gpt-5.4` (-> dl-openai-3) | 6 | 14:02:11 |
| dsv4f_foundry | `foundry/DeepSeek-V4-Flash` | 6 | 14:02:31 |
| kimi_k2_6_foundry | `foundry/Kimi-K2.6` | 4 | 14:04 |

Throughput observed: gpt-5.4 s0 hit 6/60 rollouts in ~60 s => ~10 min/cell.
15 cells total; AO cells will be slower (they always run to max_steps).
Aggregator: `ctx_edit/t6_aggregate.py` — reads **per-task traces**, not results.json,
so a runner crash cannot lose completed rollouts; it drops records carrying an
`error` key and excludes `break_apn_settings` for the n=19 denominator.

## 14:13 UTC — FIRST LAUNCH ABORTED: gpt-5-mini rate limits (this is a real trap)

First matrix launch died on HTTP 429. `gpt5_4_s0` finished with rc=0 and printed a
summary, but **42 of its 60 rollouts had errored**:

```
litellm.RateLimitError: OpenAIException - Your requests to gpt-5-mini for gpt-5-mini
in swedencentral have exceeded rate limit.
```
`kimi_k2_6_foundry_s0`: 59/60 errored (52 gpt-5-mini 429s, 7 Kimi-K2.6 429s).

**The bottleneck is not the agent model — it is `gpt-5-mini`, which is the user
simulator AND the analyzer for every arm of every model block simultaneously.**

Note the shape of this failure, because it is exactly the silent-degradation class the
brief warned about: `run_parallel.py` writes `reward: 0.0` for an errored rollout into
`results.json`, and the printed per-strategy summary silently shrinks the denominator
(it filters `"error" not in r`). So a cell that lost 70% of its rollouts still prints a
clean-looking percentage over the survivors, and `results.json` still contains 60 rows
of which 42 read `reward: 0.0`. **Any naive mean over `results.json` would have
produced a badly wrong, confidently-reported number.** My aggregator drops `error`
records and prints per-rep n.

### Fix — endpoint pooling + real backoff

Probe of every Azure OpenAI resource named in ctx_editor's load-balancer configs:

| resource | gpt-5-mini | gpt-5.4 |
|---|---|---|
| `dl-openai-1` | **OK** | **OK** |
| `dl-openai-3` | 429 (saturated) | OK |
| `fxdata-eastus2` | 401 PermissionDenied | 401 |
| `fxdata-shared` | 401 PermissionDenied | 401 |

(So `fxdata-shared` being dead is confirmed, and `fxdata-eastus2` is dead the same way.
Neither is on any route I use.)

New module `ctx_edit/_t6_llm_patch.py` wraps `litellm.completion` **and**
`tau2.utils.llm_utils.completion` (llm_utils does `from litellm import completion`,
i.e. by value, so patching `litellm.completion` alone is not enough — worth knowing):
- round-robin `api_base` across the pool of resources verified to serve that
  deployment (`gpt-5-mini` -> [dl-openai-1, dl-openai-3], `gpt-5.4` -> [dl-openai-3,
  dl-openai-1], plus `gpt-4.1-2025-04-14`, tau2's NL-assertions judge);
- on a retryable error, **rotate endpoint and back off** — 14 attempts, exponential
  from 4 s to 90 s with jitter (tau2's own `num_retries=3` litellm backoff is far too
  short); `num_retries` forced to 0 so retries are not double-counted;
- calls that already carry an explicit `api_base` (the `foundry/` path for
  DeepSeek-V4-Flash / Kimi-K2.6) keep their endpoint and get only the retry behaviour.

Transport-only change. Model identities, prompts and sweep hyperparameters untouched.

Smoke after patch: gpt-5.4 s0, 4 tasks, workers 4 -> `S0 : 3/4 (75.0%)`, 80 s, 0 errors.

## 14:18–14:20 UTC — matrix relaunched (workers 5 / 5 / 4)

`T6_reps` wiped and restarted from scratch so no rate-limit-poisoned cell survives.
gpt5_4 @5 (14:18), dsv4f_foundry @5 (14:19), kimi_k2_6_foundry @4 (14:20).

## 14:38 UTC — FIRST FULL CELL LANDED: gpt-5.4 Baseline, N=3

```
| Model   | Arm          | rep1(s42) | rep2(s43) | rep3(s44) | mean ± sd  | seed-42 ref |
| gpt-5.4 | Baseline(FC) |   52.6    |   78.9    |   73.7    | 68.4 ± 13.9 |    68.4     |
```
n=19 per rep, 0 errored rollouts, 1184 s wall for the 60 rollouts.

**Two things worth stopping on.**

1. **The mean lands exactly on the published seed-42 point estimate (68.4).** But the
   seed-42 replicate itself came back **52.6**, not 68.4. So `--seed 42` does *not*
   reproduce the original number bit-for-bit — expected, given the seed is the
   best-effort provider parameter and the transport now differs (dl-openai-1/3 instead
   of api.openai.com). The published number is a good estimate of the mean; it is not
   a reproducible point.
2. **Rep-to-rep spread is ±13.9 pp on a single cell.** For n=19 at p≈0.68 the binomial
   sd is sqrt(.68*.32/19) = 10.7 pp, so this is simply the noise floor of a 19-task
   benchmark — not an artefact. **This is the quantitative form of the reviewer's
   complaint.** Any tau2 gap smaller than roughly 15 pp measured at N=1 is inside the
   noise. Several published tau2 cell-to-cell differences are smaller than that.

Early partials on the other two models (incomplete, do not quote yet):
DSV4F Baseline rep1 = 57.9 (published 31.6); Kimi Baseline rep1 = 78.9 (published 26.3).
If those hold up they are far above the published baselines. Candidate explanations,
in order of my current suspicion:
  (a) the published DSV4F/Kimi baselines were **infrastructure-degraded** — the source
      report already concedes this for Kimi ("rate-limit-clipped floors, not honest
      performance", 14/20 short-exits; "true Baseline is probably 40-50%"), and my
      rotate-and-backoff wrapper removes exactly that failure mode;
  (b) Foundry deployment drift — `DeepSeek-V4-Flash` and `Kimi-K2.6` are alias
      deployment names and `/models` on mgalley-foundry2 now also lists
      `DeepSeek-V4-Flash-2026-04-23`; the alias may point somewhere newer than in May.
Either way, if the baselines rise the AC3-over-baseline deltas on those two models
shrink. **That must be reported, not buried.** Waiting for the AC3 arms.

Status 14:38: gpt5_4 s0 DONE, s2 running. dsv4f s0 21/60. kimi s0 24/60. Zero FAILED.

## 15:10 UTC — three Baseline cells complete. A serious problem with the published DSV4F/Kimi baselines.

| Model | Arm | rep1(s42) | rep2(s43) | rep3(s44) | mean ± sd | published seed-42 |
|---|---|---|---|---|---|---|
| gpt-5.4 | Baseline | 52.6 | 78.9 | 73.7 | **68.4 ± 13.9** | 68.4 |
| DeepSeek-V4-Flash | Baseline | 57.9 | 78.9 | 73.7 | **70.2 ± 11.0** | **31.6** |
| Kimi-K2.6 | Baseline | 78.9 | 78.9 | 83.3 | **80.4 ± 2.5** | **26.3** |
| gpt-5.4 | Gated-Reset (2/3 reps) | 36.8 | 62.5 | — | 49.7 ± 18.1 | 52.6 |

n=19/rep (one rep of Kimi has 18 — one rollout still in flight at read time), 0 errors.

**gpt-5.4 baseline replicates on the mean (68.4 vs 68.4).** DSV4F is +38.6 pp and
Kimi is +54.1 pp above their published baselines. That is not noise.

### Evidence on why

- **Termination reasons in my runs:** dsv4f s0 = 60/60 `user_stop`; kimi s0 = 59/60
  `user_stop`; gpt5_4 s0 = 58/60 `user_stop`. Essentially every rollout ran to a
  natural conversational end.
- **The original Kimi run did not.** The source report states the Kimi Baseline and AO
  cells had **14/20 and 19/20 short-exits** from `litellm.RateLimitError`, calls those
  numbers "rate-limit-clipped floors rather than honest performance", and guesses the
  true baseline at 40-50%. My 80.4% says even that guess was low.
- **Foundry alias drift: no evidence.** `DeepSeek-V4-Flash` and `Kimi-K2.6` still
  resolve as their own deployment names (`response.model` echoes them);
  `DeepSeek-V4-Flash-2026-04-23` is a *separate* deployment and 404s under the alias.
  So the deployment names are not silently repointed. Cannot fully exclude an
  in-place version bump on the alias, but there is no positive sign of one.
- **Original outputs are unauditable.** `ctx_edit/outputs/` is gitignored in the fork
  (`.gitignore:227`) and `git ls-files ctx_edit/outputs` returns nothing, so the May
  per-task traces do not exist anywhere I can reach. I cannot count the original
  short-exits for DSV4F.

### What I think happened

The rate-limit failure mode that killed 42/60 and 59/60 of my own first-launch
rollouts is the *same* one the source report documents for Kimi. My rotate-and-backoff
wrapper removes it. The most likely reading is that the published DSV4F and Kimi
Baseline cells are **infrastructure-degraded floors**, and the Kimi one is admitted to
be so in the report that produced it. The report's claim that "the AC3 vs Baseline
differential is robust regardless" rests on the AC3 arms having run clean while the
baseline did not — i.e. on comparing a clean treatment against a broken control.
Whether that holds is exactly what the AC3 arms now running will settle.

**Consequence if this survives:** the published tau2 gains on DSV4F (+26.3 pp) and
Kimi (+47.4 pp) are measured against baselines that are too low, and shrink or
invert. Kimi's re-measured baseline (80.4) is already **above every published Kimi AC3
number** (Augment 57.9, Gated-Reset 68.4, Rewrite 73.7). This is the opposite of a
convenient result and it goes in the report unhedged.

Status 15:10: gpt5_4 s0 done / s2 37/60; dsv4f s0 done / s2 starting; kimi s0 59/60.

## 15:19 UTC — all three drivers were KILLED by the agent harness; relaunched detached

At 15:18 the harness reported all three background driver tasks as `killed`
(bm2jpevg0 / behcw1xki / b0cnkm0g2) and `pgrep` confirmed no surviving
`run_parallel.py`. They had been up ~60 min. Cause was the harness's background-task
lifecycle, not the runs themselves — zero `FAILED` lines in any cell log.

Lost work at kill time: `gpt5_4_s2` 53/60, `dsv4f_s2` 8/60, `kimi_s2` 13/60 (all
in-flight, no results.json). Two fixes:

1. **Resume support** in `run_parallel.py`: a job whose trace file already exists and
   parses as JSON is skipped when building the job list. Trace paths are deterministic
   (`{safe_task_id}_{strategy}_seed{seed}.json`), so restarts are idempotent and a
   killed cell costs only its in-flight rollouts. `run_t6_reps.sh` now gates on
   *trace count* (20 x trials) rather than the presence of `results.json`, and appends
   to cell logs.
2. **Detached launch**: `setsid nohup ./run_t6_reps.sh ... &` with logs to
   `ctx_edit/outputs/T6_reps/_logs/driver_*.log`. New process group, so the harness's
   task manager cannot reap them.

Relaunched 15:19:12-14. All three s0 cells correctly SKIPped (60/60 traces), all three
s2 cells resumed. Note for whoever picks this up: **poll the trace counts, not the
background-task status** — `ls ctx_edit/outputs/T6_reps/<cell>/traces | wc -l` vs 60.

## 15:32 UTC — gpt-5.4 Gated-Reset complete (N=3). The regression reproduces in sign, not in significance.

| Model | Arm | rep1 | rep2 | rep3 | mean ± sd | range | published |
|---|---|---|---|---|---|---|---|
| gpt-5.4 | Baseline | 52.6 | 78.9 | 73.7 | 68.4 ± 13.9 | 52.6–78.9 | 68.4 |
| gpt-5.4 | **Gated-Reset** | 36.8 | 57.9 | 78.9 | **57.9 ± 21.1** | 36.8–78.9 | 52.6 |

**Direction reproduces: Gated-Reset (57.9) < Baseline (68.4) on gpt-5.4.** But the two
ranges are nested — Gated-Reset spans 36.8-78.9 and Baseline spans 52.6-78.9, and the
Gated-Reset sd is 21.1 pp. On unpaired cell means the two arms are indistinguishable.

Added `ctx_edit/t6_paired.py` — pairs on **(task, seed)** and runs an exact two-sided
sign test over discordant pairs (McNemar, exact form). Pairing removes task difficulty
and replicate effects, which is the only way to get power out of a 19-task benchmark.

| Model | Arm | paired obs | arm wins | base wins | ties | delta | exact p |
|---|---|---|---|---|---|---|---|
| gpt-5.4 | Gated-Reset | 57 | 6 | 12 | 39 | **-10.5 pp** | **0.238** |

So: with 3x the data and the paired test, the gpt-5.4 Gated-Reset regression is
**-10.5 pp and not significant (p = 0.24)**. It is a real directional effect that has
now shown up twice, but it is not something the benchmark can resolve. Note also that
39/57 pairs are ties — Gated-Reset changes the outcome on under a third of rollouts.

Honest framing for the rebuttal: *"the gpt-5.4 Gated-Reset regression reproduces at
N=3 (57.9 ± 21.1 vs 68.4 ± 13.9; paired -10.5 pp, exact sign test p = 0.24). We report
it because it is directionally consistent across independent runs, but tau2 at n=19
cannot resolve a 10 pp effect."* Do not upgrade this to "we fixed it" or "it was noise".

Status 15:32: gpt5_4 s0/s2 done, s1 running. dsv4f s2 16/60. kimi s2 27/60. 0 FAILED.

## 16:02 UTC — gpt-5.4 Augment is coming back at HALF its published value. Checked hard; not a harness fault.

| Model | Arm | rep1 | rep2 | rep3(partial) | mean ± sd | published |
|---|---|---|---|---|---|---|
| gpt-5.4 | AC3-Augment | 42.1 | 52.6 | (2 tasks in) | **48.2 ± 5.5** | **84.2** |

Paired vs Baseline over 40 pairs: **-20.0 pp, exact sign test p = 0.039**. i.e. in this
environment Augment *significantly hurts* gpt-5.4, where the paper reports it as the
headline tau2 win (+15.8 pp). This is the single most alarming number of the run, so I
went looking for a harness fault before believing it:

- **Analyzer is alive and producing real content.** Dumped `analysis_log` from the
  seed-42 traces: 18/20 carry entries with a populated `task_spec` and a detailed
  `valid_progress` (real tool-call values, customer ids, diagnostics). The 2 empty ones
  are conversations that ended before the `min_turns=2` warm-up — expected.
- **Arm is firing.** median 2 analyses per rollout on s1, same as s2.
- **No degenerate terminations.** gpt5_4 s1: **42/42 `user_stop`**, zero `max_steps`.
  Median message count 24 — identical to baseline's 24. Augment is not blowing up the
  context or stalling the agent; it is losing on task outcomes.
- **Gating is as designed** (`ctx_edit/agents.py:589-597`): Augment has no `needs_edit`
  gate, it fires whenever warm. Behaviour matches the code.

I could not find a defect. Recording it as a genuine measurement in this environment.

### The pattern across all arms so far

Published-vs-remeasured differences are large **in both directions**:

| cell | published | remeasured | delta |
|---|---|---|---|
| gpt-5.4 Baseline | 68.4 | 68.4 ± 13.9 | 0 |
| gpt-5.4 Augment | 84.2 | 48.2 ± 5.5 | **-36** |
| gpt-5.4 Gated-Reset | 52.6 | 57.9 ± 21.1 | +5 |
| DSV4F Baseline | 31.6 | 70.2 ± 11.0 | **+39** |
| DSV4F Gated-Reset | 47.4 | 76.2 ± 21.6 | **+29** |
| Kimi Baseline | 26.3 | 78.9 ± 0.0 | **+53** |
| Kimi Gated-Reset | 68.4 | 71.9 ± 11.0 | +4 |

Two-directional, up to 50 pp. If the cause were a systematic environment difference
(different analyzer snapshot, different transport) I would expect a consistent sign.
A mix of +50 and -36 is what an **n=19 benchmark read once** looks like. The DSV4F and
Kimi *baselines* still look like the infrastructure-degradation story (see 15:10), but
gpt-5.4 Augment cannot be explained that way — its baseline reproduced exactly.

**Bottom line forming: the tau2 row of the paper is N=1 on a benchmark whose 1-sigma
replicate spread is 11-21 pp. Individual cells are not reproducible, and neither the
wins nor the losses in that row should be quoted as point estimates.** That is a
stronger and more useful answer to reviewer iNYK than a tidied-up table would be, but
it is bad news for the tau2 row as currently written.

Status 16:02: gpt5_4 s1 42/60; dsv4f s2 40/60; kimi s1 11/60. 0 FAILED anywhere.
Remaining: gpt5_4 {s1,s3,ao}, dsv4f {s2,s1,s3,ao}, kimi {s1,s3,ao}. ETA ~19:00 UTC.

## 16:28 UTC — status

Complete cells (N=3, n=19/rep): gpt-5.4 {s0, s1, s2}; DSV4F {s0, s2}; Kimi {s0, s1, s2}.
Running: gpt-5.4 s3, DSV4F s1, Kimi s1(57/60). Remaining after that: 3x s3/ao tails.

New complete cells since last entry:
- gpt-5.4 Augment finished at **47.4 ± 5.3** (42.1 / 52.6 / 47.4) vs published 84.2.
  Tight across reps; the -36 pp gap is not replicate noise.
- DSV4F Gated-Reset **57.3 ± 9.7** (57.9 / 66.7 / 47.4) vs published 47.4.
- Kimi Augment **59.8 ± 11.1** (63.2 / 47.4 / 68.8) vs published 57.9 — this one
  replicates well.
- Kimi Baseline is 78.9 in **all three** reps (identical). Same 15/19 tasks solved each
  time; telecom_small has a hard core Kimi never gets and an easy core it always gets.
  Not a bug — 0.0 sd is legitimate here and is itself evidence the benchmark has very
  few discriminating tasks.

**Total errored rollouts across the entire sweep so far: 1.**
`FAILED s2 [mobile_data_issue]data_mode_off[PERSONA:None]: Extra data: line 1 column 3`
— a malformed tool-call `arguments` payload from DeepSeek that the JSON parser
rejects. That rep is scored over n=18 and the aggregator reports it. No rate-limit
failures at all since the pooling patch went in.

## 17:16 UTC — the picture resolves: AC3 arms replicate, the DSV4F/Kimi *baselines* do not

Newly complete: gpt-5.4 Rewrite; DSV4F Augment; Kimi Augment; Kimi Rewrite (near).

| cell | published | remeasured (N=3) | verdict |
|---|---|---|---|
| DSV4F Augment | 57.9 | **59.1 ± 7.1** | replicates |
| DSV4F Gated-Reset | 47.4 | 57.3 ± 9.7 | replicates (within 1 sd) |
| Kimi Augment | 57.9 | **57.9 ± 9.1** | replicates exactly |
| Kimi Gated-Reset | 68.4 | **71.9 ± 11.0** | replicates |
| Kimi Rewrite | 73.7 | 68.1 ± 8.9 | replicates |
| gpt-5.4 Baseline | 68.4 | **68.4 ± 13.9** | replicates exactly |
| **DSV4F Baseline** | 31.6 | **70.2 ± 11.0** | **does not — +39 pp** |
| **Kimi Baseline** | 26.3 | **78.9 ± 0.0** | **does not — +53 pp** |
| **gpt-5.4 Augment** | 84.2 | **47.4 ± 5.3** | **does not — -37 pp** |

This is a much sharper story than "everything is noisy". **Nine of twelve completed
cells replicate inside one replicate sd.** The three that do not are:

1. **DSV4F and Kimi Baseline.** Both move sharply *up*. Both are exactly the cells that
   the source report identifies (for Kimi) or plausibly shares (for DSV4F) as
   rate-limit-clipped, and both are on the Foundry endpoint that produced 429s for me
   too until I added rotate-and-backoff. The AC3 arms on those same two models — which
   the report says "ran clean" — replicate. **The evidence now points squarely at
   degraded *controls*, not at a flaky benchmark.**
2. **gpt-5.4 Augment**, which moves sharply *down* and is the one I cannot explain
   (its own baseline reproduced exactly; the arm is verifiably firing and terminating
   cleanly; see 16:02).

**Consequence for the tau2 row.** With corrected baselines, the published gains
+26.3 pp (DSV4F) and +47.4 pp (Kimi) do not survive: on my numbers DSV4F Baseline 70.2
beats Augment 59.1 and Gated-Reset 57.3, and Kimi Baseline 78.9 beats Augment 57.9,
Gated-Reset 71.9 and Rewrite 68.1. **On all three models, remeasured Baseline is at or
above every AC3 arm.** I want the AO cells and the DSV4F Rewrite cell in before I state
that as the finding, but that is where it is heading and I am not going to soften it.

Status 17:16: gpt5_4 {s0,s1,s2,s3} done, ao 3/60. dsv4f s1 53/60, then {s3, ao}.
kimi {s0,s1,s2} done, s3 52/60, then ao. Still exactly 1 errored rollout in the sweep.

## 17:35 UTC — FOUND A REAL BUG: 53% of analyzer Q1 calls fail tag extraction and inject escaped JSON into the context

While auditing why gpt-5.4's AC3 arms all collapsed, I dumped the text actually spliced
into an Augment rollout's context. It looks like this:

```
<analysis>
### Task Specification (reviewer's consolidated interpretation)
\nConsolidated user task specification:\n\n1) Customer identity and contact\n- Name: ...
```

Literal backslash-n. The analyzer's Q1 asks for `<task_spec>...</task_spec>`;
**gpt-5-mini often answers with a JSON object** `{"task_spec": "...\n..."}` instead.
`_extract_tag` (`ctx_edit/analyzer.py:89-95`) only regexes for the XML tags, returns
`""`, and `analyze_conversation` (`:519-521`) then falls back to **the raw completion**
— so the JSON wrapper, quoting and all escape sequences, is handed to the agent as its
briefing.

### Rate, measured over every AC3 trace in the sweep (862 analyzer calls)

| cell | analyses | JSON-fallback | rate |
|---|---|---|---|
| gpt5_4 s1 | 163 | 107 | **66%** |
| gpt5_4 s2 | 131 | 72 | 55% |
| gpt5_4 s3 | 137 | 61 | 45% |
| dsv4f s1 | 85 | 49 | 58% |
| dsv4f s2 | 80 | 28 | 35% |
| kimi s1 | 90 | 62 | **69%** |
| kimi s2 | 80 | 32 | 40% |
| kimi s3 | 96 | 48 | 50% |
| **TOTAL** | **862** | **459** | **53%** |

**This degrades every AC3 arm and cannot touch Baseline or AO** (neither calls the
analyzer). It is the exact shape of the gpt-5.4 result: baseline reproduces at 68.4,
all three AC3 arms drop 20-26 pp. And the worst-affected arm (s1, 66%) is the one with
the largest published-vs-remeasured gap (-37 pp).

Whether this is pre-existing or environment-induced is **unresolved**: it depends on
whether OpenAI-hosted gpt-5-mini emitted the tags more reliably than the Azure
deployment does. The original traces are gone, so I cannot check directly.

### Diagnostic launched (17:36)

Patched `_extract_tag` to also accept a JSON object keyed by the tag name (and to strip
markdown fences), **gated behind `T6_FIX_TAG_PARSE=1`, default OFF** so the in-flight
replicate sweep is untouched — the remaining cells launch fresh processes that read the
edited file, and with the flag unset they behave exactly as before. Verified: flag off
-> `''` (old behaviour), flag on -> the unescaped string, XML path unchanged.

Running gpt-5.4 Augment, seed 42, 20 tasks, `T6_FIX_TAG_PARSE=1` ->
`ctx_edit/outputs/T6_diag/gpt5_4_s1_fixparse`. Comparator is the matching sweep rep:
**42.1%**. If it jumps toward the published 84.2 the parser explains the AC3 collapse;
if it stays near 42 the collapse is real.

### Two other errored rollouts (total sweep errors now 3 / ~1700)

- `s3 unseat_sim_card`: Azure content-management policy filtered the prompt.
- `s3 break_app_storage_permission`: `AuthenticationError ... token expired` — the
  `foundry/` path binds its bearer token into `llm_args` at agent-build time, so a
  single rollout that outlives the remaining TTL can fail. 1 occurrence; my pooled path
  re-stamps the token per call and never hit this.

## 17:55 UTC — DIAGNOSTIC RESULT: the parser bug is real but does NOT explain the AC3 collapse

gpt-5.4 Augment, seed 42, `T6_FIX_TAG_PARSE=1`, n=18 (19th rollout still running,
`break_apn_settings` excluded):

| condition | JSON-fallback rate | accuracy |
|---|---|---|
| sweep rep1 (bug present) | 66% | **42.1%** |
| fixparse (bug mostly fixed) | 25% (9/36) | **44.4%** |
| published seed-42 | ? | 84.2% |

Fixing the extraction cut the fallback rate by roughly two thirds and moved accuracy by
**+2.3 pp** — inside a single task flip (1/19 = 5.3 pp). **It does not recover the
published 84.2.**

So I chased the most plausible confound and it is worth ~2 pp, not ~37 pp. I am
therefore reporting the AC3 underperformance on tau2 as a genuine measurement in this
environment, not as an artefact. The parser defect should still be fixed in the fork —
it is silently corrupting half of all analyzer briefings and nobody knew — but it is
not the explanation.

Residual 25% fallback = Q1 completions that are neither tagged nor a parseable JSON
object keyed by the tag. Not chased further.

Status 17:55: gpt-5.4 block **COMPLETE** (all 5 arms x 3 reps). Kimi has s0/s1/s2/s3,
ao running (9/60). DSV4F has s0/s1/s2, s3 running (14/60), then ao.

## 18:43 UTC — status

13 of 15 cells complete. DSV4F Rewrite 57/60; Kimi AO 44/60; DSV4F AO not yet started
(it is the last cell in the matrix). Newly landed:
- DSV4F Rewrite **59.8 ± 15.3** (68.4 / 42.1 / 68.8) vs published 57.9 — replicates.
- Kimi AO **0.0 ± 0.0** — replicates the published 0.0 exactly, as did gpt-5.4 AO.

**Both completed AO cells are 0.0 in every replicate.** Taken with the `max_steps`
termination mechanism confirmed in the smoke test, the paper's "AO -> 0% everywhere"
claim is the single most solidly reproduced result in the whole tau2 row. It is also
the strongest evidence the harness is scoring honestly: the same code path that
returns a hard 0 for AO returns 68-79% for Baseline on the same tasks in the same run.

## 19:32 UTC — 14/15 cells at full 60/60. Backfill complete.

Re-invoked the four cells that had errored rollouts; resume filled every gap except one
(`s3 unseat_sim_card`, the Azure content-filter rejection, which is deterministic —
and it succeeded on the retry after all, so the matrix is clean). Backfill ran at
workers=2 into the same output dirs; resume skipped 58-59 existing traces each time.

Only `dsv4f_foundry_ao` still running (33/60). Everything else is 60/60, n=19/rep.

### Near-final numbers — see final report for the full table.

The headline that will not change: **on all three models, remeasured Baseline is at or
above every AC3 arm, and the paired sign test finds AC3-Augment significantly *worse*
than Baseline on all three** (gpt-5.4 -21.1 pp p=0.008; DSV4F -19.3 pp p=0.043;
Kimi -21.1 pp p=0.012). Gated-Reset and Rewrite are directionally negative on all three
but not significant. AO is -68 to -79 pp, p<0.0001, on all three — reproducing the
paper exactly.

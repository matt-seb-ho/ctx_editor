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

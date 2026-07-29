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

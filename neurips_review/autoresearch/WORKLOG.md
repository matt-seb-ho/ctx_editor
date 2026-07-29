# Central Work Log — NeurIPS Rebuttal Autoresearch (Sub. 27902)

Protocol: `Deli_AutoResearch` (see `/home/t-matthewho/misc/deli_autoresearch_skill.md`). Zero-interaction; state lives in files, not conversation.

- **Spec:** [`state/task_spec.md`](state/task_spec.md)
- **Provenance graph:** [`PROVENANCE.md`](PROVENANCE.md)
- **Machine state:** `state/progress.json`, `state/findings.jsonl`, `state/iteration_log.jsonl`
- **Sub-agent logs:** `tasks/<ID>/worklog.md` — linked from each entry below.
- **Predecessor log** (2026-07-27 session): [`../worklog.md`](../worklog.md)

Newest entries at the bottom of each section.

---

## Session 2 — 2026-07-29

**Operator:** asleep from ~09:45 PT, then on other work. No blocking questions.
**Model policy:** `gpt-5.4-mini_2026-03-17` on TRAPI `redmond/interactive` (primary, free); `gpt-5.2` on `dl-openai-1` for escalation only.

### Environment verification (main thread)

| Check | Result |
|---|---|
| `az` identity | `sc-hy6197645@microsoft.com`, sub "Deep Learning Group" |
| TRAPI `gpt-5.4-mini_2026-03-17` chat completion | **OK** |
| TRAPI `gpt-4o_2024-11-20` chat completion | **OK** |
| Network (arxiv / github / huggingface / drive.google) | all reachable |
| `data/spider/databases/` | **MISSING** — blocks all LiC-database work |

Gotcha worth recording: `azure.identity.get_bearer_token_provider(...)` returns a **sync** callable, and passing it as `api_key=` to `openai.AsyncOpenAI` raises `TypeError: object str can't be used in 'await' expression` on the first call. Passing a plain token string works. (The repo's `azure_foundry` client path may or may not hit this — flagged for RECON.)

### Decisions

**D1 — Delegate everything but orchestration.** Operator asked for aggressive delegation. Main thread holds only: environment verification, the central log, the provenance graph, dispatch, and result integration. All experiment execution and codebase archaeology goes to subagents, each with its own worklog.

**D2 — Resolve the Spider blocker before committing to a task order.** `experiment_todos.md` names Spider SQLite DBs as "the single blocking dependency for the most valuable remaining work" (T1, T2, and a discriminating T5). Whether it resolves changes which venue T1/T2 run on, so it is dispatched first and in parallel with recon rather than serially.

**D3 — Recon before dispatch of T8/T9/T6.** The three highest-priority experiments all need harness invocations we do not currently have written down (CollabLLM competent-user-sim variant, analyzer-model override, tau2 seeds). Writing those prompts from guesswork would burn a subagent's whole run on archaeology. One recon agent produces the map once; every later agent reads it.

### Progress

- **09:30–09:45** Bootstrapped `neurips_review/autoresearch/` (state, logs, tasks). Verified TRAPI end-to-end.
- **09:45** Dispatched two agents in parallel:
  - `BLOCK-spider` — acquire + verify Spider SQLite DBs. Log: `tasks/BLOCK-spider/worklog.md`
  - `RECON` — map harnesses, operator-name→config mapping, prior-result inventory. Log: `tasks/RECON/worklog.md`

- **09:54** `BLOCK-spider` returned **SUCCESS**. Blocker cleared. Log: `tasks/BLOCK-spider/worklog.md`

### Findings

**F1 — Spider DBs recovered; LiC-database is unblocked.** `data/spider/databases/`, 4.9 GB, 29 db_id dirs, gitignored (`.gitignore:217 /data/`). Coverage is **17/17** — the union of `test_database_subset_t3.json`, `dev_database_subset.json` and `htn50_52_database_subset.json` needs exactly 17 db_ids, all Spider dev-split, all present.

Provenance matters here and should go in the camera-ready if we report database numbers. The DBs came from the `taoyds/test-suite-sql-eval` Google Drive bundle, identified via a surviving `readme.txt` in `blob_staging/supplementary.tar.gz` (whose own `spider/databases` symlink was dangling). This is the *right* bundle, not merely an available one: `eval_exec_match_sync` globs every `.sqlite` in the db dir and requires the predicted query to agree with gold on **all** of them — i.e. test-suite execution accuracy. The plain single-sqlite Spider dump would have silently changed the evaluation semantics relative to original LiC. Local disk, 9 HF datasets, and HF spaces were all empty first.

Verification: 5 gold queries across 5 db_ids all executed, returned non-empty rows, and scored `eval_exec_match_sync(gold, gold) = 1` across their full test suites; negative control `SELECT 1` correctly scored 0. A 3-sample end-to-end TRAPI run completed with real graded scores.

**F2 — Two harness gotchas that would have silently corrupted results.**
1. `unzip` must exclude `__MACOSX/*`. The eval's DB filter is `".sqlite" in basename` — a *substring* test, not a suffix test — so AppleDouble `._*.sqlite` sidecars get treated as real databases and trip the gold-query assert.
2. **Under `load_balancer=trapi`, the default `false_negative_analysis.model: gpt-5-mini` is not served, so FN analysis silently no-ops on every incorrect sample.** This is the dangerous one: it fails quietly and would deflate every TRAPI-run accuracy number relative to our existing FN-adjusted figures (cf. T4's "FN-adjusted" row). **Every TRAPI experiment this session must pass `false_negative_analysis.model=gpt-5.4-mini_2026-03-17`.** Verified working.

**F3 — `task.limit` is the sample-count config key.**

- **10:04** `RECON` returned. Log: `tasks/RECON/worklog.md`. Six findings, two of which change what we are allowed to claim.

**F4 — ⚠️ `seed=` is a no-op on LiC and CollabLLM. Our "N=3 seeds" language is wrong.** `cfg.seed` is read *only* by `huang_eval/`. Every `seed=$((42+rep))` in the LiC and CollabLLM launchers — **including T4's, from session 1** — was inert. Replicates varied through `temperature: 1.0` sampling alone. Worse, the CollabLLM loaders hardcode `random.Random(42)`, so all replicates draw the *same 20 problems*; Phase-3a Baseline scored 30.0/30.0/30.0 across "seeds", which is the signature of this bug rather than of a stable method.

Consequences, in order of severity:
1. **Wording.** For LiC and CollabLLM we must say "3 replicate runs at temperature 1.0", never "3 seeds". A reviewer who reads the launcher scripts will find this, and "seeds" would look like an overclaim. WildChat's N=3 *is* real seeding and can keep the word.
2. **Interpretation.** Temperature-only replication estimates decoder variance, not sampling variance over problems. Our error bars are therefore narrower than a true seed sweep's would be. This is a genuine limitation and belongs in the limitations appendix.
3. **Paper edit required.** Any "seeds" claim in `writing/overleaf_repo/` sourced from LiC/CollabLLM needs rewording. Queued as `PAPER-1` below; not actioned without the operator, since the paper repo is shared with collaborators.

**F5 — T8 would have failed at the judge step.** `fxdata-shared` returns 401 for this identity, and `multi_endpoint_foundry.yaml` routes `gpt-4o-mini` — the CollabLLM judge role — *only* there. Fix: add `gpt-4o-mini: 150` to the `dl-openai-3` block. `mgalley-foundry2` and `dl-openai-3` are both live (verified by single-token probe).

**F6 — The "missing" prior outputs are recoverable.** `~/ac3/blob_staging/snapshot.tar.gz` contains the whole `outputs/` tree, including the CollabLLM competent-user-sim dir and all WildChat runs. Selective-extract command is in the RECON worklog. (Spider was *not* in there — unrelated recovery path, see F1.)

**F7 — Analyzer override syntax for T9:** `model.ctx_editor.model=X`, verified. Two traps: the load balancer hard-fails on models not listed in `supported_models`, and gpt-4o inherits `reasoning_effort: medium` unless you also pass `model.ctx_editor.reasoning_effort=null`.

**F8 — Two documentation artifacts referenced by the paper do not exist.** `docs/paper_experiments_provenance.md` names configs `assistant_omit` and `concat_baseline` that are absent, and `docs/multi_run_variance_2026-05-07.md` — cited *twice* as the source of the paper's appendix variance table — does not exist. The variance table's provenance is currently unverifiable. Queued as `PAPER-2`.

**F9 — `analysis_cache` reuse is unsafe under an analyzer swap** (T9). The cache-key logic is unread; a stale hit would silently return the old analyzer's output and void the experiment. T9 must run with the cache disabled or key-verified.

### Action items for the operator (not actioned autonomously)

| ID | Item | Why it needs a human |
|----|------|----------------------|
| PAPER-1 | Reword LiC/CollabLLM "seeds" → "replicate runs (temperature 1.0)"; add the decoder-vs-sampling-variance caveat to limitations | Edits `writing/overleaf_repo/`, a shared repo synced to Overleaf |
| PAPER-2 | Appendix variance table cites a non-existent doc; re-derive or re-source | Same |

### Decisions (cont.)

**D4 — Report the seed bug rather than quietly relabelling.** Discovering that replicates were temperature-only is exactly the kind of thing that, if papered over, turns a borderline-reject into a desk-reject on integrity grounds. We reword the claims, state the limitation, and keep the numbers — they are still valid measurements of decoder variance, which is what the error bars will now say they are.


### Open questions / risks

- **R1:** TRAPI `max_concurrent: 20` is shared. If several experiment agents run at once, aggregate concurrency must stay under it or runs will throttle/fail. Mitigation: cap each dispatched run at `execution.max_concurrent=5` and never run more than 3 experiment agents concurrently.
- **R2:** The 2026-07-27 session's numbers in `replies/v4/` include several N=1 claims (CollabLLM 100%/20%, tau2 seed-42). Until T8/T6 land, those remain the paper's exposed surface.

- **09:50** Heartbeat tick. 3 agents in flight (T8, T2c, T12-T13) = concurrency cap; all <5 min old, no worklogs written yet, none stalled. No dispatch, no pivot. Queue behind them: T9, T2A, T1, T11, T6, T2B.
- **10:01** Heartbeat tick. All 3 agents healthy — worklogs for T8, T2c and T12-T13 all written and touched within the last 6 min, and live processes confirm real compute (`run_collabllm` on `collabllm_ac3_reset_v8` + `collabllm_baseline`, plus a `ctx-editor append_analysis` run). Still at cap; no dispatch, no pivot.

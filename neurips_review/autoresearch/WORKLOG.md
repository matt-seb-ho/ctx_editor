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
- **10:24** Heartbeat tick. Still 3 agents at cap, all live. Worklog ages T2c 11m / T12-T13 25m / T8 28m, all inside the 45-min stall threshold. Useful liveness signal beyond mtimes: the `run_collabllm` PIDs rotated since the 10:01 tick, so T8 is finishing replicates and relaunching rather than hanging on one. No dispatch, no pivot.
- **10:46** Heartbeat tick — **first intervention.** T12-T13's worklog crossed the 45-min staleness threshold (47m), but a process-level check showed it had launched two `append_analysis_memory` replay runs one minute earlier, so it was alive and working, just not logging. Nudged it to log incrementally rather than restarting. T8 (worklog 1m old, now on `collabllm_baseline` / bigcodebench) and T2c (20m) both healthy.

  **Rule refinement (D5):** worklog mtime alone produces false-positive stalls. Escalation is now two-stage — mtime > 45 min triggers a *process check*; nudge if a live process exists, restart only if there is neither a live process nor recent output writes. Naively restarting on mtime would have killed a healthy run mid-replicate.

- **11:00** `T2c` returned **DONE**. Logs: `tasks/T2c/worklog.md`, `tasks/T2c/RESULTS.md` (+ scripts and label files).

**F10 — The auditing interpretation survives on code and database, and must be conceded on math.** This is the answer to 5YHP's mechanism challenge, and it is stronger for being partial.

Analyzer text was already persisted (`traces/<task>/<strategy>/<sample>.json` → `conversation_analysis`, `context_edit_output.edited_context`), so no re-runs were needed. Venue: the paper's phase-1 LiC replay matrix (DeepSeek-V4-Flash, 4 tasks × 3 prefixes, 554 samples), recovered from `blob_staging/snapshot.tar.gz`. `rebuttal_random/` was correctly rejected as primary — baseline sits at 87.5% there, so no power. Replay makes the arms sample- and prefix-matched, so pairing is exact at `(task, conv, sample_id)`.

**Leakage base rate (strict: injected text verified to contain the *correct* answer):** math 38% (n=144), code **0%** (n=106), database 1% (n=147), actions 2% (n=150); **overall 11%** (n=547). A model-free numeric probe on math independently returns 40% against the LLM's 38% — two methods converging is what makes this quotable.

**Paired gain on the NO_LEAK subset (exact McNemar):** math+code+database, n=329, **36.5% → 57.1% = +20.7pp [+14.8, +25.3], p < 0.0001.** Code alone +30.2pp with *zero* leaks; database +26.0pp with one. Gated-Reset replicates it (+19.6pp, n=311). Under the looser judge label the NO_LEAK gain is *larger* than the LEAK gain (+24.5 vs +17.3), so both label definitions agree.

**Math is the exception and we should concede it outright.** NO_LEAK n=77 gives **−2.6pp [−11.9, +7.6]** — math's entire +9.7pp sits on the leaking subset. The reason is principled rather than embarrassing: on GSM8K, to say "your total of 3,270 is wrong because year 9 is 0" you must compute the right total. Auditing and solving are not separable on that task. Conceding this and holding code/database is far more credible than claiming the mechanism everywhere.

**Classifier honesty.** The raw 3-way label is not trustworthy — two prompts failed validation, and v3 scores only 10/24 exact on a held-out draw (12/13 errors are over-calls). So the agent measured the quantity that actually matters: **precision of the NO_LEAK label = 29/32 (91%)**, with all three errors on math and 24/24 on database/code/actions. Primary numbers use a stricter union detector (answer-verification + numeric probe), not the raw label. Reporting a validated sub-metric instead of an unvalidated headline label is the right call.

**Caveat to state in the rebuttal ourselves:** this conditions on a post-treatment variable. Baseline accuracy is 36.5% on NO_LEAK vs 75.0% on LEAK — the analyzer leaks on easy items — so the *between*-stratum contrast is not causal, though the within-stratum paired test is valid. Single model, one run per cell.
- **11:01** Heartbeat tick. 3 at cap, all healthy — worklog ages T9 2m, T12-T13 8m, T8 15m. The T12-T13 nudge worked on both counts: logging resumed, and it is generating its own `dev_database_ord*.json` ordering files rather than routing the shuffle through the inert `seed=`, which was the specific trap the nudge flagged. It also picked database (high-headroom) over near-ceiling math as its venue. T8 is on `collabllm_ac3_reset_v8`; T9 is running `context_edit_v2_no_gate` at `task.limit=5`, i.e. smoke-testing before committing to full runs. No dispatch, no pivot.
- **11:24** Heartbeat tick — **second intervention.** T9 (worklog 16m) and T12-T13 (12m) healthy and computing. **T8 ambiguous:** its `run_collabllm` processes vanished since the 11:01 tick and nothing has been written under `outputs/` or its task dir in 25 min, yet its worklog is only 38 min old — under the stall threshold. Nudged for a status line rather than restarting, because T8 holds bigcodebench re-scoring context a restart would discard. Escalate to restart next tick if still silent.

  **Rule refinement (D6):** absence of *both* a live process and recent file writes is now a stall signal in its own right, even under the 45-min mtime threshold — it triggers a nudge. Restart still requires all three: mtime > 45 min, no live process, no recent writes.

**F11 (preliminary, from T8's in-progress worklog) — the quoted 20% bigcodebench figure is environment-dependent.** T8 found that bigcodebench scoring is bound to library versions, so it is re-scoring every cell offline under one unified current environment, using the stored `extracted_answer` in `results.json` (no conversation re-runs needed). Under the unified scorer, **rep1's Reset cell is 5/20 = 25%, not the 20% we quote in `replies/v4/`.** At n=20 every cell has 5pp quantisation, so the rebuttal should report raw counts (5/20) rather than a percentage that implies false precision. Awaiting the full replicate set before this is final.

- **11:30** `T12-T13` returned **DONE**. Log: `tasks/T12-T13/worklog.md` (§9 has both paste-ready tables).

**F12 — ⚠️ The memory component's reported gains sit below the learner's own noise floor. This is the most consequential negative result of the session.**

Archaeology first, because it reframes both analyses: the paper states at tex line 709 "On LiC, we use online learning", so Table 1's `+ Memory` rows are **continual, transductive** runs where the cheatsheet is built from the eval set itself with `include_full_spec_q/ground_truth_a=true`. `lic_mem_learn_set.json` was never used for any published number.

**T12 (order sensitivity).** 4 recorded orderings per task (published order + `random.Random({1001,1002,1003})`; because `seed=` is inert here, orderings had to be materialised as physical data files — the trap flagged in the 10:46 nudge). Online: database **28.0 ± 6.5** (20/28/28/36, n=25), math **75.0 ± 4.1** (75/80/75/70, n=20). Cheatsheets diverge in content — mean pairwise content-word Jaccard 0.29–0.32 — converging on the same headline principle but not on operative detail.

The agent then ran two variance controls, and they invert the headline: fixing cheatsheet *and* order and resampling only the eval gives 29.0 ± 3.8; fixing order and relearning gives 25.3 ± 6.1. **Across-ordering std (6.5) does not exceed same-ordering std (6.1).** So ordering is *not* a distinguished source of variance — the cheatsheet learner is simply high-variance (~6 pp) at this scale. Running the control rather than stopping at the headline number is what makes this trustworthy, and it is the difference between reporting "memory is order-robust" (wrong) and "memory is noisy" (right).

**Why this hurts:** the paper's memory effect (+10 pp math, +12 pp database) comes from **single trials**. Against a ~6 pp noise floor a +10 pp single observation is under 2σ — not significant. An N=4 re-measurement on gpt-5.4-mini gives **−5.0 and −8.0 pp**. Different model from the paper's, so this is not a direct refutation, but the variance argument is model-independent and applies to the published numbers as they stand.

**F13 — T13 (split analysis) is clean, and this one helps.** Learn set vs canonical `lic_eval_subset`: **0/120 exact duplicates, 0 near-duplicates** (max Jaccard 0.416, boilerplate). Vs the dev subsets Table 1 actually uses: 11/98 = 11.2%. Clean-subset delta (offline, frozen, disjoint learn set): −4.5 pp database (n=22), +0.0 pp math (n=17). On the *overlapping* instances memory is equal or worse than no-memory. A within-instance probe of the transductive protocol — same instance with an empty cheatsheet vs one distilled from 5–20 other eval instances **plus their gold answers** — gives **0.0 pp on both tasks**. So the contamination concern 5YHP raised is measurably unfounded: leakage is zero, and we can say so with numbers.

**F14 — reliability incident, caught and corrected.** A duplicated background chain double-wrote output dirs between 10:14–10:52. The agent detected it via a contradiction between `metrics.json` and `run_summary.json`, deleted all affected artifacts, and re-ran under an `flock` guard. Worth carrying forward: concurrent agents writing into the same `outputs/` tree can silently corrupt each other, and cross-file consistency checks are what caught it.

**Caveats:** n=20–25 per cell; code and actions not run.

### Decisions (cont.)

**D7 — Do not lean on memory in the rebuttal, and pre-empt rather than defend it.** Memory is not what the reviewers attacked, and F12 says our own numbers there are thin. The right move is to answer 5YHP's W6 with the *strong* half (F13: contamination is measurably zero, 0/120 duplicates, transductive probe 0.0 pp) and to state the variance finding ourselves as a limitation, rather than quote the single-trial +10/+12 pp gains as if they were established. Quoting them invites exactly the seed/variance scrutiny that F4 already exposed us to.

**PAPER-3 (operator action):** Table 1's `+ Memory` rows are single-trial and sit below a ~6 pp noise floor. Either re-run at N>=4 for the camera-ready or soften the claim. Needs the operator — it touches `writing/overleaf_repo/`.
- **11:46** Heartbeat tick. All 3 healthy; no intervention. **The 11:24 T8 nudge worked** — worklog updated at 11:30 and `collabllm_ac3_reset_v8` is running again, so T8 had finished its runs and was mid-analysis rather than wedged. D6's nudge-before-restart ordering was vindicated: a restart would have discarded the bigcodebench re-scoring work. T9 worklog 11m, two `context_edit_v2_no_gate` procs. T1 was dispatched 11 min ago and already has two `summarize_v1` processes live — it stood the summariser strategy up quickly; no worklog yet, which is expected this early. No dispatch, no pivot.
- **12:01** Heartbeat tick — **T8 nudge #2.** T9 (worklog 26m, two `context_edit_v2_no_gate` live) and T1 (worklog 13m, baseline arm running) both healthy. T8 repeated the 11:24 pattern: no processes, no writes for 30 min, worklog 31 min old. Its §6 already carries the conclusions but §7's paste-ready table is still `_(pending bigcodebench)_`, so it is one step from done. Nudge scoped narrowly — fill §7 from numbers already in §6, start nothing new, return. Under the Deli protocol a third silence means structurally stuck: stop nudging and reopen the task with a fresh agent given the existing worklog.

**F15 (preliminary, from T8's §6 — not yet final).** Two claims, pulling opposite ways:
- **The bigcodebench result replicates and is *stronger* than we claimed.** Reset **21.7 ± 5.8** vs Baseline **6.7 ± 5.8** — +15 pp in every replicate, **3/3 wins**, solving 9 problem-instances Baseline never solves while losing none. Safe to lead with.
- **The math-hard side reads as *not* supporting a claimed improvement.** `replies/v4/` currently asserts **100%** off a single run. If this holds, that number must be struck from the rebuttal before submission. Awaiting explicit per-replicate counts — this is the specific thing nudge #2 asks for.

- **12:20** `T8` returned **DONE** — all 12 cells (4 arms × 3 replicates) plus a bonus disjoint-draw pair. Log: `tasks/T8/worklog.md`. This is the most consequential result of the session: it corrects a claim we currently assert in the rebuttal.

**F16 — ⚠️ The math-hard 100% claim does NOT replicate. Strike it from `replies/v4/`.**

| Arm | rep1 | rep2 | rep3 | mean ± sd |
|---|---|---|---|---|
| AC3-Augment | 20/20 (100) | **17/20 (85)** | **18/20 (90)** | **91.7 ± 7.6** |
| Baseline | 19/20 (95) | 19/20 (95) | 17/20 (85) | **91.7 ± 5.8** |

The arms are **exactly tied** — identical means *and* identical per-problem totals (55/60 each). Per-replicate delta `[+5, −10, +5]` = **0.0 ± 8.7**. The quoted 100% is the top of the range, not the centre; the apparent +5 pp was decoding noise on a near-ceiling benchmark (15/20 problems solved by both arms in every replicate).

**What we can still say, and it is not nothing:** AC3-Augment **matches** Baseline. That refutes the *regression* 5YHP raised — no arm degrades — but it does **not** support a claimed improvement. The honest sentence is "matches", and we must stop writing "100%".

**F17 — The bigcodebench claim survives and is stronger than we claimed.**

| Arm | rep1 | rep2 | rep3 | mean ± sd |
|---|---|---|---|---|
| AC3-Reset | 5/20 (25) | 5/20 (25) | 3/20 (15) | **21.7 ± 5.8** |
| Baseline | 2/20 (10) | 2/20 (10) | 0/20 (0) | **6.7 ± 5.8** |

**+15 pp in every replicate — 3/3 wins, sd of the delta 0.0.** Reset solves 9 problem-instances Baseline never solves once, and loses none. It also reproduces on a **fully disjoint** 20-problem draw (0/20 overlap): Reset 3/20 vs Baseline 1/20. A same-direction result on non-overlapping problems is much better evidence than three replicates of one draw, and is worth stating explicitly in the rebuttal.

Quantisation caveat to state ourselves: at n=20 every cell moves in 5 pp steps, and rep1 re-scores to 5/20 = 25% under the unified scorer (problem `451` flips deterministically on a library version). Quote as "≈1 in 5, ±1 problem" rather than a bare percentage.

**F18 — Two harness bugs that silently produce zeros.** Both would have manufactured fake negative results:
1. `bigcodebench` package absent → cells report `0/0 (20 errors excluded)`.
2. Package present but **matplotlib** missing → BigCodeBench's `reliability_guard` dies in-sandbox and `judge_pass_rate` swallows the failure as `0.0`. **T8's first Reset rep2 read 0/20 this way; it is really 5/20.** Caught by re-scoring a known-4/20 cell and getting 0/20 — i.e. by a deliberate positive control, not by noticing something looked wrong.

All bigcodebench cells are consequently re-scored offline under one unified environment from stored `extracted_answer`, with a canonical-solution pre-flight (seed=42 draw passes 19/20; the single failure is never solved by either arm). **Any future bigcodebench number in this project must carry a positive-control check.**

**F19 — True seeding is fixed (2 lines).** The loaders already accepted `seed`; only the dispatcher dropped it. Default remains 42, so **all prior runs reproduce bit-for-bit (verified)**; `seed=1234` yields a 0/20-overlap draw. This partially retires F4 going forward, though it does not retroactively make past "seeds" real.

**Process caveat:** the fix ended up on `main` because other agents' commits landed on T8's branch while it was checked out in the shared tree, fast-forwarding main (refs-only; no working files touched). Verified sane at 12:20 — on `main`, clean tree. **Rule for the rest of the session: no `git checkout` in this shared tree; use a worktree.**
- **12:24** Heartbeat tick. All 3 healthy and — notably — all now logging incrementally without prompting (T9 9m, T2A 15m, T1 17m); the logging-discipline instruction added to briefs after the 10:46 nudge appears to have taken. Live: `baseline`, `context_edit_v2_no_gate`, `summarize_v1`. No dispatch, no pivot.

  Worth flagging from T1's commit stream: `d266c41` adds a **neutral-prompt summarisation robustness arm**. That directly addresses the strawman risk its brief warned about — running a second, differently-worded condenser means the T1 result will not hinge on one prompt's phrasing, which is the first thing a reviewer would attack in a self-implemented baseline. T1 has also already committed an MT-OSC reimplementation (`178edae`), which was only its stretch goal.
- **12:46** Heartbeat tick — **T1 nudge #1.** T2A healthy (worklog 2m). T9 healthy — its worklog records rep2 launched 12:13 into `outputs/T9/rep2/`, matching the four live `context_edit_v2_no_gate` processes; it also notes a preliminary shape worth tracking: *"the analyzer's contribution is recall of divergences, and recall degrades smoothly with analyzer strength"*. T1 nudged: no live processes and a 39-min worklog ending mid-reasoning rather than at a stopping point. The nudge endorsed its null-result framing explicitly so it does not tune the baseline toward an outcome, and required measured call/token counts plus both summariser prompts verbatim.

  **Tooling caveat (D8):** `find -newermt` over `outputs/` returned empty this tick even though T2A's worklog had been modified two minutes earlier — the "recent writes" probe is unreliable in this tree. Stall detection now rests on worklog mtime + `pgrep` only; absence-of-writes is no longer trusted as a signal. Two of the three stall checks I have used tonight turned out to have false-positive modes, which is itself an argument for nudge-before-restart.
- **13:01** Heartbeat tick — **T9 nudge #1.** T9's worklog hit 46 min, the first genuine breach of the 45-min threshold tonight; the D5 process check found two `context_edit_v2_no_gate` processes live and its §8.4 records rep2 launched at 12:13, so this is a long replicate rather than a stall. Nudged for a status line and incremental logging, and re-stated that the `analysis_cache` key finding must appear prominently in its final report — if a stale hit returned a previous analyzer's output, the whole sensitivity curve is an artifact, and that is the first thing a reviewer would check.

  **T1's nudge worked**: worklog updated 12:49 and it committed `fe96bc8` (status line, zero-score controls, live results, neutral-prompt appendix), then launched a `summarize_v1_2pass` arm. The zero-score controls are a direct response to the silent-`0.0` warning propagated from T8's F18 — the cross-task propagation of that finding is doing real work. T2A healthy at 17 min.
- **13:24** Heartbeat tick. All 3 healthy, no intervention. **T9's nudge worked** — worklog went from 46 min stale to 17 min. T2A at 17 min. T1 at 35 min but with live arms: `ac3_rewrite_v8_lic` and `context_edit_v2_gated`, i.e. the AC3-Rewrite and Gated-Reset comparison arms its brief asked for, so it has moved past the summariser arms into the AC3 side of the comparison.

  Scoreboard on the guardian mechanism: **five nudges tonight (T12-T13, T8 ×2, T1, T9), five responses, zero restarts.** Every case that tripped a staleness signal turned out to be a live agent mid-work, which is why the nudge-before-restart ordering (D5/D6) mattered — a restart-on-threshold policy would have destroyed T8's bigcodebench re-scoring and T9's in-flight rep2.

- **13:50** `T9` returned **DONE**. Log: `tasks/T9/worklog.md` (commit `1f4f32d`). Clean, strongly positive, and it closes a question we were asked directly and had never answered.

**F20 — The `analysis_cache` confound is resolved; it was never a threat.** `AnalysisCache.make_key()` includes the analyzer model identity (`src/ctx_editor/strategies/analysis_cache.py:92`), and the sole call site passes the live model (`src/ctx_editor/strategies/analyzer.py:587`, `analyzer_model=self.model`, Hydra-bound to `${model.ctx_editor.model}`). RECON's open Unknown #9 is closed. The agent nonetheless disabled the cache on every run *and* audited every trace to confirm each arm made 100% of its analyzer calls with the intended model — three independent guards on the one check that could have invalidated the whole task. This is the right level of paranoia for a load-bearing validity question.

**F21 — Analyzer-model sensitivity: graceful degradation, not collapse.** Assistant pinned to DeepSeek-V4-Flash; only `model.ctx_editor.model` varies. Venue LiC code+database last-turn replay (Baseline 21.3% pooled — the headroom T2c identified; math deliberately avoided). AC3-Reset always-on so the analyzer fires every sample. 2 replicate runs at temperature 1.0 (**not** seeds). n=178 matched pairs, exact McNemar.

| Analyzer | Family | AC3-Reset | Δ | p |
|---|---|---|---|---|
| Kimi-K2.6 | Moonshot | 61.2 ± 2.4 | **+39.9** | 2e-17 |
| DeepSeek-V4-Flash (ref) | DeepSeek | 50.0 ± 2.4 | **+28.7** | 3e-09 |
| gpt-5.4-mini | OpenAI | 48.3 ± 1.6 | **+27.0** | 1e-08 |
| Llama-3.3-70B | Meta | 39.3 ± 0.0 | **+18.0** | 6e-06 |
| gpt-4o-mini | OpenAI | 34.3 ± 0.8 | **+12.9** | 8e-04 |

Every analyzer is positive and individually significant. The weakest retains 32% of the reference gain and still beats Baseline by 12.9 pp; **no arm falls below Baseline on either task in either replicate**. The top is flat — the two strongest are indistinguishable (Δ = −1.1 pp, p = 1.00).

**The mechanism behind the curve is measured, not assumed:** weak analyzers **under-detect rather than mis-detect**. gpt-4o-mini declares `needs_edit` on 74.4% of turns vs ~97% for strong analyzers and writes 2.7× shorter issue lists, yet `user_intent` parsed on 100% of calls and `edited_context` was non-empty on 100% of applied edits. It notices less; it does not hallucinate issues that corrupt the context. That is exactly why the degradation is graceful, and it is a far better answer to Vg97 than a bare table.

**F22 — The method is not gpt-specific, and the evidence is stronger than "it also works elsewhere."** Three of five analyzers are non-OpenAI and they occupy the top, middle and lower rungs, interleaving with the OpenAI models. The best analyzer overall is **Kimi-K2.6, +12.9 pp above the paper's own default**, and the *weakest* is an OpenAI model. Since the assistant is also non-OpenAI, the best-performing cell contains no OpenAI model anywhere.

**Limits to state ourselves:** n = 40+49 per replicate; adjacent rungs are not individually separated — defend the *shape* and the *endpoints*, not the exact ordering. The ± is spread over N=2, not a variance estimate. One assistant, one strategy (no Gated arm). Baselines reproduced phase-1 to within 4 pp, so the harness is sound.

- **14:00** `T2A` returned **DONE**. Artifacts: `tasks/T2A/{RESULTS.md,worklog.md,inject.py,measure.py,manifest.jsonl}`, 32 run cells under `outputs/T2A/`, commit `88cacb3`.

**Design (why the labels are trustworthy):** into 145 LiC database+code replay prefixes the agent injected **two** spans per conversation — one known-false, one known-true — in an identical surface frame, each anchored on a rare token verified absent from the conversation. Labels are ground truth by construction; **no judge anywhere**. 126 conversations pass a mechanical admissibility check. The two-span design is what makes preservation measurable at all: with only false spans injected, an editor that deletes everything would score perfectly.

**F23 — Detection works, and the four metrics (AC3-Reset, n=126):**
- **Pollution removal 97.6%** (123/126), CI [93.2, 99.2]; 96.9% on the causally-validated subset
- **Preservation 4.0%** (5/126), CI [1.7, 9.0]
- **Edit precision 50.4%** (123/244) — **chance is exactly 50% here**
- **Gate sensitivity 98.4%** (124/126); clean-arm gate-open base rate 96.8%

The signal that is *not* explainable by "it deletes everything": the analyzer **names the injected pollutant in `issues` 78.6%** of the time (89.7% on the causally-harmful subset). That is genuine detection, independent of what the editor then does.

**F24 — Removal predicts accuracy, causally.** The direct split is underpowered (only 3 conversations where AC3 kept the span), so the load-bearing evidence is a detector-free factorial over Baseline (clean / harm-only / useful-only / both): the harmful span costs an unedited assistant **−11.1 pp**; the true span is worth **+15.1 pp**. On the causally-validated subset: Baseline clean 24.7% → with pollutant 9.3% → **AC3 with pollutant present 59.8%**. Building the causal ladder out of Baseline arms rather than out of detector output is what keeps this non-circular.

**F25 — ⚠️ The paper's "we preserve what's correct and remove what's harmful" is NOT supported for AC3-Reset.** Edit precision sits at chance and preservation is 4%: Reset removes *correct* injected content at essentially the same rate as false content. What the data supports for Reset is a different and still-defensible mechanism — **"detect, discard the assistant side, and re-derive the spec from the user side."** The detection is real (78.6% naming rate); the *surgical* part is not.

Crucially, **AC3-Rewrite sits at the opposite corner** (removal 27.0%, preservation 38.9%), which both proves the metric is not saturated and shows the selectivity claim belongs to Rewrite, not Reset. The fix is attribution, not retraction: state the operator-specific mechanism rather than a blanket claim.

This matters beyond the rebuttal — the "unlike prior work that discards all assistant messages, we preserve what's correct" framing is in the project's own overview and is part of how the paper differentiates from ERGO. **Queued as PAPER-5.**

**F26 — Positive controls all pass, and one caught a real bug.** Offline, n=126: identity editor 0.000/1.000, oracle 1.000/1.000, nuke 1.000/0.000, delete-both 1.000/0.000. **PC2 caught a word-boundary vs substring mismatch in the agent's first probe** (`Museum_ID` ⊂ `Museum_IDs`) that would have silently overstated removal. Third time tonight a control caught something that looked fine.

**Caveats (stated in RESULTS.md's first paragraph, correctly):** injected pollution is plausibly more salient than natural pollution, so these are an **upper bound / sanity check**, not a headline. Two of four injected types are causally inert; N=1 per cell; single model.

### Decisions (cont.)

**D9 — Report T2A as "detection is strong, selectivity is operator-dependent," never as a bare 97.6%.** Quoting 97.6% removal alone would be the most attackable sentence in the rebuttal: a reviewer computes edit precision from our own confusion table, finds chance, and concludes we hid it. Leading with the honest decomposition — high detection, chance-level selectivity for Reset, real selectivity for Rewrite — is both more defensible and more interesting.
- **14:01** Heartbeat tick. All 3 healthy, no intervention. **T1's nudge #2 worked** — worklog went from 57 min stale to 10 min, `summarize_v1` running again. T6 is moving fast: it cloned `tau2_ctxe` to `~/ac3/` — correctly *outside* the shared ctx_editor tree, as its brief required — and had two `run_parallel.py` processes live within 11 minutes of dispatch. T11 is extracting `huang_eval/{phase1,phase2,rejudge}` and `post_neurips_ac3_phase3_huang` from `snapshot.tar.gz`, i.e. recovering the existing judgements rather than re-running generations, which is the cheap path RECON identified.

  Guardian scoreboard: **six nudges, six responses, zero restarts.** Only T2B (counterfactual span ablation) remains unqueued.
- **14:24** Heartbeat tick. No intervention. T6 healthy (worklog 6m) and has scaled from two to **three** `run_parallel.py` workers. T11 healthy (worklog 3m). T1 at 33 min — inside tolerance, with a `context_edit_v2_no_gate` process plausibly its AC3-Reset arm; deliberately **not** nudged a third time, since it is already at two and over-nudging a working agent is itself disruptive.

  **Escalation plan recorded (D10):** if T1 breaches 45 min next tick, that is nudge #3 — the Deli "structurally stuck" threshold, where the protocol says stop nudging and reopen. Rather than a third nudge, I will ask T1 to return whatever it has immediately; failing that, reopen T1 with a fresh agent handed the existing worklog and commits (`178edae` MT-OSC, `d266c41` neutral-prompt arm, `fe96bc8` controls/appendix) so none of the work is lost. T1 answers the Area Chair's "limited baselines" and must not end the session unreported.
- **14:46** Heartbeat tick. T6 (worklog 8m, three `run_parallel.py` workers) and T11 (worklog 6m) healthy. **T1 breached the threshold at 55 min — third intervention, but revised from the D10 plan.**

  **D10 revised.** The recorded plan was to treat a third breach as "structurally stuck" and reopen with a fresh agent. On inspection that would have been wrong: `summarize_v1_2pass` is live and T1 has shipped three commits since dispatch, so it *is* progressing — the Deli stuck-criterion is *no progress*, not *no logging*. Reopening would have destroyed four arms of work to fix a bookkeeping problem.

  The real failure mode is **scope creep, not stalling**: T1 has now started `summarize_v1`, a neutral-prompt robustness arm, `summarize_v1_2pass`, *and* an MT-OSC reimplementation — more than T1 needed, and the marginal arm is now worth less than a finished report. So I issued a **scope directive** instead: let the current arm finish, start no new arms, write up, return. Priority order given: the Baseline/summarisation/AC3-Reset table first (the Area Chair's "limited baselines" answer), then measured call/token budgets, then the prompts verbatim.

  Worth recording as a general lesson: a stall detector that only watches liveness will misclassify an over-eager agent as a dead one. The signal that distinguished them was *commits and new processes without worklog updates* — progress in the artifact stream but not in the record.
- **15:01** Heartbeat tick. T6 (worklog 23m, three `run_parallel.py`) and T11 (worklog 11m) healthy. **T1 held, not re-escalated.** Its worklog is now 70 min stale and `summarize_v1_2pass` is still live, but the scope directive went out only 15 min ago and messages are delivered at the agent's next tool round — if T1 is blocked on a long subprocess poll it has not seen it yet. Repeating the same directive 15 minutes later would be noise rather than escalation, so: hold one tick, then act. T1 remains the session's single watch item.

- **15:10** `T1` returned **DONE**. Logs: `tasks/T1/worklog.md` (decisions, all prompts verbatim, gaps) and `tasks/T1/RESULTS.md` (regenerable via `analyze.py`).

**F27 — Summarisation does NOT close the gap. The AC's "limited baselines" is answered empirically.**

| Task | Arm | Acc | n | Δ vs base | McNemar p |
|---|---|---|---|---|---|
| database | Baseline (FC) | 56.1% | 60/107 | — | — |
| database | Summarisation, 1 call/turn | 53.3% | 57/107 | −2.8 | 0.678 |
| database | Summarisation, 2 calls/turn (budget-matched) | 47.7% | 51/107 | −8.4 | 0.078 |
| database | MT-OSC (reimpl., w=4 as published) | 60.7% | 65/107 | +4.7 | 0.383 |
| database | **AC3-Reset** | **75.7%** | 81/107 | **+19.6** | **0.0005** |
| database | **AC3-Gated-Reset** | **73.8%** | 79/107 | **+17.8** | **0.0013** |
| code | Baseline (FC) | 83.0% | 83/100 | — | — |
| code | Summarisation, 1 call/turn | 79.0% | 79/100 | −4.0 | 0.481 |
| code | Summarisation, 2 calls/turn | 80.0% | 80/100 | −3.0 | 0.581 |
| code | **AC3-Reset** | **92.0%** | 92/100 | **+9.0** | **0.023** |

Head-to-head paired: AC3-Reset − summarisation = **+22.4/+28.0 pp** (database), **+13.0/+12.0 pp** (code), all p < 0.01. The prediction held: a good-faith condenser carries invalidated reasoning forward in compressed form.

**The budget result is stronger than parity.** Measured per-component via a new `utils/call_meter.py`: the budget-matched summariser did not merely match AC3-Reset, it **over-consumed** it — **1.02–1.19× strategy calls, 1.62–2.14× strategy tokens** — and still lost by 12–28 pp. Gated-Reset gets +17.8 pp on **0.41×** Reset's calls. "We spent more compute on the baseline and it still lost" is a far better sentence than "budgets were comparable."

**MT-OSC is reportable but structurally inapplicable, and that is the interesting part.** At published w=4 it fired **30 times across 107 conversations (0.3/conv)** because it cannot touch context before turn 6, while LiC conversations average 4.1 turns. So its +4.7 pp (p=0.383) is not a fair test of MT-OSC's idea — it is evidence that length-triggered compaction schedules *cannot engage* with pollution that appears early. That is exactly our scoping argument, now with a number behind it.

**F28 — ⚠️ `adjusted_accuracy` is invalid across context-editing arms, and it inflates our own published numbers.** The false-negative judge reads *visible* messages only, so editing arms get **50–78% of failures excluded** versus **9%** for baseline. An arm-symmetric re-judge collapses exclusions to 2–6% uniformly and **reproduces the raw ordering**. Magnitude on a shipped number: **AC3-Reset database 89.0% as published vs 77.1% corrected.**

This is the most serious methodological finding of the session. The bias runs *in our favour*, it affects the paper's headline LiC table, and a reviewer who reconstructs the FN-adjustment would find it. The direction of our claims survives — the raw ordering is unchanged and AC3 still wins — but the magnitudes do not. **Queued as PAPER-6, and see D11 below.**

**F29 — A 30 pp low score was a harness fault, and was caught.** MT-OSC w=2 scored 26.2% because the agent's schedule dropped raw pairs completed after the condensation window (fixed in `c1dd523`). The buggy run is archived; **do not quote its 26.2%**. Fourth time tonight that treating an anomalous number as a suspected fault rather than a result was correct.

**Confidence:** high on direction and significance (n=207 paired, consistent across two tasks, two summariser budgets, and both accuracy metrics); moderate on exact magnitudes (N=1 per cell — `seed=` is inert on LiC). **Not run**, having converged on the scope directive: MT-OSC w=2 post-fix, all code MT-OSC/Gated cells, both neutral-prompt robustness cells (implemented; prompt in the worklog appendix).

- **15:20** `T11` returned **DONE**. 1,824 judgements, 0 hard failures. Log: `tasks/T11/worklog.md` (paste-ready tables + both prompts verbatim); raw JSONL and `analysis_full.txt` in `tasks/T11/out/`.

**F30 — Position bias is real and significant, but does not contaminate the published number.** The headline judge (gpt-5-mini) prefers the **second**-presented response: AC3 wins 92.3% shown second vs 86.7% shown first (452 pairs, 904 judgements). Of 44 order-discordant pairs, 32 flip toward the second slot vs 8 toward the first — exact binomial **p = 1.8e-4**. Swap-consistency 90.3%. The other two judges lean the *opposite* way (DeepSeek −6.2 pp, Kimi −3.1 pp, neither significant), so this is a per-model quirk rather than a prompt artefact.

Why the paper is nonetheless safe: `pairwise_judge.py` **already randomises A/B 50/50 per call**, so the published number is unbiased for the order-balanced quantity in expectation. It discards the realised assignment, which is why this needed re-judging rather than re-analysis — worth an appendix note, because it is also the reason we could not have checked this from the existing logs.

**F31 — The 89.8/92.1 headline survives with a small honest correction.**

| | published | order-balanced (corrected) | Δ |
|---|---|---|---|
| AC3-Reset | 89.8 ± 1.4 | **87.8 ± 2.1** | −2.0 |
| AC3-Augment | 92.1 ± 1.3 | **91.2 ± 2.1** | −0.9 |

A 200-draw random-order resimulation puts Augment's published value inside the interval and Reset's ~0.5 pp outside, so **report the corrected numbers** rather than defend the originals. Cheap concession, and it makes the rest of the section more credible.

**F32 — Judge agreement holds under cross-family and self-consistency checks.** Shared 160-pair subset, matched presentation: gpt-5-mini vs DeepSeek-V4-Flash raw 87.5% / κ 0.449; vs Kimi-K2.6 raw 88.8% / κ 0.507; DeepSeek vs Kimi 85.9% / κ 0.445. κ is depressed by the ~90% marginal (the kappa paradox), so the agent also reports **PABAK 0.79–0.83 and Gwet's AC1 0.84–0.87** — the right response to a known statistical artefact rather than quietly quoting the flattering statistic. Self-consistency (identical prompt and order, independent call) is raw **96.9%, κ 0.810**, materially higher than swap-consistency, which cleanly attributes most judge instability to **order rather than sampling**. Each judge's own order-balanced win-rate: 88.8 / 85.6 / 85.3 — max spread 3.5 pp. Under a punitive "2-of-3 judges in both orders" rule it is still **82.5%**.

**Positive controls pass** (intact vs a degraded copy of itself, both orders, n=20 pairs each): gpt-5-mini 39/40, DeepSeek 36/40, Kimi 40/40; zero cases of the degraded copy winning outright for gpt-5-mini/Kimi.

**F33 — incidental:** the judge never ran at temperature 0. The client logs `gpt-5 models require temperature=1.0, overriding 0.0 -> 1.0`. Any claim that judging was deterministic is wrong; the 96.9% self-consistency figure is the honest substitute.
- **15:24** Heartbeat tick. All 3 healthy, no intervention. T6 worklog 5m with three `run_parallel.py` workers; T14 worklog 2m, extracting `outputs/`, `scripts/` and `docs/` from `snapshot.tar.gz` to reach the historical runs it needs; T15 dispatched 5 min ago, no worklog yet as expected. No dispatch — the queue is empty apart from the deliberately deferred T2B.

  **Session shape from here:** T6 (tau2 replicates) and T14 (FN-adjustment audit) are the last two results outstanding, and T15 is writing `replies/v5/` around clearly-marked placeholders for both. T14 is the one that could still move numbers — it may reduce the paper's headline LiC magnitudes, which is why every LiC figure in v5 is flagged provisional.

- **15:45** `T15` returned **DONE**. `neurips_review/replies/v5/` written and committed (`5775f71`); `v4/` untouched as the diff baseline. Audit table: `replies/v5/CHANGES.md`. Posting blockers: `replies/v5/README.md`.

**Audit outcome over 64 v4 claims: 24 unchanged · 14 corrected · 6 struck · 11 newly added · 4 on hold · 5 unverified.** Of the 14 corrections, 6 move against us, 3 in our favour, 5 are wording-only.

**F34 — ⚠️ The rebuttal's end-to-end table was itself FN-adjusted, and the artifact proves it.** v4's "AC3-Reset **100.0 ± 0.0**" traces to `exp1_results.txt` / `exp1_reps_results.txt`, where AC3-Reset had 1, 2 and 5 items excluded across the three runs while **baseline had zero**. That is precisely the F28 bias, inside our own rebuttal rather than the paper. Corrected to raw: **87.5 ± 2.0 / 93.3 ± 4.2 / 95.0 ± 0.0**. The claim survives — both operators win in all three runs — but a perfect 100.0 ± 0.0 built on asymmetric exclusions was the single most attackable number we had, and it appeared in **five files**.

**F35 — The 33/36 paired significance table is NOT affected by F28, and this materially shrinks the T14 exposure.** Verified mechanically: every (task, prefix) cell in the phase-1/2 source tables uses one denominator across all strategies, which an FN-adjusted table could not. v5 now says "on raw accuracy" explicitly. So T14 threatens the **paper's Table 1**, not the rebuttal's headline statistic — a much better position than it looked at 15:10.

**F36 — Two v4 claims were factually wrong and are struck; one was a limitation we conceded that does not exist.** We told 5YHP that BigCodeBench "cannot be evaluated with executable tests" — T8 §5 shows that path runs real `untrusted_check` execution. Conceding a false limitation is a pure own-goal: it invites a reviewer to think we did not understand our own harness. The dependent "the judge discriminates" figures went with it.

**F37 — ⚠️⚠️ Biggest remaining exposure: the tau2 baselines may not replicate.** T6's completed Baseline cells read DeepSeek-V4-Flash **70.2 ± 11.0** and Kimi **80.4 ± 2.5** against published **31.6** and **26.3**. Kimi's re-measured baseline is above *every* published Kimi AC3 number. If this holds, two of three tau2 cells were measured against broken controls, and the AC letter needs a fifth self-correction. **Preliminary — T6 is still running and this is the number to watch.**

T15 handled it correctly rather than optimistically: all per-model tau2 magnitudes are sealed in six loudly-marked `⚠ INTERNAL — HOLD` blocks with draft withdrawal wording pre-written, and the section is rebuilt around the **AO-collapses-to-0%** result, which T6's own positive control corroborates mechanistically and which is the tau2 result our argument actually needs. It also removed CW1's "tau2 confirms the operator rule" sentence (same contested cells) and replaced that argument with **T9's five-analyzer sweep** — stronger evidence for the same point, from data that is not in question.

**F38 — Five claims could not be verified against any artifact** (`CHANGES.md` §7). The one that matters: **gate-open rates 97.3% (LiC, n=554) and 98.3% (CollabLLM, n=119)**, which appear in the reply to the reviewer who asked specifically for detector statistics. Their only source is session-1 prose — no `needs_edit` tally artifact exists. They are consistent with tonight's independent measurements (T2A 96.8%/98.4%, T9 ~97%), so they were left in, but an unverifiable number in the detector reply is exactly what a probing reviewer would ask us to produce. Re-deriving them from `traces/*/conversation_analysis.needs_edit` is a **zero-API script** — the cheapest risk reduction left, so it is being dispatched now (T16).
- **15:46** Heartbeat tick. All 3 healthy, no intervention. T6 worklog 17m, still sweeping on three `run_parallel.py` workers — it is the long pole and carries the session's most severe open question (F37, whether the published tau2 baselines replicate). T14 worklog 2m. T16 dispatched 3 min ago, no worklog yet, as expected for a zero-API task. No dispatch, no pivot; queue empty apart from the deferred T2B.

- **15:55** `T16` returned **DONE** (zero API calls). Artifacts: `tasks/T16/{worklog.md,gate_stats.py,report.md,gate_stats.json}`, commit `8d545ff`.

**F39 — The gate statistics hold to the digit; the *wording* was wrong.** The claim reproduces exactly, and U1 turns out to have been a false alarm about provenance — the 2026-06 artifacts do exist in-repo at `scripts/analysis_rewrite_v_reset/data/gated_reset_reconstructed_{lic,collabllm}.md`, stating `539/554 (97.3%)` and `117/119 (98.3%)` verbatim; the T15 audit simply missed them. T16 re-derived both independently from raw traces.

| population | metric | value |
|---|---|---|
| LiC | legacy (= the claim) | **539/554 = 97.3%** ✅ exact |
| LiC | corrected turn-level | 539/547 = **98.5%** |
| CollabLLM | legacy (= the claim) | 118/120 = **98.3%** ✅ exact |
| CollabLLM | **turn-level** | 628/659 = **95.3%** |

No bimodality — every task/cell lands in 93–100%. Two defects worth fixing regardless: both figures are per-**conversation**, not per-turn (harmless for LiC, which is last-turn replay with exactly one analyzer call per conversation, but materially wrong for CollabLLM at 659 calls over 120 conversations); and both denominators counted conversations the analyzer never ran on as gate-*closed* — the precise trap flagged in the brief. Correcting it raises both rates.

**New caveat T16 surfaced:** 29% (LiC) / 73% (CollabLLM) of gate-open records have the analyzer writing `issues: "None"` while still setting `needs_edit=true`. It is a **firing rate, not a detection rate.** This does not contradict the reply — which already says the gate is deliberately near-always-on — but a reviewer handed `gate_stats.py` would find it, and we are better off having named it first.

**Controls pass:** an independent regex parser matches the JSON walk across all 3,179 fields; 0/1,197 disagreements against `edit_decision.should_edit`; 12 records hand-read. One false alarm caught and corrected (an apparent 51% "prompt-template echo" rate in CollabLLM was a header-prefix formatting artifact; no headline number touched).

**Action taken (main thread):** applied T16's one-sentence correction to `replies/v5/03_reviewer_5YHP.md` myself — T16 correctly declined to edit a file it believed other agents were using, but T15 had already finished, so the edit was safe. The line now reports LiC 97.3% per-conversation (98.5% turn-level) and CollabLLM **95.3% turn-level** (98.3% per-conversation), rather than mislabelling both as turn rates. `CHANGES.md` §7 U1 is retired.

**Note on the gate paragraph:** it is worth keeping the sentence that follows — "we would not over-read firing rates into a precision/recall claim" — because F39 shows exactly why that hedge was correct, and T2A's 50.4% edit precision is the measurement that belongs there instead.
- **15:58** Dispatched `T2B` (counterfactual span ablation) into T16's freed slot — the last unrun item in `experiment_todos.md`. Framed deliberately as *upgrading T2A's synthetic injections to naturally-occurring spans*, which is T2A's own stated limitation, rather than as filling a gap: T2A already answered the circularity objection non-circularly. Its brief requires the alignment check against **Rewrite as well as Reset**, since T2A showed Reset's non-selectivity (edit precision at chance) makes its answer largely predetermined by design — Rewrite is where "do AC3's edits match the causal labels?" is actually an open question.

- **16:15** `T14` returned **DONE**. Artifacts: `tasks/T14/{RESULTS.md,worklog.md,survey.py,rejudge.py,analyze.py,corrected_matrix.*}`, commit `30089f3`.

**F40 — Two conclusions flip under the arm-symmetric correction, both on AC3-Rewrite.** Under the shipped metric AC3-Rewrite beats baseline in 4/4 LiC tasks; corrected, it **loses in 2/4** — code **+46.0 pp → −5.3 pp**, actions **+22.4 → −1.5**. A 46-point win is manufactured out of a 6-point loss, on our own arm.

**Scope, stated precisely so this is neither over- nor under-sold: neither flip is a published error.** `tab:main` has no AC3-Rewrite LiC row, and `tab:megatable` — where Rewrite does appear — is computed from **raw** (`build_mega_table.py:87-96`). So this is not a correction to the paper; it is proof that the metric *can* invert an ordering, which is the argument for deleting it.

**What survives, and it is the load-bearing part:** AC3-Reset and AC3-Gated-Reset beat baseline in **all 8 cells** under raw, shipped-adjusted and corrected alike, and the Gated-vs-Reset ordering holds cell-for-cell.

**F41 — Magnitude and mechanism.** Reset arms inflate **+13.9 to +55.9 pp** (worse than the single +12 pp cell T1 found); no-reset arms only **+0.2 to +6.5**. After correction, adjusted−raw is a uniform +0.0 to +3.9 across every arm. The mechanism is measured, not inferred: the judge sees **1.00 user turns/sample** on AC3-Rewrite vs **5.35** on baseline (`trace.py:102-105` hides user messages; `context_edit_v2.py:117-124` re-adds the spec under role `"compacted conversation"`; `identify_false_negatives.py:173` keeps only `role=="user"`). A second full re-judge cleanly separates judge-swap from visibility: the visibility effect is **+0.5% on no-reset arms and −48.9% on reset arms.**

**F42 — ⚠️ The paper is *less* exposed than feared on FN adjustment, but has a worse defect: ERGO is scored on the wrong denominators.** `tab:main` uses a **pool-level pre-filter** (`data/baseline_traces_v2/*_false_negatives.json`, computed on baseline traces and applied identically to all arms) that exactly reproduces its 20/19/25/23 denominators. That is arm-symmetric and correct — **defend it.** Per-run `adjusted_accuracy` touches at most 4 cells at ≤1 sample each, and 2 of the 4 favour prior work.

**But ERGO's denominators are 23/25/25/25 — the *unfiltered* pools — while every other row uses 20/19/25/23.** Bound: ERGO math could reach **80.0 vs published 69.6**, tying or beating AC3-Reset's 75.0. That is worth ~14 pp **against prior work**, and it is visible from the printed percentages alone.

This is the most dangerous single item found tonight. An error that inflates our own numbers is embarrassing; an error that *deflates a baseline we compare against* is the kind reviewers read as thumb-on-the-scale, and it is arithmetically checkable from the table as printed. **Queued as PAPER-7 and dispatched for immediate quantification as T17.**

**T14's recommendation (endorsed):** report **raw** as primary; keep the pool filter as the only FN adjustment; **delete per-run `adjusted_accuracy`**; rewrite `tex:478-480` (it claims "all user simulator messages"; the code collates only the visible ones); and **fix the ERGO/Gated-Reset denominators first.**

**Controls:** shipped metric reproduced to 1e-6 across 499 runs; 0 cross-file mismatches; no archived run hit the TRAPI FN no-op condition.
- **16:01** Heartbeat tick. All 3 fresh and healthy — T6 worklog 2m with three `run_parallel.py` workers, T17 worklog 3m (it logged within three minutes of dispatch), T2B worklog 8m with a baseline arm running. No dispatch, no pivot; the queue is empty.

  The two open severe items are both in flight: **F37** (do the published tau2 baselines replicate — T6) and **F42** (ERGO scored on unfiltered denominators — T17). Everything else this session has either landed or been retired.

- **16:20** `T17` returned **DONE** (zero API calls). Artifacts: `tasks/T17/{RESULTS.md,worklog.md,build_corrected.py,corrected_tabmain.json}`, commit `6ebc59b`.

**F43 — Confirmed, and there are two defects, not one.**
- **D1 — ERGO alone is scored on the unfiltered pools**: 16/23, 11/25, 3/25, 12/25 against everyone else's 20/19/25/23. Confirmed not by inference but by the author's own Overleaf commit `d856247`, which states those exact fractions and names the (now-lost) run dirs. The filter is `replay.py:21-56` + `run_experiment.py:441-470`, and ERGO's denominators equal filtered-n plus pruned stubs exactly on all four tasks (20+3, 19+6, 25+0, 23+2).
- **D2 — four cells sit one sample *below* the pool denominator** (AO/code 14/18, Concat/math 16/19, Augment/code 10/18, Reset/code 11/18) and Gated-Reset's actions row sits two *above* it (n=25).
- Also: **the actions column's n=23 has no artifact behind it at all** — no `actions_false_negatives.json` has ever existed. It is the ad-hoc "common 23-sample" normalisation the paper itself confesses at `tex:508`.

**F44 — ⚠️⚠️ An AC3 claim genuinely weakens, and we must say so plainly.** Corrected ERGO (k=0 point estimate): math **69.6 → 80.0**, code **44.0 → 57.9**, database 12.0 unchanged, actions **48.0 → 52.2**.

- **ERGO beats AC3-Reset on math (80.0 vs 75.0)**, ties it on code (57.9) and actions (52.2), and **ties AC3-Gated-Reset — our recommended default — on math (80.0 vs 80.0)**.
- Across the twelve no-memory ERGO-vs-AC3 comparisons, ERGO moves from losing 11/12 to **winning-or-tying 7/12**.

**What holds, and it is not nothing:** database is untouched and decisive (ERGO 12.0 vs AC3 48.0); **Gated-Reset is still ≥ ERGO on all four tasks**; every operator still clears Baseline; and **no printed *sentence* becomes false** — the LiC prose compares against AO and Baseline, and the single explicit ERGO claim survives. Two body numbers even move in our favour (code gap-closure 78% → 82%; "closes 55–80%" → "67–82%").

This is the correct outcome to have found ourselves. The fix strengthens a competitor and narrows our margin, which is exactly why a reviewer finding it first would have been severe.

**F45 — The bound cannot be closed from disk.** The per-sample results are gone: `outputs/2026-05-01/23-*` (ERGO), `2026-03-21/*` (AO, Concat, Reset) and the whole v8 batch are absent from the 69,738-entry snapshot index, from `supplementary.tar.gz`, from `runs.yaml` (875 entries) and from every recovered tree. Numerators are attested; the pruned-item split is not. **ERGO code is therefore only bounded to [26.3, 57.9]** — far too wide to publish.

Closing it needs **87 last-turn ERGO replays at roughly $0.20**, using `replay_source=data/baseline_traces_v2/{task}` so the filter fires automatically. T17 correctly stopped rather than estimating, and flagged it as step 1 of PAPER-7. **Dispatched as T18** — twenty cents to convert an unpublishable interval into an exact number is the best remaining trade in the session.

**Controls (exemplary):** the denominator rule reproduces on all 28 archived pool-replay runs with 0 exceptions; the 20+3=23 stub arithmetic was verified against actual files (a run reporting n=20 holds 23 traces, 3 empty, matching the sidecar IDs); a **blind rational reconstruction of ERGO's fractions matched the Overleaf commit message on all four cells**; three independent source docs reproduce three published rows to the digit; all 30 unchanged cells are bit-identical.
- **16:24** Heartbeat tick. All 3 healthy, no intervention. T6 worklog 25m with three `run_parallel.py` workers still live — it is now ~2h30m in and by far the longest-running task of the session, which is expected for agentic tau2 rollouts. T2B worklog 13m, T18 worklog 8m. No dispatch, no pivot; queue empty.

  **F37 (do the published tau2 baselines replicate?) is the last severe item outstanding.** Everything else has landed: the ERGO denominator defect is quantified (F43/F44) with its bound being closed by T18, and the FN-adjustment question is resolved in the paper's favour on `tab:main` (F42).
- **16:46** Heartbeat tick. All 3 healthy, no intervention. T6 worklog 19m (three `run_parallel.py` workers). T18 worklog 21m with a baseline arm running. T2B worklog 17m and now running **both** `ac3_rewrite_v8_lic` and `context_edit_v2_gated` — i.e. it is doing the Rewrite-arm alignment check its brief specifically required, rather than only the easy Reset comparison whose answer T2A showed is largely predetermined by design. No dispatch, no pivot.
- **17:01** Heartbeat tick. All 3 healthy, no intervention. T2B worklog 14m. T6 (34m) and T18 (36m) are both approaching the 45-min threshold but each has live processes — three `run_parallel.py` workers for T6, baseline arms for T18 — so under D5/D6 the process check clears them. Flagged as the watch item for next tick; per tonight's record (six nudges, six responses, zero restarts) the correct response if they breach is a nudge, not a restart.

- **17:10** `T18` returned **DONE**. Log: `tasks/T18/worklog.md`.

**F46 — The positive control did NOT reproduce, and that is the most important line in the report.** ERGO/database measured **44.0 vs published 12.0**. `gpt-5-mini` (the published-era model) is unreachable — `dl-openai-3` returns 401, there is no `.env`, and TRAPI serves only `gpt-5.4-mini`/`gpt-4o`. **Therefore no re-run's absolute levels are substitutable into `tab:main` tonight, by anyone.** The control did exactly its job: it prevented a plausible-looking set of numbers from being written into the paper.

**F47 — The bound was closed anyway, by a design that does not depend on comparable levels.** T17's interval has exactly one free parameter — **k**, how many pruned items ERGO solved. T18 measured k directly by replaying ERGO against a *pruned-items-only* pool (sidecar removed so the filter cannot fire):

| task | published | T17 pt est | T17 interval | **k measured** | **T18 result** |
|---|---|---|---|---|---|
| math | 69.6 (16/23) | 80.0 | [65.0, 80.0] | **0/3**, 3 reps | **80.0 = 16/20 — CLOSED** |
| code | 44.0 (11/25) | 57.9 | [26.3, 57.9] | **2.67/6** (3,2,3) | **43.9 = 8.3/19, [42.1, 47.4]** |
| database | 12.0 (3/25) | 12.0 | exact | n/a | 12.0 |
| actions | 48.0 (12/25) | 52.2 | [43.5, 52.2] | **unmeasurable** — no sidecar exists | unchanged |

k transfers across the model gap because **full-context Baseline solves 0/6 pruned code items at the newer model too** — the three solvable ones are unlocked by *context cleaning* (ERGO 3/6, Concat 3/6, AC3-Reset 2/6), not by the newer model. That is the argument that makes the transfer legitimate rather than assumed.

**F48 — T17's code estimate was too generous; the math finding survives.**
- **math holds: ERGO 80.0 beats AC3-Reset (75.0) and ties AC3-Gated-Reset (80.0).** This is the reviewer-visible defect and **it must ship**.
- **code does not: T17's k=0 was wrong.** Corrected ERGO/code is ~43.9 — essentially the published 44.0, a correction of ≈ **−0.1 pp, not +13.9**. AC3-Reset leads by ~14 pp, Gated-Reset by ~19. **Shipping T17's 57.9 would have overstated a competitor by 14 pp** — an error in the opposite direction, and equally unacceptable.
- Scorecard: published 1/12 ERGO wins-or-ties → T17 estimated 7/12 → **measured 3/12** (5/12 only if the unclosable actions cell sits at its ceiling).

**F49 — The whole ordering dispute is inside the noise.** Paired exact sign tests on the same items show **no ERGO-vs-AC3 `tab:main` difference is significant at n≈20 in either direction** (code p=0.375, math p=1.00). This deserves its own line in the paper: it reframes the ERGO comparison from "who wins" to "n≈20 cannot resolve this", which is both true and far more defensible than either ordering.

**Cost note:** ≈$6 across 40 runs against a $0.20 brief. The overage is the comparator arms and the pruned-items probe, logged as deliberate deviations — and it bought the k-measurement that closed the bound, so the deviation was correct. Worth recording that the brief's estimate was wrong, not the agent's judgement.

### Decisions D11–D14 (backfilled 17:30 — see correction note below)

**D11 — Pivot to T14 over the queued T2B (15:10).** T1's F28 showed `adjusted_accuracy` excludes 50–78% of editing-arm failures vs 9% for baseline, with one shipped cell at 89.0% vs 77.1% corrected. An inflated headline table a reviewer can reconstruct is existential; T2B would only add a third evidence tier to a question T2A had already answered non-circularly. Protecting the existing result outranked strengthening an answered point.

**D12 — Dispatch T15 (claims audit → `replies/v5/`) over T2B (15:45).** Tonight invalidated seven claims already written into the rebuttal drafts. Research that never reaches the submitted text is worth zero. Zero API cost.

**D13 — Endorse T14's metric recommendation (16:15).** Report **raw** as primary; keep the pool-level pre-filter as the only FN adjustment (it is arm-symmetric and reproduces `tab:main`'s denominators exactly — **defend it**); **delete per-run `adjusted_accuracy`**; rewrite `tex:478-480`, which claims "all user simulator messages" when the code collates only the visible ones.

**D14 — Final ERGO position (17:10).** Ship corrected ERGO/math **80.0** (beats AC3-Reset 75.0, ties Gated-Reset 80.0) — real, reviewer-visible, must be disclosed. **Do not** ship T17's code 57.9; T18 measured k = 2.67/6, giving ≈43.9 against the published 44.0. Lead the framing with F49: no ERGO-vs-AC3 difference is significant at n≈20 in either direction (code p=0.375, math p=1.00), so report "n≈20 cannot resolve this" rather than any ordering. ERGO/actions is uncorrectable — no sidecar has ever existed.

**Correction to my own bookkeeping.** D11–D14 were written to `logs/orchestrator.jsonl` at the time but never mirrored into this file, and D11 was referenced here without being written out. T19 caught it while working from this log as its source of truth. Backfilled above. **Lesson: the JSONL is the machine log and this file is the human one; a decision recorded only in the former is invisible to anyone reading the latter, which is every downstream agent.**

- **17:30** `T19` returned **DONE**. Commit `0154041`. Log: `tasks/T19/worklog.md`.

**F50 — v5 needed no numeric changes from T14, which vindicates T15's precaution.** No accuracy figure moved: v5 was already raw throughout, which is exactly what the provisional flagging was for. The substantive change is reframing — `tab:main`'s 20/19/25/23 denominators come from an arm-symmetric pool-level pre-filter and are now **defended, not conceded**. T19 added a cross-cutting rule forbidding the FN-metric concession (which v5 makes loudly in five places) from bleeding into an admission that the denominators themselves are wrong. That drift risk was real and worth blocking explicitly.

**F51 — The ERGO disclosure is placed in five locations, each chosen for rhetorical fit:** `00` CW5 (where ERGO is named), `01` W1 (iNYK's own noise complaint, so it reads as vindication rather than concession), `02` W1 (Vg97's central weakness is the baseline set), `04` correction 5, `05` correction 7. Ships math 69.6 → **80.0** and code **≈44.0**. **T17's 57.9 appears nowhere except as an explicit "do not ship" guardrail — verified by grep.** F49 leads the framing throughout, and T19 added a guardrail against the obvious compensating move ("ERGO still loses overall"), since the measured scorecard is 3/12 against a published 1/12.

**F52 — T19 corrected its own draft mid-task, which is the behaviour we want.** It first wrote "we re-ran ERGO on the filtered pools" — an overstatement of T18, whose positive control did *not* reproduce (ERGO/database 44.0 vs published 12.0; `gpt-5-mini` unreachable), so no absolute level is substitutable. Rewritten to "we measured the correction… we replayed ERGO against those excluded items directly", and the reply now says "roughly half" on code rather than quoting 43.9 as if it were a measured level.

**Hold integrity verified mechanically:** all five tau2 `⚠ INTERNAL — HOLD` blocks are **byte-identical** (`git diff | grep '^[-+].*⚠ INTERNAL'` shows zero removed HOLD lines). Adding numbered corrections made the blocks' internal cross-references stale, so T19 appended separate renumbering notes rather than editing sealed blocks — the right call.

**Remaining exposure per T19:** **T6/tau2, and not close.** Everything else is measured or explicitly bounded. Second-order: **U4** ("1 of 11 baseline failures") is unverified *and* characterises a baseline T6 may move, so it must be re-checked in the same pass as T6 rather than after.
- **17:24** Heartbeat tick. All 3 healthy, no intervention. T6 worklog 10m with three `run_parallel.py` workers — now roughly 3h30m in, the longest task of the session by a wide margin, which is expected for agentic tau2 rollouts and consistent with why it was dispatched longest-pole-first. T2B worklog 5m with a baseline arm. T20 dispatched 7 min ago, no worklog yet as expected. No dispatch, no pivot.

- **17:40** `T20` returned **DONE** (zero API calls; every recomputation ran a positive control first, all passed). Log: `tasks/T20/worklog.md`, with drop-in replacement wordings.

**The T16 base rate held: three of four were findable.** That is now twice tonight that "no artifact exists" turned out to mean "the audit did not look hard enough" — worth remembering before we ever strike a claim for unverifiability again.

**F53 — U3 VERIFIED; retire it.** The "72–92%" range is the exact rounded envelope of the 22 populated cells of `tab:wildchat` (min 71.6 Kimi/Reset, max 91.5 Kimi/Rewrite). T20 re-derived **all 22 cells** from per-turn judge verdicts recovered across five snapshot directories — **22/22 reproduce to the digit**. Crucially, **T11's corrections touch no Table 3 cell**: T11 corrected the Phase-3b *pooled* figures (89.8→87.8, 92.1→91.2), which appear nowhere in Table 3, whose gpt-5-mini Reset cell is 83.0. There is no conflict to manage, and **v5 is currently giving away a defensible number.**

**F54 — U5 VERIFIED and strengthened, plus a new defect found and closed.** The AO cells reproduce exactly (90.0, 15.0). But T20 noticed that **T8 re-scored every *other* bigcodebench cell in that row under its unified dependency environment — moving Baseline 1→2 and Reset 4→5 — and never re-scored the AO cell.** Nobody had checked whether the row was internally comparable. T20 re-scored it offline (controls reproduced T8's 5/20 and 2/20): **unchanged at 15.0**, so the row *is* comparable. This is the kind of defect that only surfaces when someone audits the auditor.

Cost to take that column to N=3: **≈$0.20, ~50 min** on two parallel streams. Cheapest open item in the reply set — dispatched as part of T21.

**F55 — U2 recomputed; keep it struck, but for a better reason.** 88.6 (39/44) and 74.1 (43/58) reproduce exactly. **However the two arms were scored on different pools** — 44 vs 58 turns, 35 shared — so **the paper's Table 3 caption ("on the same prefixes") is false as written.** On the matched 35 turns the gap survives (88.6 vs 74.3, +14.3 pp) but rests on seven discordant turns, 6 vs 1, **exact McNemar p = 0.125**. The §7 justification should change from "not order-balanced" — which invites the reply "so re-judge it" — to **non-significance**, which is the real and unanswerable reason. Caption fix queued as **PAPER-8**.

**F56 — U4 is the one genuine casualty; soften it.** The "1 of 11 baseline failures" figure is traceable to `~/ac3/tau2_ctxe/ctx_edit/EXPERIMENT_LOG.md`, commit `169b044` (2026-03-24), with the table verbatim identical to the paper's. But the 20 traces are **gone** — never tracked in git, absent from both tarballs and from disk — and no labels file or rubric ever existed. Two further defects: it is the **45.0% trial, the worst of three {45, 55, 60}**, while the table reports best-of-3, so 11 failures does not reconcile with the reported cell; and n is ambiguous (20 vs 19).

Usefully, T20 established that **U4 is decoupled from T6** — T6's matrix is gpt-5.4/DSV4F/Kimi and gpt-5-mini is only its user-sim/analyzer — so this need not wait on T6. Re-deriving needs a hand-labelling pass that cannot be made defensible overnight: **defer to camera-ready and soften now.** Replacement wording for both `00` and `01` is in T20's worklog. It ran nothing against the tau2 fork, as instructed.
- **17:46** Heartbeat tick. All 3 healthy, no intervention. **T21 moved fast**: Part 1 is already committed (`99e28ba` — U2's reason changed to non-significance, U3's range restored, U4 softened, U5 cleared) and Part 2 is running with two `collabllm_assistant_omit` processes taking the AO column to N=3. T6 worklog 11m, three `run_parallel.py` workers, now ~4h in. T2B worklog 2m with a baseline arm. No dispatch, no pivot.
- **18:01** Heartbeat tick. All 3 healthy and converging, no intervention. T6 worklog 6m with `run_parallel.py` workers down 3 → 2, and T21 down 2 → 1 `collabllm_assistant_omit` — falling worker counts here are replicates finishing, not attrition, since both worklogs are fresh. T2B worklog 17m with a baseline arm. No dispatch, no pivot.
- **18:24** Heartbeat tick. All 3 under threshold, no intervention. T2B worklog 5m with a baseline arm. T6 worklog 29m, two `run_parallel.py` workers. T21 worklog 20m with its `collabllm_assistant_omit` processes now gone — consistent with the offline re-scoring step its brief required (unified dependency environment, from stored `extracted_answer`) rather than idleness, since that step is pure local computation. No dispatch, no pivot.

- **18:30** `T21` returned **DONE**. Commits `99e28ba` (Part 1) and `89dfecf` (Part 2). Log: `tasks/T21/worklog.md`. **UNVERIFIED count 4 → 1** (only U6 survives).

**Part 1 applied:** U3's 72–92% range restored to `03_reviewer_5YHP.md` W1 as its own bullet, labelled as a spread across 22 single-run configurations (binomial sd 4–5 pp each) — never as the win-rate claim, and deliberately never in the same sentence as the 87.8/91.2 headline, which is the confusion that would have invited an attack. U2 kept struck with the reason changed to non-significance. U4 softened in both `00` and `01`. U5 recorded verified. PAPER-8 (the false Table 3 caption) recorded in both `CHANGES.md` and `README.md`.

**F57 — The AO column at N=3 narrows a margin we should therefore stop claiming.** T8's exact config, $0.178, 25 minutes:

| Dataset | rep1 | rep2 | rep3 | mean ± sd | prior N=1 |
|---|---|---|---|---|---|
| MATH-Hard | 18/20 | 17/20 | 18/20 | **88.3 ± 2.9** | 90.0 |
| BigCodeBench (re-scored) | 3/20 | 3/20 | 5/20 | **18.3 ± 5.8** | 15.0 |

Absolutely the cells barely move (<1 problem each), but the BigCodeBench shift narrows **AC3-Reset's margin over assistant omission from +6.7 pp to +3.3 pp** (13/60 vs 11/60 instances) — inside the noise. v5 now **declines to claim that ordering** and rests instead on AC3-Reset over *full context* (+15 pp, 3/3 replicates), which is untouched. Per-problem the two arms succeed on partly different problems, which is the substantive reason not to read 3.3 pp as a ranking at all.

This is the fourth time tonight that adding replicates dissolved a margin we had asserted from N=1 (after math-hard 100%, the memory gains, and the ERGO ordering). The pattern is consistent enough to be worth stating in the paper's limitations: **at n≈20 per cell, this benchmark family cannot resolve differences below roughly 10 pp**, and several of our narrower claims were reading noise.

**Controls, all run before launch:** judge verified live (2/2 AO smoke with real verdicts); canonical-solution preflight 19/20 with `501` failing, matching T8; the re-scorer reproduced T8's 5/20 and 2/20 and T20's 3/20 exactly, and the final pass re-derived T8's full N=3 grids for all four other arms. **New finding:** `BigCodeBench/859` has a **seedless stochastic SVM test** (7 of 8 full-suite passes; 7/7 in isolation) — reported at its mode, disclosed in the reply, no replicate dropped.

**Hold integrity re-verified mechanically:** `git diff 1382e61 HEAD -- replies/v5/ | grep '^[-+].*⚠ INTERNAL'` returns nothing; no blockquote line in v5 was added or removed; the extracted HOLD blocks of `00`/`01`/`04`/`05`/`README` hash identically to pre-T21. T21 also updated `04` and `05` *without renumbering*, deliberately, so the T6 HOLD block's "fifth correction" cross-reference stays valid — a small piece of foresight that will save a reconciliation pass when T6 lands.

- **18:45** `T22` returned **DONE**. `neurips_review/autoresearch/HANDOFF.md` written and committed (`11d8e40`, that file only). Seven sections: bottom line; **14 claims that must change** (each with finding ID, artifact, and whether v5 already fixes it or the paper still needs it); the new results with numbers; the PAPER-1..8 table with effort estimates and a suggested order; T6/T2B still open with no guessed outcomes; the artifact map; and the methodological lessons.

**F58 — The single most important thing for the operator, and it is a coupling nobody had named until now: `replies/v5/` is drafted but NOT postable.** Two halves of one problem:
1. **v5 now discloses the ERGO denominator defect in five places**, which commits us *in front of the reviewers* to a paper fix that **has not been made**. Posting v5 while `tab:main` still shows the old ERGO row would be worse than not disclosing at all — we would be announcing an error and simultaneously demonstrating we had not corrected it.
2. **Five `⚠ INTERNAL — HOLD` blocks remain sealed pending T6**, which has preliminary evidence that the published DSV4F (31.6 → 70.2) and Kimi (26.3 → 80.4) tau2 baselines were degraded floors.

So the highest-value hour available to the operator is **PAPER-7** (the ERGO table fix), and the rebuttal cannot go out before it. Recorded at the top of `HANDOFF.md`.

**Honest balance, kept in the handoff rather than softened:** this session found **more problems with our existing claims than it produced new wins**. Every one of those problems was findable by a reviewer, so finding them ourselves is the good outcome — but the framing should not be dressed up. The core result survived everything: **AC3-Reset and Gated-Reset beat baseline in all 8 LiC cells under raw, shipped-adjusted and arm-symmetric-corrected accuracy alike.**

- **18:40** `T23` returned **DONE**. `tasks/T23/RED_TEAM.md` — 10 HIGH, 15 MEDIUM, 5 LOW, each with quoted text, the attack, and drop-in revision wording. This pass found things three accuracy audits did not, because it asked a different question: not "is this true?" but "what does a hostile reviewer do with it?"

**F59 — ⚠️⚠️ H1: three mutually incompatible full-context baselines for the same benchmark, spread across 52 points.** The paper reports LiC-database full-context at **4.0%** and code at **15.8%**; the reply to iNYK reports **19.0–22.4%**; the answer to the AC's baseline reservation (T1) reports **56.1% / 83.0%**. Nothing in the rebuttal explains the gap. The dilemma a reviewer draws is sharp: either the evaluation changed — and the headline gap shrinks — or the condensation baseline was run in a near-unpolluted regime and therefore **does not answer the AC's concern at all**. This is checkable from documents we are about to hand them. **Dispatched as T24.**

**F60 — H2: AC3-Rewrite is silently missing from the paired table.** `paired_analysis_results.txt` contains a fifth row we did not print: **−0.3 pp, 6 wins / 6 losses.** CW1 says "the same four operators"; the printed table shows the three that win. Rewrite is also precisely the operator 5YHP's W4 was about. Printing three of four rows while claiming four is the kind of omission that, once noticed, colours a reviewer's reading of everything else.

**F61 — H4: operator substitution as a *pattern*.** 5YHP asked about Rewrite and was answered with Augment; iNYK asked about Gated-Reset's 38.7% and was answered with Reset. Our own guardrail says "report best operator per cell." Once a reviewer names that pattern, it reads as a per-cell oracle and discounts every headline in the paper. Individually each substitution is defensible; as a pattern it is not.

**F62 — H5: our biggest under-defended strength.** We tell the AC the FN metric was "biased in our own favour" and **never say Table 1 is unaffected** — even though F40–F42 established its denominators come from an arm-symmetric pool filter, and `README.md` says in terms "defend, not concede." No reviewer-facing sentence defends it. We are conceding ground we already know we hold.

**F63 — H7/H6: two arithmetically checkable errors.** "AC3 beats assistant omission in every [WildChat] cell (22 populated cells)" — 9 of the 22 are against *full context*, and 4×4 ≠ 22. (Inherited from T20's suggested wording, so the error propagated through a verification step — worth noting that a verified *number* can still arrive inside a wrong *sentence*.) And the ERGO paragraph says no difference is resolvable at n≈20 and then asserts three orderings from that same table, one breaching our own guardrail.

Also flagged: **H8** the tau2 failure-mode claim whose traces no longer exist and which traces to the *worst* of three trials iNYK can see in Appendix B.6; **H9** the "only method that improves over full context across the entire spectrum" sentence sitting **outside** every HOLD block while T6 may falsify it; **H10** Vg97 asked for latency and we report the summariser's 13%, not AC3's.

**F64 — The strongest objection against us, stated plainly.** That v5's own concessions have quietly reduced AC3-Reset to *assistant omission plus a spec-extraction call*: preservation 4.0% against a delete-everything control at 0.00, edit precision at chance, the "preserve what's correct" claim withdrawn, and the head-to-head against AO withdrawn on both BigCodeBench and MATH-Hard — leaving a ~2.6 pp average edge over a one-line baseline, plus AO's already-published structural failure on tau2.

The counter-evidence exists — 33/36 vs 31/36 paired; +21 pp over AO on database across three models; the causal factorial; Rewrite's 91.5% on WildChat — **but is never assembled in one place.** That assembly is the highest-leverage writing task remaining, and `RED_TEAM.md` ends with a four-move plan for it.
- **18:46** Heartbeat tick. All 3 healthy, no intervention. T6 worklog 4m with two `run_parallel.py` workers. T2B worklog 27m with a baseline arm. T24 dispatched 5 min ago, no worklog yet as expected. No dispatch, no pivot.

  Housekeeping: corrected the T23 entry header above from 19:00 to 18:40 — I had labelled it ahead of the actual clock. Section headers here are hand-written labels; `logs/heartbeat.jsonl` carries the authoritative timestamps. Fixed so the human log does not drift from the machine log, which is the same class of error as the D11–D14 backfill earlier.
- **19:01** Heartbeat tick. All 3 under threshold, no intervention. T6 worklog 19m with two `run_parallel.py` workers; T24 worklog 5m. **T2B at 42 min** — approaching the threshold but with live `baseline` and `omit_assistant` processes, so the D5/D6 process check clears it. If it breaches next tick the response is a nudge, not a restart, consistent with tonight's record of six nudges and zero necessary restarts. No dispatch, no pivot.

- **19:05** `T2B` returned **DONE**. Artifacts: `tasks/T2B/{RESULTS.md,worklog.md,per_span.json,per_span_alignment.json,+scripts}`, commit `289de75`; `experiment_todos.md` §T2 Tier B marked done (`c83a8a6`). **Cost $62.80** — by far the most expensive task of the session, and the only one where that was warranted: it is the causal gold standard the TODO asked for.

**Scale:** 111 naturally occurring spans across 30 LiC database+code conversations, each re-run **14× present / 12× removed** at temperature 1.0 — 3,357 assistant turns, 0 errors. **No detector, judge, or LLM anywhere in the label-generation path**, which is what makes it immune to the circularity objection.

**Controls pass in both directions** — the design detail that matters most here: contentless span +0.033 (n.s.); T2A's causally-validated pollutant **+0.368** (p=1e-4); full-spec + gold-SQL span **−0.447** (p<1e-4). Probe controls identity 1.000 / nuke 0.000 / other 0.000. MDE 0.333 as an observed difference.

**F65 — Pollution is concentrated, not diffuse.** Point labels (|δ|≥0.25): 11 harmful, 5 useful, 95 inconclusive; per-span identification is weak. But the *aggregate* question is well powered, and against a replicate-matched parametric null (2,000 sims): SD of effects 0.155 vs 0.125 (**p=0.0085**), and 16 large-effect spans where the null predicts 9.3 (**p=0.017**). Mean effect +0.020 [−0.010, +0.048]. So **natural spans do carry real causal effects, concentrated in a ~6% excess minority; the typical span is inert.** That is a genuinely useful characterisation of the phenomenon the paper is about.

**F66 — ⚠️ Alignment: BOTH operators are non-selective on natural spans. This supersedes the Rewrite attribution in F25 and PAPER-5.** AC3-Reset keeps 5/66 probe-admissible spans; **AC3-Rewrite keeps 0/66**. Removal on causally harmful spans 100% (7/7), preservation on causally useful spans 0% (0/4), **edit precision exactly at the base rate (63.6%) for both**. The label-free aggregate test agrees (Reset removed−kept = −0.014, p=0.85).

This **extends** T2A rather than contradicting it, and the explanation is the important part: **Rewrite looked selective on T2A's short injected spans (38.9% preservation) because a compactor can copy a self-contained sentence verbatim. On the model's own verbose prose and code it paraphrases, and nothing distinctive survives.** So T2A's synthetic-injection caveat — which T2A itself flagged as an upper bound — turns out to have been load-bearing in exactly the way it warned.

**Consequence: we must retract the "Rewrite is the selective operator" line from `replies/v5/`.** The honest claim for *both* operators is **rebuild-from-the-user-side, not surgical excision.** Dispatched as T25.

**Limits T2B states itself (8 of them, unusually candid):** most spans are *inconclusive*, and inconclusive ≠ inert; useful spans are structurally under-detectable at LiC's low base rates; the 30 conversations are a headroom-selected high-power subsample, not representative; ~40% of spans lack a unique token and are excluded from the 2×2, so the probe measures *lexical* survival and prose preservation is a lower bound (the 2×2 is repeated on code spans alone); one model, one analyzer, `replay_turns=1`; single-span ablation only, no interactions; Tier C not run.

**F67 — A methodological self-correction worth keeping.** T2B's first empirical null came from the filler control at *mismatched replicate counts* and produced a **false negative**; it was replaced with a matched parametric null. That is the tenth control-caught fault tonight, and the second where the fault was in the *analysis* rather than the harness.

Also unanswerable as specified: the TODO's "close the loop" correlation has a **zero-variance predictor** — both operators removed 100% of harmful spans in all 6 qualifying conversations. Worth noting the TODO's design assumed variation that the method does not produce.
- **19:24** Heartbeat tick. All 3 under threshold, no intervention. T24 worklog 7m with an `omit_assistant` process, consistent with its baseline-reconciliation work. T25 dispatched 18 min ago, no worklog yet. **T6 at 42 min** — approaching the threshold but with two `run_parallel.py` workers live, so the D5/D6 process check clears it; a breach next tick gets a nudge, not a restart. T6 is now the last experiment outstanding in the session. No dispatch, no pivot.

- **19:30** `T24` returned **DONE**. Log: `tasks/T24/worklog.md`, commit `78226bd`.

**F68 — H1 is fully explained, and the explanation is measured rather than argued.** All three baselines are correct measurements of deliberately different populations; the dominant term is **pool difficulty selection**, not model era, evaluator, or metric.

| source | value | population |
|---|---|---|
| paper | 4.0 / 15.8 | GPT-5-mini, last-turn replay, `dev_{task}_subset` — **top-25 items by GPT-5-mini baseline failure rate** (≥60% error over 5 runs; 75 eligible → 25 kept, per `docs/lic_dev_set_provenance.md`). **4.0% = 1/25 is what the construction guarantees**, not an independent measurement. |
| iNYK reply | 19.0–22.4 | three newer models, last-turn replay, `htn50_52` (top-50 by GPT-5.2 true-negative rate), **with replay prefixes deliberately weighted toward baseline failures** (74–86% on database, per `curate_valid_prefixes.py`). A floor by construction. |
| T1 | 56.1 / 83.0 | gpt-5.4-mini, **full end-to-end** sharded simulation, the **complete unselected pool** (107/100). |

**Verified by direct restriction, not inference:** restricting T1's own baseline run to the paper's exact 25 items — same model, evaluator, protocol — gives 56.1 → **32.0** (database) and 83.0 → **48.0** (code). Independently, LiC's released logs put GPT-5-mini at 29.9% on the whole 107-item pool vs 4.0% on its top-25 subset. **Two routes to a ~25 pp selection effect, agreeing within 2 pp.** No case of the same setup producing two numbers.

**F69 — T1 still answers the Area Chair; no re-scoping needed.** T24 ran the ceiling arms T1 lacked. On the unselected pool the fully-specified single-turn ceiling is **94.4% database / 98.0% code** (positive control: LiC's own `full` band for this pool is 89.7–98.1%). So T1's venue carries a **38.3 pp / 15.0 pp** multi-turn gap, and AC3 closes **51% / 60%** of it — **the same fraction as on the paper's much harder pool (50%)**.

That is the sentence that kills the objection: **baselines move 52 points across venues; gap-closure moves 4.** And condensation got no easy ride — it scores *below* full context in every venue.

**F70 — ⚠️⚠️ Worse than H1, and found on the way: we answer iNYK's own complaint with a false statement.** `01_reviewer_iNYK.md:31` says the 36-comparison matrix is on "the full, non-difficulty-selected pool". **It is not.** Difficulty selection is precisely what iNYK complained about, and we assert the opposite about our new headline evidence. If a reviewer checks one claim in the rebuttal, this is the one they check.

The fix is a straight swap rather than a retraction: **T1 is the experiment that genuinely satisfies the claim** (complete unselected pool, end-to-end). Draft replacement wording is in T24's §7. Routed to T25, which is already editing that tree — dispatching a second editor onto the same files would risk the double-write class of corruption we hit earlier tonight.

- **19:45** `T25` returned **DONE**. Commit `edbda19`. Log: `tasks/T25/worklog.md`.

**Part 1 — retraction shipped.** The "we preserve what's correct" re-attribution to Rewrite is retracted **for both operators** across `02` Q4, `03` W5, `04` correction 3, `05` correction 3, `README.md`, and `CHANGES.md`. **PAPER-5 rewritten** from "attribute to Rewrite" to "delete the framing", with a note that **the ERGO differentiation argument changes too** — that consequence had not occurred to me, and it matters: "unlike prior work that discards all assistant messages" was how we distinguished ourselves from ERGO, and T2B says we largely *do* discard them.

The reconciliation ships in the reviewer-facing text (a compactor copies a short *injected* sentence verbatim but paraphrases the model's own prose), so T2B reads as an **extension** of T2A rather than a reversal, and T2B is presented as *answering* 5YHP's W5 — pollution is real and concentrated (0.155 vs 0.125, p=0.0085), AC3 removes 100% of causally harmful spans.

**F71 — Part 2: the case is assembled, and it leads with the concession.** New CW2 subsection, "Where AC3 separates from assistant omission, and where it does not", plus a summary in the AC letter. It opens with the wash — matrix-wide head-to-head **+2.6 pp, 15 W / 17 L / 4 T** — then the concentration: **database +18.7 pp, 8 of 9**; tau2 AO 0% structural; WildChat every populated cell; framed as a decision procedure over operators indexed by referentiality.

**Note against myself:** my brief told T25 "+21 pp over AO on database". **T25 recomputed it as 18.7 pp and printed the measured value.** I had carried +21 forward from an earlier summary without re-deriving it. The agent verifying its orchestrator's numbers rather than trusting them is exactly the behaviour that should be rewarded, and it is the eleventh number tonight that moved when someone actually checked.

**F72 — H10 answered with a number recovered at zero API cost.** Vg97 asked for AC3's latency and we had been reporting only the summariser's. T25 recovered AC3's own wall-clock from `outputs/T1/main/*/experiment.log`: Reset is **+82% end-to-end but +9% per turn** once turn inflation is separated, against the summariser's +19%. Separating the two is the honest presentation — the end-to-end figure is dominated by AC3 producing more turns, not by slower turns.

**HIGH items applied:** H2, H3, H4, H5, H6, H7, H8, H10. **T24's routed work also landed**: the false *"full, non-difficulty-selected pool"* claim in `01` W2 is fixed, and the three-way baseline reconciliation is now in `00`, `01`, `02`, `04`, `05`. T24's two paper-side items queued as **PAPER-9/PAPER-10**.

**Still open:** **H9** — the tau2-dependent "improves across the entire spectrum" sentence — recorded as **README Blocker 5** with pre-drafted fallback wording and deliberately **not** applied, since T6 may falsify it. M11, M12, M6, M3, M15 need runs; the rest deferred as survivable or tone calls.

**HOLD integrity:** all eight `⚠ INTERNAL` blocks verified byte-identical by **per-block SHA-256** against `d24a2db` — a stronger check than the grep used in earlier passes.
- **19:46** Heartbeat tick. T6 healthy (worklog 15m, `run_parallel.py` workers 2 → 1, converging). T26 healthy — editing `HANDOFF.md` directly per its brief, touched 4 min ago.

  Slot free and the queue empty, so dispatched **T27**: triage the five MEDIUM red-team items T25 flagged as needing runs (M11, M12, M6, M3, M15), then execute only the ones that pass triage, cheapest-first, under ~$15. The instruction that matters most is to **decline any item whose entire value is a sub-10 pp ordering at n≈20** — four such margins dissolved tonight once replicates were added, so buying another would be spending compute to manufacture a claim we would later have to retract. Declining with a cost estimate is an acceptable outcome for every item.

### Decisions D15–D19 (backfilled 19:55 — I repeated the D11–D14 mistake)

**D15 — Never strike a claim for unverifiability without a documented deep search.** Twice tonight (T16/U1, T20/U3+U5) "no artifact exists" meant "the audit did not look hard enough". Striking a true claim costs us a defensible number for nothing.

**D16 — At n≈20 per cell this benchmark family cannot resolve sub-10 pp differences.** Four asserted margins dissolved once replicates were added: math-hard 100% → tied; memory +10/+12 pp → below a ~6 pp noise floor; the ERGO ordering → nothing significant either way; AC3-Reset-over-AO +6.7 → +3.3 pp. This belongs in the paper's limitations as a stated resolution limit, not as four separate retractions.

**D17 — Run the adversarial read as well as the factual audit.** T23 found in one pass what three accuracy audits missed, because it asked "what does a hostile reviewer do with this?" rather than "is this true?" Both H7 and the 22-cell error were **inherited through** a verification step: a verified *number* can arrive inside a wrong *sentence*.

**D18 — Route follow-up work to the agent already in the tree.** T24's fixes went to T25 by message rather than to a new agent, because two writers on `replies/v5/` is the double-write pattern that corrupted output dirs at 10:14–10:52.

**D19 — Briefs must cite finding IDs so agents can re-derive rather than inherit.** My T25 brief said "+21 pp over AO on database", carried forward from an earlier summary without re-derivation; T25 recomputed 18.7 pp and printed the measured value. An agent checking its orchestrator's numbers is correct behaviour.

**Repeat offence, recorded deliberately.** I backfilled D11–D14 at 17:30 after T19 flagged them, stated the rule "any decision in the JSONL must also be written into WORKLOG.md prose", and **then broke it again for D15–D19**, which T26 caught. The lesson is not "remember harder" — it is that a rule enforced only by the actor who keeps breaking it does not hold. The durable fix is to write the decision into this file **in the same command** that appends to the JSONL, which is what I am doing from here.

- **19:55** `T26` returned **DONE**. `HANDOFF.md` refreshed and committed (`701f6b6`, that file only).

**F73 — T26 verified against `WORKLOG.md` rather than trusting my brief, and corrected it in three places.** (i) The eight `⚠ INTERNAL` blocks are the *total*, of which **five** are tau2 HOLDs pending T6 — the rest are a preamble and two renumbering notes; I had implied all eight were tau2 holds. (ii) `README.md` carries **six** numbered blockers, three resolved and three open, **plus PAPER-7, which is the real blocker and is not in that list** — a gap worth knowing about, since someone working the numbered list would miss the one that actually gates posting. (iii) The session runs to D19, and D15–D19 existed only in the JSONL; the artifact map now flags that.

**The operator's order of business, per T26:**
1. **PAPER-7 (~1–2 h) — the only thing blocking the post.** v5 discloses the ERGO denominator defect in five reviewer-facing places; posting before the `tab:main` fix means announcing a correction we have not made.
2. **PAPER-5 has flipped, and the knock-on needs human judgement.** T2B killed the Rewrite attribution (Rewrite keeps 0/66 natural spans, *worse* than Reset's 5/66). "Preserve what's correct" is deleted for both operators — and "unlike prior work that discards all assistant messages" was the ERGO differentiation. **That is a contribution-framing decision, not a number edit**, which is exactly why it should not be made by an agent.
3. **T6 is the last unsettled result.** Five HOLDs plus Blocker 5 stay sealed until it lands. Its 19:32 self-report has hardened but is **not integrated or audited** — T26 deliberately did not resolve it.

Cheapest high-value item after PAPER-7: **PAPER-9, ten minutes**, on the `tab:main` caption covering the 52-point baseline spread — the discrepancy a reviewer is most likely to catch unaided.
- **20:01** Heartbeat tick. Both healthy, no intervention, nothing to dispatch (queue empty). T6 worklog 30m with one `run_parallel.py` worker, converging. **T27 is working well**: worklog 2m, already committed `6396b31` resolving **M3 and M15 at zero API cost**, and now running `mtosc_w2` and `summarize_v1` for the items that genuinely need measurement. That is the triage doing its job — separating what can be settled from artifacts from what actually needs compute, rather than running all five reflexively.

**D20 — Adversarial-reader output is a hypothesis list, not a patch set.** T27 found that **two of `RED_TEAM.md`'s own suggested fixes are false** and must never be posted. The red team wrote its wording under time pressure without running anything; its *attacks* were excellent, its *proposed replacements* need the same verification as any other claim. (Logged to `logs/orchestrator.jsonl` in the same command, per the D15–D19 lesson.)

- **20:05** `T27` returned **DONE**. Log: `tasks/T27/worklog.md` (triage table, results, drop-in wording in §6), commit `6396b31`. **Cost $19.60**, $4.60 over guidance.

**Triage outcome — three run, two declined, and the declines are as valuable as the runs.** M3 and M15 ran at **$0** (data was already on disk / in the snapshot). **M6 (human validation) declined**: a human study cannot be recruited overnight and a stand-in would be worse than the acknowledged gap. **M12 split**: MT-OSC w=2 run (cheap, already implemented, answers an objection *we* supplied); **U-Fold declined** — hours adapting someone else's method, T6 still live on that fork, and the red team's own remedy was to *offer* it rather than run it.

**F74 — ⚠️ Two of the red team's suggested fixes are false and must not be posted.**
1. M3's proposed line *"the analyzer cache was disabled for these runs"* is **wrong** — `context_edit_v2_gated.yaml` sets the cache path and `run_exp1_reps.sh` never overrides it. The true answer is both correct and **stronger**: **39/39 conversations have differing analyzer outputs across the three replicates**, the two failing problems are a *different pair* each run (intersection 0), and turn counts and answers differ on 7 and 5 of 40. That is positive evidence of genuine replicate variation, where the proposed wording was an unverified excuse.
2. M11's proposed line *"it degrades with more budget (−2.8 → −8.4 pp), which is itself the mechanism prediction"* — T27's replicate of the **1-call** arm scores **47.7%, exactly the 2-call value**, and the two 1-call runs differ by *more* (p=0.29) than 1-call differs from 2-call (p=0.26). **Fifth margin to dissolve under replication tonight.** Print "neutral-to-negative", not a mechanism story.

**F75 — M11 (neutral condenser) closes the AC's central reservation.** Neutral prompt **51.4%** vs full context 56.1%, landing *between* the two replicates of our own prompt — so the condensation result does not depend on our prompt's wording. AC3-Reset **+24.3 pp** (31/5), Gated-Reset **+22.4 pp** (30/6). The decisive detail: **the condenser flags an assistant error 0/340 times** with the "find errors" clause removed — identical to with it. Probe validated (26.4% on AC3 analyzer output, 0% on baseline turns). A summariser does not audit, whatever you tell it.

**F76 — M12: MT-OSC w=2 engages 9× more and still loses.** Fix verified live (`raw_pairs_carried` 133 vs the buggy run's 0). Scores **47.7%, −13.1 pp vs w=4** (p=0.016); AC3-Reset +28.0 pp. So the earlier "MT-OSC barely fires" defence is no longer needed — making it fire *more* makes it worse.

**F77 — M15 replaces the sign test with intervals, and supplies a guardrail against ourselves.** AC3-Reset **+15.4 pp, 95% CI [+11.5, +19.4]**, 350 W / 93 L over 1,668 items; both controls exact. The guardrail matters: **do not quote the matrix-wide Reset-vs-AO McNemar (p=0.010) as a win** — it ignores clustering, and the clustered CI is **[−0.3, +5.9]**. Database is [+10.7, +26.6]. This is consistent with T25's assembled case (a wash overall, concentrated on database) and stops us re-introducing a claim we already retired.

**On the overspend:** T27 sized from a 3-sample smoke rather than T1's comparable $7.70–12.39 cells, then cancelled the marginal second-venue cell once it noticed. The estimate was wrong, not the decision — the money went to the decisive item.
- **20:24** Heartbeat tick — **T6 nudge #2** (first was 13:01). Its worklog hit 53 min, a genuine threshold breach, and its `run_parallel.py` workers are gone. Under D6 a restart needs mtime > 45 min *and* no process *and* no recent writes; the write probe is unreliable (D8), and T6 holds roughly **six and a half hours** of agentic tau2 rollouts that a restart would destroy unrecoverably. So: nudge to converge and return partial results, explicitly forbidding new replicates.

  The most important thing I asked for is **whether its positive control reproduced**. A teammate's control did not (ERGO/database 44.0 vs published 12.0) because `gpt-5-mini` is unreachable tonight, which meant no re-run's absolute level was substitutable into the paper. For T6 the distinction between *"the published tau2 baselines were wrong"* and *"these are not comparable measurements across model eras"* **is the entire finding**, and the second answer stated clearly is worth more than the first stated loosely. Five HOLD blocks and README Blocker 5 cannot be resolved either way without it.

  T28 dispatched 19 min ago, no worklog yet as expected. Queue empty; nothing to dispatch.

- **20:35** `T6` returned **DONE** — the last experiment of the session, and the most consequential. Full published matrix, nothing skipped: 3 models × 5 arms × 3 replicates × 19 tasks = **855 scored rollouts**, 15/15 cells at 60/60, same hyperparameters and model identities as the committed sweep scripts. Log: `tasks/T6/worklog.md`; clone at `~/ac3/tau2_ctxe`.

**F78 — ⚠️⚠️⚠️ Two of three published tau2 baselines do not replicate, and the tau2 story inverts.** DSV4F **31.6 → 70.2 ± 11.0**; Kimi **26.3 → 78.9 ± 0.0**. **On all three models the remeasured Baseline is at or above every AC3 arm.**

| Model | Baseline | AO | Augment | Gated-Reset | Rewrite |
|---|---|---|---|---|---|
| gpt-5.4 | **68.4 ± 13.9** | 0.0 | 47.4 ± 5.3 | 57.9 ± 21.1 | 47.4 ± 5.3 |
| DSV4F | **70.2 ± 11.0** | 0.0 | 50.9 ± 8.0 | 57.9 ± 10.5 | 57.9 ± 13.9 |
| Kimi-K2.6 | **78.9 ± 0.0** | 0.0 | 57.9 ± 9.1 | 71.9 ± 11.0 | 66.7 ± 8.0 |

Paired vs Baseline (57 pairs, exact sign test): Augment −21.1 (p=.008) / −19.3 (p=.043) / −21.1 (p=.012); Gated-Reset −10.5 / −12.3 / −7.0 (n.s.); Rewrite −21.1 (p=.012) / −12.3 / −12.3; AO −68 to −79 pp (p<.0001).

**F79 — This is "the published baselines are wrong", not "not comparable" — and that distinction was tested, not assumed.** The positive control **reproduced**: gpt-5.4 Baseline 68.4 vs published 68.4, and AO 0.0 across 9 cells / 171 rollouts vs published 0/0/0. `gpt-5-mini` *was* reachable for T6 (dl-openai-1 + dl-openai-3), invocation strings byte-identical, no model substitution. Supporting evidence that the old cells were **degraded controls** rather than a shifted environment: the AC3 arms on those two models replicate well, T6's runs terminate 60/60 and 59/60 `user_stop`, and **the source report itself already concedes Kimi's baseline was rate-limit-clipped** (14/20 short-exits, described there as "floors, not honest performance").

So the honest position is: **the tau2 comparison must be withdrawn.** AC3 does not beat full context on tau2 on any of the three models once the baseline is measured properly. The one tau2 result that survives and is worth keeping is **AO → 0.0 across all 9 cells / 171 rollouts**, which is structural and reproduces exactly.

**F80 — The gpt-5.4 AC3 collapse is unexplained, and T6 says so rather than papering over it.** Augment 84.2 → 47.4 while that model's *baseline* reproduced exactly. T6 ruled out model substitution, gating, terminations and rate limits. It also found a **real fork bug** — 53% of analyzer Q1 calls fail tag extraction and splice escaped JSON into the context (`analyzer.py:89-95`) — but fixing it moved accuracy only **+2.3 pp**, so that is not the explanation either. An unexplained 37-point drop on our own arm is a genuine open problem and belongs in the camera-ready as one.

**F81 — `--seed` genuinely threads on the tau2 fork** (`run_parallel:131` → `orchestrator:526-528` → `llm_config.py:41-48` → litellm), unlike LiC's inert `cfg.seed`. Best-effort provider seed only, so ship as "N=3 replicate runs (seeds 42/43/44)". The gpt-5.4 Gated-Reset regression **reproduces in direction** (57.9 ± 21.1 vs 68.4; paired −10.5 pp, p=0.24) — kept, not dropped, not upgraded.

**D21 — Withdraw the tau2 magnitude table; keep only the AO structural result.** The five sealed `⚠ INTERNAL — HOLD` blocks and README Blocker 5 exist precisely for this outcome and their withdrawal wording is pre-drafted. This removes a benchmark that was front and centre in the General Response and the AC letter, which is a real loss — but publishing a comparison against a control we can now demonstrate was rate-limit-clipped would be indefensible, and the clipping is already conceded in our own source report. (Logged to `logs/orchestrator.jsonl` in the same command.)

- **20:55** `T28` returned **DONE**. All of T27's items applied, `RED_TEAM.md` inoculated, and **the tau2 withdrawal (D21) landed**. Log: `tasks/T28/worklog.md`. Zero API calls.

**Applied:** M11 replaces the "did not finish in the window" concession with the result in `00` CW5, `02` Q1, `04`, `05` — neutral condenser 51.4% vs full context 56.1%, landing between our own prompt's two replicates (53.3 / 47.7), AC3 +24.3 / +22.4 pp, and **0 errors flagged in 340 summaries** with the clause removed. M12's measured result now leads the "barely fires" one-liners in `04`/`05`. M15's clustered CIs are in five places. M3 ships the measured answer only — **the false cache clause is written nowhere**. M6 is one undressed sentence.

**F82 — The guardrail held under pressure, and it mattered.** The matrix-wide Reset-vs-AO McNemar p=0.010 appears in **no** reply text; only the clustered CI **[−0.3, +5.9]** with "which is why we do not claim it", codified in `CHANGES.md` §8 rule 6b and `README.md`. T28 checked this against T25's CW2 subsection and found the cell-level +2.6 pp / 15-17-4 and the new item-level +2.8 pp agree — **but had it quoted the p-value, the two sections would have contradicted each other.** That is the cross-file tension the red team warned about, caught before it shipped.

**F83 — Three reconciliations, one of which corrects a teammate.** (i) T27's M11 second paragraph withdrew a budget-ordering claim **v5 never made**; T28 kept every number but reframed it as "do not read this as a mechanism" rather than staging a fake retraction of something we had not said. (ii) "Not powered for significance" contradicted M3's p=0.023 — reworded in `00` CW3 and `01` Q1. (iii) Correction counts moved 5→6 and 7→8.

**tau2 withdrawal applied** across `00` CW1+CW4, `01` W3, `02` W2/Q2, `04` correction 6, `05` correction 8, `README`, `CHANGES` §12.3. AO = 0.0 kept; the gpt-5.4 Gated-Reset regression kept and not upgraded; the gpt-5.4 collapse disclosed as unexplained. H9's fallback wording applied, closing README Blocker 5.

**Hold-integrity audit, the strongest of the session:** per-block SHA-256 from `d989c50` shows **all nine regions byte-identical through the entire T27 pass** (`hold_baseline.txt`; only line numbers shifted). Phase-2 unsealing was my explicit instruction and is recorded separately from phase 1, so the record distinguishes "sealed and untouched" from "deliberately opened". `grep "⚠ INTERNAL"` now returns only `00`'s orientation preamble.

**Session status: every experiment and every edit pass is complete.** Nothing is in flight. Remaining work is consolidation.

**D22 — Run a coherence pass distinct from the adversarial read.** `replies/v5/` has been through **eight editing passes**, several reversing earlier ones, each verifying only its own change. Nobody had read it end to end since assembly, and T28 already caught one near-miss of exactly this kind. Dispatched **T30** to fix unambiguous staleness and list judgement calls for the operator, and **T29** for the final `HANDOFF.md` refresh — stale at 72 of 83 findings and still presenting the tau2 question as open when it is now the session's largest single change. (Logged to `logs/orchestrator.jsonl` in the same command.)
- **20:46** Heartbeat tick. T29 and T30 dispatched 9 min ago; no worklogs yet, which is expected. **0 live processes, and that is correct** — both are zero-API writing/reading tasks with no subprocess signature, so `pgrep` is uninformative for them and worklog mtime is the only usable liveness signal. Worth noting explicitly because the same reading on an *experiment* task would be a stall indicator; the check has to be interpreted against what the task actually does.

  Queue empty, every experiment complete, no dispatch, no pivot. The session is now purely in consolidation: `HANDOFF.md` refresh and the end-to-end coherence pass over `replies/v5/`.

- **20:55** `T29` returned **DONE**. `HANDOFF.md` refreshed in place at F1–F83 / D1–D21, committed alone (`60b9e3f`). It verified every claim against `WORKLOG.md` and the task worklogs rather than my brief, and correctly left T30's uncommitted `replies/v5/` edits untouched.

**F84 — ⚠️ New top-level item: `replies/v5/` is rewritten around the tau2 withdrawal, but the *paper* is not.** That is now **PAPER-11**, and it is much larger than the other paper items because tau2 is threaded through the whole document: **abstract, Fig. 1, introduction, `tab:megatable`, the tau2 results section, discussion, and conclusion**. I had been tracking the withdrawal as a rebuttal edit; it is also a substantial paper edit, and nobody had said so until T29 traced it.

Importantly, **PAPER-11 does not block posting** — it is a *withdrawal*, so it is camera-ready-mandatory rather than rebuttal-blocking. **PAPER-7 (the ERGO `tab:main` fix, 1–2 h) remains the only item that gates posting**, because v5 commits us to that correction in front of the reviewers in five places.

**The counterweight, which T29 correctly places in the same breath rather than in a separate "positives" section:** T27/M11 closed the Area Chair's baseline reservation — neutral condenser 51.4% vs full context 56.1%, landing between our own prompt's two replicates, AC3 +24.3 / +22.4 pp, and **0 errors flagged in 340 summaries** with the "find errors" clause removed. M15 gives +15.4 pp, 95% CI [+11.5, +19.4]. **All eight LiC cells still win under raw, shipped-adjusted and corrected accuracy alike.**

Left unsmoothed, as it should be: gpt-5.4's tau2 AC3 collapse (84.2 → 47.4) is unexplained, and the real fork bug found accounts for only +2.3 pp of it.

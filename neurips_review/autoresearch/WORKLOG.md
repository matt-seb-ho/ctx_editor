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

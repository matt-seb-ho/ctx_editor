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

# T1 — Condensation / summarisation baseline at matched call budget

**Reviewer prompt:** Area Chair "limited baselines" + Vg97 W1/Q1. We currently *argue* that
compaction / folding methods target context-length pressure rather than context pollution.
One run at the boundary converts that scoping argument into an empirical claim.

**Prediction (registered before running):** a faithful summariser carries invalidated reasoning
forward in compressed form and therefore does **not** close the multi-turn gap. If it does close
the gap, that is a real negative result for us and gets reported as such.

**Status:** in progress (2026-07-29 overnight session). **Operator asleep — no questions asked.**

---

## 0. Decisions taken up front (all ambiguity resolved here)

**D1 — venue.** LiC `database_v2` + `code_v2`, N=30 each (the full `data/lic_eval_subset.json`
slice per task). **No math**: session 1's T5 equal-budget control was run on near-ceiling math,
all arms landed at ~97.5%, and the experiment was non-discriminating. T2c independently shows
code/database are where the headroom is (baseline 22–32% on the informative subsets) while math
sits near ceiling.

**D2 — what the summarisation baseline is.** A *generic, non-analyzer* LLM condenser of the kind
production agent harnesses use for context-length management. Every turn it compresses the
conversation and the assistant proceeds from the condensed context.

**D3 — the fairness constraint that makes this an experiment rather than a strawman.** The
summariser is told to compress **faithfully**. It is never told to find errors, judge
correctness, remove invalidated reasoning, or drop the assistant's wrong approach. It is
explicitly told the opposite: *"Your job is compression, not evaluation… Preserve the
assistant's current approach and conclusions as they stand."* If it were told to drop wrong
reasoning it would just be AC3 and the comparison would be vacuous. Full prompts are reproduced
verbatim in §A so a reviewer can check we did not handicap it.

**D4 — plumbing parity.** `SummarizationStrategy` builds its replacement context with exactly
the same structure AC3-Reset / AC3-Rewrite use — `[system] + [compacted conversation] +
[latest user message]`, same `role="compacted conversation"` tag, same `trace.reset_conversation`
call, same `min_turns=1`. The *only* thing that differs between the summarisation arm and the
AC3 arm is the text of the replacement message. This is deliberate: it isolates "what the
replacement says" from "how replacement is plumbed in".

**D5 — call budget.** Measured, not asserted (see §2). AC3-Reset's `ConversationAnalyzer` is a
**two-query** flow (Q1 task spec from user messages only, Q2 comparison) → **2 extra LLM calls
per fired turn**. So we run *two* summarisation arms:
- `summarize_v1` — 1 condenser call/turn (the natural form; **under** AC3's budget).
- `summarize_v1_2pass` — condense + a faithfulness-refinement pass = **2 calls/turn, exact call
  parity with AC3-Reset**. Its only purpose is to close off "you gave the baseline half the
  compute". The refinement pass checks the *summary against the transcript*, never the
  assistant's work against the task.

**D6 — analysis cache disabled for the AC3 arms** (`experiment.strategy.analysis_cache_dir=null`).
Two reasons: (a) a cache hit means no LLM call, which would silently understate AC3's measured
budget and destroy the whole point of the measurement; (b) `outputs/analysis_cache` is shared
with two other agents running concurrently tonight. The cache key does include `analyzer_model`
(`analyzer.py:585`), so no stale-hit correctness risk existed — this is purely about clean
measurement and write contention.

**D7 — output isolation.** Everything under `outputs/T1/`. Concurrent agents share the
`outputs/` tree and have already caused one double-write corruption incident, so every cell gets
a task-scoped `logging.output_dir` and `metrics.json` is cross-checked against `run_summary.json`
before any number is trusted.

**D8 — FN-analysis model.** `false_negative_analysis.model=gpt-5.4-mini_2026-03-17` on every
cell. The default is not served on TRAPI and silently no-ops on every incorrect sample, which
deflates accuracy with no error raised. (RECON's worklog names `gpt-4o_2024-11-20`, which is
also served; the task brief specifies gpt-5.4-mini and that is what is used, uniformly across
all arms, so the adjustment is at least internally consistent.)

**D9 — replicates.** `seed=` is inert on LiC (`cfg.seed` is read only by `huang_eval/`).
Variation would come from `temperature: 1.0` only. N=1 per cell for now; if the sweep finishes
early, reps are added and called "replicate runs", never "seeds".

---

## 1. What was built

| file | what |
|---|---|
| `src/ctx_editor/strategies/summarization.py` | `SummarizationStrategy` — the condensation baseline. `num_passes ∈ {1,2}`. |
| `src/ctx_editor/strategies/prompts/summarize_v1.txt` | condenser prompt (verbatim in §A) |
| `src/ctx_editor/strategies/prompts/summarize_v1_refine.txt` | faithfulness-refinement prompt for the 2-call parity arm (verbatim in §A) |
| `src/ctx_editor/config/experiment/summarize_v1.yaml` | 1 call/turn arm |
| `src/ctx_editor/config/experiment/summarize_v1_2pass.yaml` | 2 calls/turn (budget-parity) arm |
| `src/ctx_editor/utils/call_meter.py` | process-global call/token meter (see §2) |
| `neurips_review/autoresearch/tasks/T1/run_t1.sh` | the sweep launcher |

Reuse audit, as instructed: `ContextCompactionStrategy` (`ac3_rewrite_v8_lic`) was read first.
It could **not** be reused as-is — it hard-wires a `ConversationAnalyzer` stage-1 and templates
the analyzer's `user_intent`/`aligned`/`issues` into the rewriter prompt, i.e. it *is* an
analyzer-driven method. Making it non-analyzer would have meant a `analyzer=None` code path
through `prepare_context` plus a bypass of the `compaction_analysis` logging — more invasive
than a 200-line strategy that mirrors its `_build_*_context` / `reset_conversation` structure
exactly. The new class is a deliberate structural copy of it minus the analyzer.

---

## 2. Budget measurement (this is a measurement, not an assertion)

Nothing in the repo measured strategy-side LLM cost: `UsageStats` only records the
`user` / `assistant` / `system` roles (`core/simulator.py`), so analyzer and rewriter calls were
invisible in `metrics.json` and `results.json`. Added `utils/call_meter.py`:

- a process-global accumulator hooked into `OpenAIModelClient._parse_response` — the single
  choke point every OpenAI-dialect response passes through;
- attribution via a `contextvars` tag so concurrent async conversations do not clobber each
  other's labels. `user_agent`, `system_agent`, `analyzer`, `context_compaction` and
  `summarization` tag their own calls; anything untagged defaults to `assistant`;
- dumped to `<run_dir>/call_meter.json` **before** false-negative analysis (so the numbers
  describe the experiment, not the post-hoc adjustment) and to `call_meter_final.json` after.

Verified on the smoke run (`outputs/T1/smoke_summarize_db`, 2 database samples, `summarize_v1`):
total 28 calls / 29,046 tokens, split `assistant` 8, `system` 8, `user` 6, `strategy` 6 — and
6 strategy calls is exactly the number of summarisation events logged in the traces. The meter
is consistent with the trace logs.

---

## 3. Smoke test (2 database samples, `summarize_v1`)

Ran before the sweep. Raw 1/2, adjusted 1/1 (the miss was FN-classified user-sim-induced).
The condenser output is a good-faith faithful summary — it reproduces the schema, the user's
two shards verbatim, **and the assistant's prior SQL unchanged**, with "Current state: the
initial approach was to find the match with the maximum `minutes`." That is precisely the
behaviour the experiment is designed to test: the prior approach is carried forward in
compressed form rather than audited.

---

## 4. Sweep

Launcher: `neurips_review/autoresearch/tasks/T1/run_t1.sh` (idempotent — skips any cell whose
`run_summary.json` already exists). Cells run **sequentially** at `execution.max_concurrent=5`;
TRAPI capacity is shared with two other agents tonight, so no parallel cells.

Order is deliberate — the core result lands first in case the session runs out of time:

1. `db_baseline` 2. `db_summarize1` 3. `db_reset`
4. `code_baseline` 5. `code_summarize1` 6. `code_reset`
7. `db_summarize2` 8. `code_summarize2`
9. `db_gated` 10. `code_gated`

Canonical command (all cells identical modulo `experiment=` / `task=` / dir):

```bash
ctx-editor \
  experiment=summarize_v1 \
  model=gpt5_4_mini_trapi \
  load_balancer=trapi \
  task=database_v2 \
  user_mode=sharded \
  execution.max_concurrent=5 \
  false_negative_analysis.model=gpt-5.4-mini_2026-03-17 \
  experiment_name=T1_db_summarize1 \
  logging.output_dir=outputs/T1/db_summarize1
```

AC3 cells add `experiment.strategy.analysis_cache_dir=null` (D6).

Launched 2026-07-29 ~11:52. Progress log: `neurips_review/autoresearch/tasks/T1/run_log.txt`.

---

## 5. Pilot (n=30, `data/lic_eval_subset.json`) — and why the venue changed

Ran 12:05–12:20. Artifacts kept at `outputs/T1/pilot_n30/`.

| task | arm | acc |
|---|---|---|
| database | Baseline | 53.3% (16/30) |
| database | Summarisation, 1 call/turn | 60.0% (18/30) |
| database | AC3-Reset | 66.7% (20/30) |
| code | Baseline | **93.3% (28/30)** |

**Decision D10 — abandon `lic_eval_subset.json`, move to the full LiC pool
`data/sharded_instructions_600.json`.** LiC-code baseline at 93.3% is *at ceiling*: two
errors of headroom cannot discriminate between four treatment arms. This is precisely the
failure mode that wasted session 1's T5 (near-ceiling math, all arms ~97.5%, non-discriminating),
and the brief was explicit that repeating it would be a waste. The full pool gives **n=107
database and n=100 code**, with no baseline-failure selection bias (unlike
`htn50_52_*`, which is selected on baseline failure and would regress to the mean), and its
code half is 55% LiveCodeBench vs 43% in the 30-sample subset — i.e. genuinely harder.

Larger n was preferred over N=3 replicates at n=30: 107 independent samples beat 90
observations over 30 reused ones, and `seed=` is inert on LiC anyway (D9).

All 19 `db_id`s required by the 107-sample database pool are present in
`data/spider/databases/` (checked before launching). The pilot's database ordering is a prefix
of the full pool, so nothing is lost.

**Operational near-miss, recorded as a warning for other agents.** Stopping the pilot with
`pkill -f "ctx_editor.run_experiment\|ctx-editor"` would have killed **two other agents'
T9 runs** sharing this box. It happened not to, only because `pkill` uses ERE and `\|` was
matched literally. **Kill T1 processes by PID, never by `pkill -f ctx-editor`.**

---

## 6. MT-OSC (arXiv:2604.08782) — reimplemented

The brief listed MT-OSC as optional-if-time and warned against a half-faithful reimplementation.
Assessment: **it is specified concretely enough**, so it was implemented — it is the closest
published analogue to what the AC meant by "compaction baseline", and it evaluates on the *same
sharded LiC datasets we use* (GSM8K, Spider, BFCL, HumanEval).

*MT-OSC: Path for LLMs that Get Lost in Multi-Turn Conversation* — Singh, Tu, Ballesteros, Sun,
Ghoshal, Yuan, Benajiba, Ravi, Roth (Oracle AI), arXiv:2604.08782v3, 2026-06-01. **No code
release** (no availability statement, no repo link anywhere in the paper).

What it does: a **Condenser** (one few-shot LLM call producing a single synthetic
user/assistant pair from a window of `w` pairs), a rule-based **Decider** (no LLM) that can
withhold condensation on information-dense dialogues, and a schedule that runs the condenser
**as a background process**, so the condensation computed at turn `T_j` is only used from turn
`T_j + 1`.

Faithful: Appendix B.1 condenser prompt **verbatim**; the three few-shot exemplars transcribed
from Figure 2 (they exist only as a rasterised figure, and the authors call the exemplar set
"central to maintaining nuanced context"); the JSON `HumanInput`/`Assistant`/`Reasoning`
contract with `Reasoning` discarded; the Appendix B.3 schedule including the one-turn lag and
the recursion `C_j = Condense({C_{j-1}} ∪ new pairs)`; γ=0.2, τ=1000; decoding settings from B.1.
The schedule was generalised to arbitrary `w` as trigger at `T_j = (w-1)j + 2`, usable from
`T_j + 1`, `C_j` covering raw pairs `1 … (w-1)j+1`; substituting w=4 reproduces the paper's
turn-by-turn walkthrough exactly (trigger 5/8/11, used from 6/9/12, `H_6 = {C_1,(u_5,a_5)}`,
`H_9 = {C_2,(u_8,a_8)}`).

Not determined by the paper, and recorded rather than hidden:

1. **The Decider's polarity is self-contradictory in the paper.** §3 prose: the rule fires on
   high redundancy and "condensation is *withheld* to avoid potential loss". The
   Combined-Operation equation says the opposite (raw history *if D_w is False*). We implement
   the prose. **This is inert on LiC and measured, not assumed**: τ=1000 user tokens over `w`
   turns is never approached — LiC sharded user messages give `user_tokens` of 10–12 per window
   in the smoke run — so the Decider never fires under either reading. Every decision is logged
   (`mtosc_decider`) so the trigger rate is reportable.
2. Stopword list / lemmatiser / tokeniser behind "normalized content words" are unnamed. Inert,
   per (1).
3. The exemplar concatenation format is unstated; the B.1 skeleton is followed literally.
4. The paper's condenser is Llama-3.3-70B-Instruct. We run the condenser on gpt-5.4-mini, the
   same model every other arm's context operator uses, because matched-model is the point of the
   comparison. The paper's §5.3 reports MT-OSC is insensitive to the condenser model. Also,
   gpt-5 deployments force `temperature=1.0`, so the paper's `temperature=0.01` cannot be
   honoured; and we pass `reasoning_effort=medium` to match the other arms (generous to the
   baseline).

**Structural point worth putting in the rebuttal regardless of the numbers.** At the paper's
headline **w=4, MT-OSC does not touch the context before turn 6.** The authors say as much —
their Spider ≥6-turn subset is n=6. LiC conversations here average ~4–5 turns, so w=4 is a
near-no-op. **w=2** (the smallest window in the paper's own sweep, w ∈ {2,3,4}) intervenes from
turn 4 and is the informative configuration; both are run. Pollution in LiC starts at turn 2–3,
which is *earlier than MT-OSC's earliest possible intervention* — a scheduling fact, independent
of how good the condenser is.

Also relevant, from the paper's own results: aggregated over its 10 datasets the accuracy change
is **not significant** (Wilcoxon signed-rank, p=0.118); the authors' own framing is "efficiency
without compromising on performance". Its abstract frames the problem as context-window
exhaustion, latency and cost — i.e. context *length*. Pollution appears only as a secondary
claimed side effect (§5.1, Appendix E), and their own Appendix E example shows the condenser
carrying a fabricated value forward.

Smoke run (`outputs/T1/smoke_mtosc`, 4 database samples, w=2) behaves exactly to spec:
condensation at turn 3, applied at turn 4, recursion at turn 4 over `{C_1} ∪ pair 3`, Decider
never withholding. The condenser output compresses the assistant's SQL to prose ("Provided an
SQL query joining Treatments and Professionals, selecting …") — carrying the approach forward
without auditing it, which is the behaviour under test.

Bug found and fixed during the smoke: `str.format` cannot be used on the condenser template
because the Figure-2 exemplars embed literal JSON braces; use `str.replace`.

---

## 7. Main sweep (full pool)

Launcher `neurips_review/autoresearch/tasks/T1/run_t1_main.sh`, output `outputs/T1/main/`,
log `run_log_main.txt`. Launched 2026-07-29 12:05. Idempotent (skips completed cells).

7 arms × 2 tasks, sequential at `execution.max_concurrent=5`:
Baseline, Summarisation-1call, Summarisation-2call (budget-matched), MT-OSC w=2, MT-OSC w=4,
AC3-Reset, AC3-Gated-Reset. Database first (the discriminating venue).

---

## 8. Results

**Status line (2026-07-29 12:50, live):** main sweep running, 3/16 cells done. Not wedged —
the pilot processes were deliberately killed at 12:04 when the venue changed (D10) and
everything since runs under `outputs/T1/main/` via `run_t1_main.sh` (PID-tracked, log
`run_log_main.txt`). Remaining: 4 more database arms, then 7 code arms, then 2 robustness
arms. ETA ~15:30. Next action after that: `analyze.py` → `RESULTS.md`.

### 8.0 Zero/low-score sanity controls

A standing warning from a sibling task: two harness bugs elsewhere **silently returned 0.0**
instead of erroring, so a real 5/20 read as 0/20. Controls in place here:

1. **Positive control by construction.** The Baseline arm on each task is run through the
   *identical* harness, task evaluator and FN pipeline as every treatment arm. Baseline scoring
   56.07% on database and 93.3% on the code pilot proves the evaluator, the Spider execution
   path and the extraction path all work. Any treatment arm reading 0.0 while baseline reads
   non-zero would therefore be a strategy-side fault, not an evaluator fault.
2. **Cross-file consistency assert.** `analyze.py` asserts `results.json` correct-count ==
   `metrics.json.correct` and `metrics.json.accuracy` == `run_summary.json.metrics.accuracy`
   for every cell before using any number, and refuses to build the table otherwise. This is
   the check that caught the earlier double-write corruption incident.
3. **Error accounting.** `metrics.json` separates `errors` (excluded conversations) from wrong
   answers; the first MT-OSC smoke run surfaced exactly this way — `0.00% (0/0) (4 errors
   excluded)` from a `str.format` crash on the condenser template, not a silent zero.
4. No arm has produced a suspiciously low score so far. If one does, it will be re-run with
   `logging.verbose=true` on 3 samples and the traces read before any number is reported.

### 8.1 Database results — COMPLETE (n=107, paired, 1 run per cell)

`data/sharded_instructions_600.json`, filter=database, gpt-5.4-mini TRAPI, sharded user sim.
**Raw accuracy is the primary metric** — see §8.3 for why the repo's `adjusted_accuracy` is
*not* comparable across these arms.

| Arm | Acc (raw) | correct/n | Δ vs baseline | 95% CI | W/L | McNemar p |
|---|---|---|---|---|---|---|
| Baseline (full context) | 56.1% | 60/107 | — | — | — | — |
| Summarisation, 1 call/turn | 53.3% | 57/107 | **−2.8pp** | [−10.5, +5.7] | 10/13 | 0.678 |
| Summarisation, 2 calls/turn (budget-matched) | 47.7% | 51/107 | **−8.4pp** | [−14.2, −0.0] | 6/15 | 0.078 |
| MT-OSC (reimpl.), w=4 as published | 60.7% | 65/107 | +4.7pp | [−3.6, +11.5] | 13/8 | 0.383 |
| **AC3-Reset** | **75.7%** | 81/107 | **+19.6pp** | [+9.2, +26.1] | 28/7 | **0.0005** |
| **AC3-Gated-Reset** | **73.8%** | 79/107 | **+17.8pp** | [+7.6, +24.3] | 26/7 | **0.0013** |

Head-to-head, paired: AC3-Reset − Summarisation-1call = **+22.4pp** (31 W / 7 L, p=0.0001);
AC3-Reset − Summarisation-2call = **+28.0pp** (36/6, p<0.0001); AC3-Reset − MT-OSC-w4 =
**+15.0pp** (21/5, p=0.0025).

**The registered prediction holds, and more strongly than expected.** Faithful condensation does
not close the gap — it does not move accuracy at all (−2.8pp, p=0.68), and *doubling* its budget
makes it worse (−8.4pp). Meanwhile the identical plumbing driven by an analyzer gains +19.6pp.

### 8.2 Measured budget — parity is a measurement, not an assertion

From `<run_dir>/call_meter.json`, snapshotted before FN analysis. 107 conversations per cell.

| Arm | total calls | strategy calls | strategy calls/conv | strategy tokens | total tokens | avg turns |
|---|---|---|---|---|---|---|
| Baseline | 1222 | 0 | 0.0 | 0 | 874,226 | 4.1 |
| Summarisation, 1 call/turn | 1558 | 336 | 3.1 | 559,644 | 1,596,358 | 7.3 |
| **Summarisation, 2 calls/turn** | 1909 | **678** | 6.3 | **1,268,902** | 2,294,569 | 7.3 |
| MT-OSC w=4 | 1258 | **30** | 0.3 | 51,711 | 940,225 | 4.3 |
| **AC3-Reset** | 1879 | **666** | 6.2 | **781,968** | 1,682,405 | 6.9 |
| AC3-Gated-Reset | 1483 | 276 | 2.6 | 330,333 | 1,204,787 | 5.3 |

**Ratios, stated rather than rounded to "comparable":**

- Summarisation-2call vs AC3-Reset: **1.02× the strategy calls (678 vs 666)** and **1.62× the
  strategy tokens (1.269M vs 0.782M)**. The budget-matched summariser therefore consumed
  *more* compute than AC3-Reset and still lost by 28.0pp. This is a stronger statement than
  equal-budget: the baseline was over-budgeted and still lost.
- Summarisation-1call vs AC3-Reset: 0.50× calls, 0.72× tokens. Under budget — which is exactly
  why the 2-call arm exists.
- AC3-Gated-Reset reaches +17.8pp on **0.41× AC3-Reset's strategy calls** and 0.22× the
  summarisation-2call arm's strategy tokens.
- **MT-OSC w=4 fired only 30 times across 107 conversations (0.3 calls/conv).** At w=4 it cannot
  touch the context before turn 6; LiC-database conversations average 4.1 turns under baseline.
  Its +4.7pp (p=0.38) is a near-no-op, and that is a structural fact about its schedule, not a
  quality judgement on its condenser.

### 8.3 Incidental finding — `adjusted_accuracy` is invalid for cross-arm comparison

**This affects the paper's own headline numbers, not just T1.** Worth escalating.

`identify_false_negatives.analyze_sample` builds the user-sufficiency judge's prompt from
`get_active_messages(trace)`, which returns **visible** messages only
(`identify_false_negatives.py:191-193, 228-229`). After any context reset the visible user
messages are the condensed text plus the latest shard — so the judge is shown a *truncated* user
history and concludes "the user never specified X", marks the sample user-sim-induced, and
`compute_adjusted_accuracy` drops it from the denominator.

The exclusion rate is therefore a function of the treatment — textbook post-treatment
conditioning — and scales with how aggressively an arm discards user text:

| arm | incorrect analysed | excluded as user-sim-induced | raw | adjusted |
|---|---|---|---|---|
| Baseline | 47 | **4** (9%) | 56.1% | 58.3% |
| MT-OSC w=4 (near-no-op) | 42 | **3** (7%) | 60.7% | 62.5% |
| AC3-Gated-Reset | 28 | 14 (50%) | 73.8% | 84.9% |
| AC3-Reset | 26 | 16 (62%) | 75.7% | 89.0% |
| Summarisation 1-call | 50 | **39 (78%)** | 53.3% | 83.8% |
| Summarisation 2-call | 56 | **43 (77%)** | 47.7% | 79.7% |

The two arms that leave the context alone exclude 7–9%; every context-editing arm excludes
50–78%. The user shards are *identical* across arms and revealed by the same user agent, so a
genuine user-sim failure rate cannot differ 9× by treatment.

**Consequence to state plainly, because it cuts against us:** under the repo's canonical
`adjusted_accuracy` the summarisation arm reads 83.8% against AC3-Reset's 89.0% — a 5pp gap
instead of 22pp. That metric is wrong for this comparison, but a reviewer running our own
pipeline would see it, so T1 reports raw as primary, prints adjusted alongside, and explains
the confound rather than quietly dropping the column.

**Planned correction (§10):** re-run the sufficiency judge with the *complete* user-message
history read from `trace.messages` (which retains hidden messages), which is the arm-symmetric
input the check was always meant to have.

### 8.4 Zero/low-score controls — one fired, and it caught a real bug

Control 1 (baseline as positive control through the identical evaluator), control 2
(`analyze.py` asserts `results.json` ↔ `metrics.json` ↔ `run_summary.json` agreement on every
cell before any number is used) and control 3 (errors separated from wrong answers) are as
described above. They fired twice:

1. **First MT-OSC smoke** reported `0.00% (0/0) (4 errors excluded)` — surfaced as *errors*, not
   as a silent zero. Cause: `str.format` on the condenser template, which embeds literal JSON
   braces from the Figure-2 exemplars. Fixed with `str.replace`.
2. **`db_mtosc_w2` returned 26.2% against a 56.1% baseline** — a 30pp drop, well outside
   anything the method could plausibly cause. Per the standing instruction this was treated as a
   fault until proven otherwise, and it *was* a fault — see §9.

Every other cell is within a plausible band and the consistency asserts pass on all of them.

---

## 9. Bug found by the low-score control — commit `c1dd523`

**What it was.** MT-OSC's Combined Operation is
`H_{w+2} = {(C_ju, C_ja)} ∪ {(u_k, a_k)}_{k=t}^{w+1}`, and the paper's own w=4 walkthrough gives
`H_6 = {C_1, (u_5, a_5)}`: pair 5 is *not* covered by `C_1` (which covers pairs 1–4) and stays
raw. My reset rebuilt the context as `[system] + C_j + [latest user message]`, dropping every
pair completed between the condensation trigger and its application. At w=2 that silently
deleted **a whole user shard per condensation**.

Concrete instance (`sharded-spider-val-1008-medium`): the user says "only filter singers born in
1948", then "or you could include singers born in 1949 too". Both shards were discarded; the
final answer was `SELECT Name FROM singer WHERE Birth_Year = <birth_year>` — a placeholder,
because the assistant no longer had a year. Cost: **26.2% vs a 56.1% baseline**.

**Why it mattered beyond MT-OSC.** A misrepresented baseline is worse than an absent one, and
this one would have been misrepresented by 30pp in *our favour*. Had it shipped, MT-OSC would
have appeared catastrophically bad and the whole "we tested the closest published compaction
method" claim would have been indefensible on inspection of the traces.

**Scope check — does it affect the summarisation arms? No.** `SummarizationStrategy` re-reads
the *entire* conversation every turn and replaces the context with a summary covering everything
up to the latest user message; nothing can fall between a window and its application because
there is no window. Same for AC3-Reset, whose analyzer sees the full conversation and which
additionally rebuilds its task spec from `get_user_messages_string(all_unique=True)`. The bug
was specific to MT-OSC's windowed, lagged schedule.

**Fix.** Carry the raw pairs completed after the condensation window:
`carry = self._window_pairs(trace)[pending["n_pairs_condensed"]:]`, spliced in between the
condensed pair and the latest user message. Verified on a fresh 4-sample smoke run:
`mtosc_applied {'j': 1, 'turn': 4, 'raw_pairs_carried': 1}` and the raw pair is visible in the
final context. The buggy run is preserved at `outputs/T1/main/BUGGY_db_mtosc_w2/` and
`db_mtosc_w2` is being re-run post-fix. `db_mtosc_w4` ran **after** the fix and is clean.

---

## 10. Still outstanding

- `db_mtosc_w2` re-run post-fix (the buggy run is archived, not deleted).
- All 7 code arms (n=100) — `code_baseline` started 13:46.
- Both `summarize_v2_neutral` robustness cells.
- Arm-symmetric FN re-judge (§8.3) using the full user-message history.

---

## A. Appendix — the summariser prompts, verbatim

Reviewers will want to check the baseline was not handicapped, so both prompts are reproduced
in full. Source of truth: `src/ctx_editor/strategies/prompts/summarize_v1.txt` and
`summarize_v1_refine.txt`.

### A.1 `summarize_v1.txt` (the condenser — used by both summarisation arms)

```
You are condensing a multi-turn conversation so that it fits in a smaller context window.

The AI assistant in this conversation will continue working on the task. It will see ONLY the summary you produce, plus the system prompt and the most recent user message; it will not see the original conversation history. Your summary must therefore carry forward everything needed to continue seamlessly.

Write a faithful, information-preserving summary. Include:
- Every requirement, constraint, value, name, and detail the user has provided so far, stated precisely.
- What the assistant has done so far: the approach it is taking, the reasoning behind it, and any intermediate results, code, queries, or answers it has produced. Reproduce code, SQL, formulas, and specific values verbatim where they matter.
- The current state of the work and what remains to be done.
- Any assumptions, decisions, or clarifications that have been made during the conversation.

Guidelines:
- Be faithful to the conversation. Report what was actually said and done; do not add information that is not there, and do not invent details.
- Your job is compression, not evaluation. Do not judge whether the assistant's work is correct, do not critique it, and do not attempt to solve the task yourself. Preserve the assistant's current approach and conclusions as they stand.
- Preserve detail wherever removing it would lose information the assistant needs. Compress by removing redundancy, conversational filler, and repetition — not by dropping substance.
- Use whatever structure, sectioning, and length best preserves the content.

## System Prompt (for context; already visible to the assistant, do not repeat it)
{system_message}

## Conversation So Far
{conversation}

Wrap your final summary in <summary>...</summary> tags. Only the content inside those tags will be shown to the assistant.
```

### A.2 `summarize_v1_refine.txt` (second pass, budget-parity arm only)

```
You are reviewing a draft summary of a multi-turn conversation for FAITHFULNESS and COMPLETENESS before it replaces the conversation history.

The AI assistant in this conversation will continue working on the task and will see ONLY this summary, plus the system prompt and the most recent user message. If the summary omits or garbles something, that information is lost.

Compare the draft summary against the original conversation and produce a revised summary that fixes:
- Omissions: user-provided requirements, constraints, values, names, or details that are missing from the draft.
- Inaccuracies: anything the draft states that does not match what the conversation actually says.
- Lost specifics: code, SQL, formulas, numbers, or intermediate results that were dropped or paraphrased away and should be reproduced precisely.
- Missing state: what the assistant is currently doing, the reasoning behind it, and what remains to be done.

Guidelines:
- You are checking the summary against the transcript, not checking the assistant's work against the task. Do not judge whether the assistant's approach or answers are correct, do not critique them, and do not attempt to solve the task yourself. If the assistant took an approach, the summary should say so faithfully.
- Do not add information that is not in the conversation.
- If the draft is already faithful and complete, return it essentially unchanged.

## System Prompt (for context; already visible to the assistant, do not repeat it)
{system_message}

## Conversation So Far
{conversation}

## Draft Summary
{draft_summary}

Wrap your final revised summary in <summary>...</summary> tags. Only the content inside those tags will be shown to the assistant.
```

**Design tension recorded honestly.** The clause *"Your job is compression, not evaluation"* is
load-bearing in both directions. Without it, a strong model summarising a conversation may
spontaneously start auditing the assistant's work — which would make the arm a partial
reimplementation of AC3 and make a positive result uninterpretable. With it, a reviewer could
argue we forbade the baseline from doing the useful thing. We keep it, because the claim under
test is specifically "generic condensation ≠ pollution removal", and a condenser that removes
pollution is not a generic condenser. The sentence is also standard in real compaction prompts
(faithfulness instructions are the norm). If the result is null, the honest framing is: *the
gain comes from the audit, not from the compression* — which is exactly the paper's claim, and
the prompt makes that separation legible rather than hiding it.

### A.3 `summarize_v2_neutral.txt` (robustness arm — no "compression, not evaluation" clause)

Added so the result does not hinge on one prompt's wording. `summarize_v1` explicitly tells the
condenser not to evaluate; a reviewer could argue that clause forbids the baseline from doing
the useful thing. This prompt is deliberately minimal and takes no position either way, leaving
the model free to audit the assistant's work if it spontaneously chooses to.

```
Summarize the conversation so far so that it can replace the conversation history.

The assistant will continue this conversation and will see only your summary, the system prompt, and the most recent user message.

Preserve the important details: what the user has asked for, what has been done so far, and the current state of the work.

## System Prompt (for context; already visible to the assistant, do not repeat it)
{system_message}

## Conversation So Far
{conversation}

Wrap your summary in <summary>...</summary> tags. Only the content inside those tags will be shown to the assistant.
```

### A.4 MT-OSC condenser prompt

Not reproduced here because it is not ours: it is Appendix B.1 of arXiv:2604.08782 verbatim,
plus the three Figure-2 exemplars transcribed. The exact file we send is
`src/ctx_editor/strategies/prompts/mtosc_condenser.txt` and it should be diffed against the
paper rather than against anything we wrote.

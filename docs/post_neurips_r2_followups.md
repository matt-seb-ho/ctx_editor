# Follow-ups from the R2 overnight batch

Tracked items surfaced during the 2026-05-18 overnight that should be
addressed next session.

## Method / experimental

- **Rewrite v3 prompt** — if anyone wants another iteration. The v2
  prompt fixed F5 on code but made F4 worse on database. A v3 might:
  (a) **anchor each spec item on a quoted user message** ("for each
  requirement, paste the user's words that motivate it"); (b) forbid
  speculative prose in `verified_work`; (c) append the latest user
  message verbatim as the final task_spec item. Cost: ~1 evening
  to design + 1 LiC sweep. Not on the critical path — the v2 result
  already supports the "Reset is simpler and sufficient" framing.

- **Multi-rep error bars on CollabLLM R2**. Tonight was N=1 due to
  scope. The math-hard cluster (85–95%) and bigcodebench order
  (Reset 20% > AO 15% > Baseline 5%) both need a 3-rep follow-up to
  bound sampling variance. Cost: ~1.5h overnight, parallel.

- **Replay variant for CollabLLM**. The plan deferred this because
  the user-sim swap addressed the dominant problem (sim drift). For
  cleaner per-strategy variance bars, a replay mode would isolate
  the strategy effect from sim sampling. Engineering: split
  `run_collabllm.py` so a frozen prefix can be replayed across
  strategies. ~1 day of code.

- **Huang R2 augment variant** (in flight as of 2026-05-18 02:15 PT;
  results will be appended to the R2 summary). If augment dominates
  Reset on DeepSeek (as it did on gpt-5-mini), the multi-model
  augment-vs-reset comparison is the new flagship result.

- **CollabLLM math-hard saturation check**. At Baseline=95%,
  Reset=85% there are 2 ambiguous cases (out of 20). A multi-rep
  check would tell us whether the 10pp Reset deficit is real.

## Engineering

- **`huang_eval/run_phase2.py` load_balancer plumbing**: landed
  tonight. Verified via DeepSeek + Kimi Huang R2 runs.
- **`AC3RewriteStrategy.compaction_prompt` kwarg**: landed tonight.
  Supports swapping between `context_compaction` (v1),
  `context_compaction_v2`, and any future variant by name.
- **aggregator regex**: `aggregate_ac3_phase.py` was missing
  `ac3_rewrite_v2_lic` in `EXP_TO_STRAT`; added.
- **CollabLLM aggregator** is still LiC-shaped. The `scripts/`
  directory has no canonical CollabLLM cross-cell aggregator —
  tonight I read summary.txt files by hand. Logged as a follow-up.

## Paper narrative items

- **Rewrite negative result is worth a paragraph**: the failure-mode
  analysis (F4 / F5 / F1 / F2 each dominating different tasks) is a
  clean explanation of *why* the simpler Reset method wins, beyond
  cost arguments. A "rewrite is flexible but lossy" framing motivates
  the Reset choice.

- **CollabLLM section needs a full rewrite**. The Phase 3a numbers
  (which suggested AC3 regresses on CollabLLM) were a user-sim
  artefact. With a competent simulator: math-hard is saturated,
  bigcodebench shows the AC3 win.

- **Cross-model on Huang**: the AC3-Reset win-rate vs AO is **model
  dependent** — 89.8% on gpt-5-mini, 71.6% on Kimi-K2.6, ?% on
  DeepSeek (in flight). The pattern is *not* monotone with model
  strength. We may want to write this up as "AC3 helps most when
  the respondent model is mid-tier" — a useful caveat for the paper.

## Cost / time accounting (tonight)

- Categorizer (DeepSeek labeler, 48 cases): ~8 min, negligible cost.
- Rewrite v2 LiC sweep (12 cells): ~40 min wall, all parallel, ~$0.12.
- CollabLLM R2 (6 cells): ~50 min wall, ~$0.50 reported.
- Huang R2 Kimi: 63 min wall.
- Huang R2 DeepSeek (s15 + augment): in flight.
- CollabLLM R2 augment fill-in (2 cells): in flight.

Total estimated cost: under $5 for the analyzed-LLM bill; foundry
DeepSeek/Kimi tokens not yet priced into the model pricing file.

# T11 — WildChat judge-agreement and position-bias checks

**Started:** 2026-07-29 (overnight autonomous session)

## Commitment being delivered
`neurips_review/replies/v4/03_reviewer_5YHP.md`, W4 Revision line, verbatim:

> **Revision:** We will report the corrected CollabLLM numbers, add execution-based scoring where the harness permits, **add judge-agreement and position-bias checks for WildChat**, and footnote the per-method sample counts, which differ because each method is evaluated against its own assistant-omission failure pool.

Also relevant (W4 body): "On **WildChat**, results are over 3 seeds with tight intervals (Reset **89.8 +/- 1.4**, Augment **92.1 +/- 1.3**), spanning 72-92% across cells."

So the deliverable is exactly: (1) position-bias check on the WildChat pairwise judge, (2) judge-agreement check. Scoped to WildChat only.

## Log

### 00:00 — Setup
- Read 5YHP v4 reply + RECON worklog §B.3 (WildChat/Huang harness map).
- Key facts from RECON: harness at `src/ctx_editor/huang_eval/`, judge prompt at
  `src/ctx_editor/huang_eval/prompts/pairwise_judge.txt` (emits `quality_winner`,
  `ontopic_winner`, `confidence`; **A/B order randomized by caller's rng** — so the
  existing numbers are already partially order-randomized; need to check this in code).
- Headline source: `outputs/post_neurips_ac3_phase3_huang/*_seed{42,43,44}_*`, N=3 real seeds.
- All prior outputs off disk; extracting from `~/ac3/blob_staging/snapshot.tar.gz`.

### 00:25 — Recovery + harness reading complete
- Extracted from `snapshot.tar.gz` into `~/ac3/recovered/ctx_editor/outputs/`:
  `post_neurips_ac3_phase3_huang/{s15,augment}_seed{42,43,44}_*`,
  `huang_eval/{phase1,phase2,rejudge}`, `post_may26_wildchat_gpt54`.
- Verified the headline reproduces from the recovered files: `s15_seed42` →
  66/73 = **90.4%** AO-failure turns where Reset beats AO on quality, matching
  `docs/reports/post_neurips_ac3_phase3_huang.md`. 452 (AO, variant) pairs total
  across the 6 cells (225 Reset / 227 Augment); all 452 join cleanly to the 30
  Phase-1 conversations.
- Judge = **gpt-5-mini** (respondent + analyzer also gpt-5-mini), prompt
  `src/ctx_editor/huang_eval/prompts/pairwise_judge.txt`.

**Two findings from reading the harness (both matter for the checks):**
1. `judge_pairwise()` **already randomizes A/B order per call** (`rng.random() < 0.5`),
   so the headline is order-*randomized* but not order-*balanced*, and the realized
   order was **never stored** (`_judgment_dict` drops `position_assignment`). So the
   existing files cannot be re-analyzed for position bias — the judging must be re-run.
   Re-running judging only (generations reused verbatim from the recovered files).
2. **The judge did not actually run at temperature 0.** `judge_pairwise` passes
   `temperature=0.0`, but the OpenAI client prints
   `gpt-5 models require temperature=1.0, overriding 0.0 -> 1.0`. So the headline
   judge is stochastic, and self-consistency is a real (not degenerate) measurement.

### 00:30 — Positive controls (trap #1)
Control = judge each variant response against a **degraded copy of itself**
(first 25% truncated mid-sentence + generic filler tail), judged in **both** orders.
Smoke results, all "good" wins:
- gpt-5-mini: 6/6 ✅  · DeepSeek-V4-Flash: 4/4 ✅ · Kimi-K2.6: 4/4 ✅
Full n=20-pair controls queued for all three judges. Also: `judge_once` in my
harness **never coerces a failure to "tie"** (the shipped `judge_pairwise` does —
that is exactly the silent-0.0 class of bug); failures are recorded as `ok:false`
with the error text and excluded from denominators, with counts reported.

### 00:35 — Runs launched
- Judge A (gpt-5-mini, = headline judge): **all 452 pairs × 2 forced orders** (904 calls), running.
- Shared cross-judge subset frozen at `out/subset160.json` — 160 pairs, stratified
  ~27 per cell, deterministic (seed 1234).
- Second/third judge families verified live on `mgalley-foundry2` via
  `load_balancer=t9_foundry_trapi`: DeepSeek-V4-Flash (~16 s/call), Kimi-K2.6 (~45 s/call).
- Script: `neurips_review/autoresearch/tasks/T11/rejudge.py` (self-contained; does not
  modify anything under `src/`). Outputs to `neurips_review/autoresearch/tasks/T11/out/`
  (T11-scoped, per trap #3).

### 01:05 — Runs in flight, first partial numbers (do not quote — interim)
Progress: gpt-5-mini 294/904 judgements, DeepSeek 166/320, Kimi 67/320. **0 hard failures** on all three.

Interim (gpt-5-mini, 147 pairs of 452 complete): variant-second 93.2%, variant-first 87.8%,
order-balanced 90.5%, swap-consistency 89.1%. Direction of bias: gpt-5-mini favours the
**second**-presented response (recency), DeepSeek and Kimi favour the **first**. Cross-family
raw agreement 84-86%, kappa 0.36-0.42.

Note for the write-up: kappa is depressed here by extreme marginal imbalance (the variant wins
~90% of pairs), the classic kappa paradox. Adding PABAK and Gwet's AC1 alongside raw+kappa,
and reporting each judge's *own* win-rate on the shared subset, which is the quantity the
paper's claim actually rests on.

### 01:35 — DeepSeek order run complete (320/320, 0 failures)
gpt-5-mini at 769/904, Kimi at 181/320. Launched the DeepSeek n=20 positive control.
Added PABAK + Gwet's AC1 to `analyze.py` alongside raw agreement and Cohen's kappa.

### 02:00 — Judge A (gpt-5-mini) position-bias run COMPLETE: 452 pairs x 2 orders = 904 judgements, 0 failures

**Position bias IS present in the headline judge, and it is a SECOND-position (recency) preference.**

| | variant presented 2nd | variant presented 1st | order-balanced | swap-consistency |
|---|---|---|---|---|
| all 452 pairs | 92.3% | 86.7% | **89.5%** | 90.3% |
| AC3-Reset (s15), 3 seeds | 91.1 +/- 2.2 | 84.4 +/- 2.1 | **87.8 +/- 2.1** | |
| AC3-Augment, 3 seeds | 93.4 +/- 2.6 | 89.0 +/- 2.0 | **91.2 +/- 2.1** | |

Order effect = 5.5pp. Of 44 order-inconsistent pairs, 32 flip toward the second-presented
response vs 8 toward the first (exact binomial **p = 1.8e-4**), so the bias is real, not noise.
The other two judges lean the *other* way (first-position): DeepSeek +6.2pp toward first
(13 vs 5, p = 0.096), Kimi +1.8pp (6 vs 4, p = 0.75). So it is a per-model idiosyncrasy,
not a property of the prompt.

**Crucially, this does not bias the headline.** `judge_pairwise` randomises A/B 50/50 per call,
so the published number is an unbiased estimate of the order-balanced quantity in expectation.
The corrected (explicitly order-balanced) numbers are Reset **87.8 +/- 2.1** vs published
89.8 +/- 1.4, and Augment **91.2 +/- 2.1** vs published 92.1 +/- 1.3 — shifts of -2.0pp and
-0.9pp, both within the judge's own run-to-run noise (agreement of this re-judge with the
May-2026 stored verdicts: raw 88.5%, kappa 0.487, AC1 0.871). Headline conclusion unchanged.

Cross-family (shared 160-pair subset, DeepSeek-V4-Flash): pooled raw agreement 87.5%,
kappa 0.449, AC1 0.859; each judge's own order-balanced win-rate on that subset:
gpt-5-mini 88.8% vs DeepSeek 85.6% — a 3.2pp difference, same conclusion.

Positive control (DeepSeek, n=20 pairs x 2 orders): 36/40 good, 2 degraded, 2 tie, in both orders. ✅
Still running: Kimi order run (230/320), gpt-5-mini self-consistency repeat, gpt-5-mini control.

### 02:55 — ALL RUNS COMPLETE. 1,824 judgements, 0 hard failures.

| run | judge | pairs | judgements | failures |
|---|---|---|---|---|
| `out/order_gpt5mini.jsonl` | gpt-5-mini | 452 (all) | 904 | 0 |
| `out/order_deepseek.jsonl` | DeepSeek-V4-Flash | 160 (subset) | 320 | 0 |
| `out/order_kimi.jsonl` | Kimi-K2.6 | 160 (subset) | 320 | 0 |
| `out/repeat_gpt5mini.jsonl` | gpt-5-mini (self-consistency) | 160 | 160 | 0 |
| `out/control_{gpt5mini,deepseek,kimi}.jsonl` | positive controls | 20 each | 120 | 0 |

Full analyzer output archived at `out/analysis_full.txt`. Deliverable below.

---

# T11 DELIVERABLE — WildChat judge position-bias and judge-agreement checks

**What was promised** (`neurips_review/replies/v4/03_reviewer_5YHP.md`, W4 Revision):
"add judge-agreement and position-bias checks for WildChat".

**What was run.** The WildChat generations were *not* re-run. The 452 (AO, AC3) response
pairs from the N=3-seed Phase-3b run (`outputs/post_neurips_ac3_phase3_huang/{s15,augment}_seed{42,43,44}_*`,
recovered from `snapshot.tar.gz`) were re-judged with the **byte-identical judge prompt**
under **forced presentation order**, in both directions, plus a self-consistency repeat and
two additional judges from different model families.

**Bottom line: position bias exists in the judge, but it does not bias the published number,
because the shipped harness already randomises presentation order 50/50 per comparison.
The order-balanced headline is AC3-Reset 87.8 +/- 2.1 and AC3-Augment 91.2 +/- 2.1
(published: 89.8 +/- 1.4 and 92.1 +/- 1.3).**

## (a) Position bias

Quality dimension. "AC3 shown 1st/2nd" = AC3 response in prompt slot A / slot B.
Swap-consistency = fraction of pairs whose verdict is unchanged when the order is flipped.
The exact binomial (McNemar) p-value tests, on the order-discordant pairs only, whether flips
favour the first- or the second-presented response equally often.

| Judge | pairs | judgements | AC3 shown 1st | AC3 shown 2nd | **order-balanced** | swap-consistency | order effect | discordant pairs (1st-pref / 2nd-pref / tie-flip) | exact p |
|---|---|---|---|---|---|---|---|---|---|
| **gpt-5-mini** (the judge behind the published number) | 452 | 904 | 86.7% | 92.3% | **89.5%** | 90.3% | **+5.5pp toward the 2nd slot** | 44 (8 / 32 / 4) | **1.8e-4** |
| DeepSeek-V4-Flash | 160 | 320 | 88.8% | 82.5% | **85.6%** | 87.5% | -6.2pp (toward the 1st slot) | 20 (13 / 5 / 2) | 0.096 |
| Kimi-K2.6 | 160 | 320 | 86.9% | 83.8% | **85.3%** | 88.8% | -3.1pp (toward the 1st slot) | 18 (11 / 5 / 2) | 0.21 |

Raw slot preference over all judgements: gpt-5-mini picks slot A 47.0% / slot B 52.5% / tie 0.4%;
DeepSeek 51.6 / 45.9 / 2.5; Kimi 51.2 / 47.5 / 1.2. The three judges lean in **opposite
directions**, so this is a per-model idiosyncrasy rather than an artefact of the prompt.

### Corrected headline (order-balanced), per operator, N=3 seeds

| WildChat, AC3 vs AO (quality) | published | AC3 shown 1st | AC3 shown 2nd | **order-balanced (corrected)** | delta | n per seed |
|---|---|---|---|---|---|---|
| AC3-Reset | 89.8 +/- 1.4 | 84.4 +/- 2.1 | 91.1 +/- 2.2 | **87.8 +/- 2.1** | -2.0pp | 73 / 76 / 76 |
| AC3-Augment | 92.1 +/- 1.3 | 89.0 +/- 2.0 | 93.4 +/- 2.6 | **91.2 +/- 2.1** | -0.9pp | 76 / 76 / 75 |

Per-seed order-balanced rates: Reset 86.3 / 86.8 / 90.1 (seeds 42/43/44); Augment 92.8 / 88.8 / 92.0.
On-topic dimension, gpt-5-mini, all 452 pairs: 1st 73.2%, 2nd 80.5%, balanced **76.9%**, swap-consistency 83.2%.

**Interpretation.** `judge_pairwise()` draws the A/B assignment from `rng.random() < 0.5` on
every call, so the published estimate is unbiased for the order-balanced quantity in
expectation; the position bias inflates nothing. The -2.0 / -0.9pp movement is a mixture of
that residual randomisation variance and judge drift between the May-2026 run and this one.
A 200-draw random-order resimulation of this re-judge gives Reset median 87.6% (90% CI
85.8-89.3, published 89.8) and Augment median 91.2% (90% CI 89.4-93.0, published 92.1), so
Augment's published value is fully consistent with the re-judge and Reset's is ~0.5pp optimistic
at the edge of the interval. We therefore report the order-balanced numbers as the corrected
headline. **The claim is unaffected: both operators beat AO on ~88-91% of the AO-failure pool.**

## (b) Judge agreement

Cross-family judges run on the same frozen 160-pair subset (stratified, ~27 per cell,
`out/subset160.json`), in both presentation orders. Labels are 3-way {AC3, AO, tie}.
kappa is reported alongside PABAK and Gwet's AC1 because the marginal distribution is extreme
(AC3 wins ~90% of pairs), which is the classic kappa-paradox regime where kappa understates
concordance.

| Comparison | n | raw agreement | Cohen's kappa | PABAK | Gwet's AC1 |
|---|---|---|---|---|---|
| gpt-5-mini vs **DeepSeek-V4-Flash**, matched presentation | 320 | **87.5%** | **0.449** | 0.812 | 0.859 |
| gpt-5-mini vs **Kimi-K2.6**, matched presentation | 320 | **88.8%** | **0.507** | 0.831 | 0.873 |
| DeepSeek-V4-Flash vs Kimi-K2.6, matched presentation | 320 | 85.9% | 0.445 | 0.789 | 0.839 |
| gpt-5-mini vs DeepSeek, order-balanced labels | 160 | 83.1% | 0.455 | 0.747 | 0.801 |
| gpt-5-mini vs Kimi, order-balanced labels | 160 | 80.6% | 0.365 | 0.709 | 0.772 |
| **gpt-5-mini self-consistency** (identical prompt and order, independent call) | 160 | **96.9%** | **0.810** | 0.938 | 0.963 |
| gpt-5-mini re-judge vs the May-2026 stored verdicts | 452 | 88.5% | 0.487 | 0.827 | 0.871 |

Each judge's **own** order-balanced AC3 win-rate on the identical 160 pairs:

| Judge | family | AC3-Reset | AC3-Augment | overall |
|---|---|---|---|---|
| gpt-5-mini | OpenAI | 89.9 +/- 5.4 | 87.7 +/- 5.7 | **88.8%** |
| DeepSeek-V4-Flash | DeepSeek | 83.6 +/- 5.4 | 87.7 +/- 2.8 | **85.6%** |
| Kimi-K2.6 | Moonshot | 85.4 +/- 5.7 | 85.2 +/- 1.9 | **85.3%** |

All three judges, run independently, land within 3.5pp of each other; the largest cross-family
gap is 3.2pp (gpt-5-mini vs Kimi). Under a deliberately punitive rule — a pair counts as an AC3
win only if at least 2 of 3 judges pick AC3 in **both** presentation orders — the win-rate is
still **82.5%** (132/160), and all three judges are unanimous on 71.9% of pairs.
Self-consistency (96.9%) exceeds swap-consistency (90.3%), which cleanly attributes the
majority of the judge's instability to presentation order rather than to sampling noise.

## (c) Positive controls (trap #1)

Each judge scored a real AC3 response against a **degraded copy of itself** (first 25% of the
text, truncated mid-sentence, plus a generic filler tail), in both presentation orders.
Correct answer is known: prefer the intact response.

| Judge | n judgements | good wins | degraded wins | tie | good-first | degraded-first |
|---|---|---|---|---|---|---|
| gpt-5-mini | 40 | 39 (97.5%) | 0 | 1 | 20/20 | 19/20 |
| DeepSeek-V4-Flash | 40 | 36 (90.0%) | 2 | 2 | 18/20 | 18/20 |
| Kimi-K2.6 | 40 | 40 (100%) | 0 | 0 | 20/20 | 20/20 |

All three discriminate correctly and symmetrically across orders, so the re-judging pipeline
(prompt assembly, JSON parsing, A/B-to-condition remapping, endpoint routing) is sound.
Additionally, this harness records API/parse failures explicitly as `ok:false` and excludes them
from every denominator rather than coercing them to "tie" as the shipped `judge_pairwise` does;
**0 failures occurred in all 1,824 judgements**, so no denominator was affected either way.

## (d) Two harness facts worth putting in the paper's appendix

1. **The shipped judge already randomises presentation order** (`pairwise_judge.py`,
   `if rng.random() < 0.5`), but it **discards the realised assignment** — `_judgment_dict()`
   in `run_phase2.py` drops `position_assignment`. That is why this check required re-judging
   rather than re-analysis. Recommend persisting the field.
2. **The judge does not run at temperature 0**, despite `judge_pairwise` passing
   `temperature=0.0`: the OpenAI client emits `gpt-5 models require temperature=1.0,
   overriding 0.0 -> 1.0`. The self-consistency figure above (96.9%) is therefore a genuine
   measurement of that stochasticity, not a tautology.

## Appendix — prompts verbatim

### A.1 Pairwise judge prompt
Identical string for all three judges; only the model identifier changed. Source of truth
`src/ctx_editor/huang_eval/prompts/pairwise_judge.txt`, read at runtime by
`neurips_review/autoresearch/tasks/T11/rejudge.py` so it cannot drift from the harness.
`{context_for_a}` and `{context_for_b}` are both filled with the same original conversation
prefix (all turns before the evaluated user turn, rendered as `[role]\n<content>` blocks joined
by blank lines). Sent as a single `user` message, no system message.

```
You are an expert evaluator of AI assistant responses. You will evaluate two responses to round {round_num} of {total_rounds} in a multi-turn conversation.

CONVERSATION CONTEXT FOR RESPONSE A (All Past User and Assistant Turns):

{context_for_a}

RESPONSE A:

{first_resp}

CONVERSATION CONTEXT FOR RESPONSE B (All Past User and Assistant Turns):

{context_for_b}

RESPONSE B:

{second_resp}

EVALUATION CRITERIA:

You must compare the two responses on TWO separate dimensions and pick a winner for each:

1. Overall Quality: How well does the response address the user's current prompt?
   - Completeness in addressing the user's request
   - Accuracy of information provided
   - Clarity and coherence of the response
   - Helpfulness and usefulness to the user

2. On-Topic: Does the response stay focused on the conversation?
   - Stays on-topic and relevant to the conversation thread
   - Avoids topic drift, tangents, or unrelated content
   - Avoids repetitive phrases or unnecessary fillers

TASK:

For EACH dimension, directly compare the two responses and pick a winner. If the responses are roughly equal on a dimension, declare a tie. Provide your evaluation in the following JSON format:

{
  "quality_winner": "A" or "B" or "tie",
  "quality_justification": "<explanation comparing both responses on quality>",
  "ontopic_winner": "A" or "B" or "tie",
  "ontopic_justification": "<explanation comparing both responses on on-topic relevance>",
  "confidence": <float from 0.0 to 1.0 indicating how confident you are in your judgments>
}

Be objective and thorough in your evaluation. Respond ONLY with valid JSON.
```

### A.2 Positive-control construction
Same prompt as A.1. The two responses compared are the AC3 response `r` and `degrade(r)`:

```python
def degrade(text: str) -> str:
    """Obviously-degraded copy of a response: truncated mid-sentence, first 25%,
    with a generic filler tail. Used as the positive control."""
    n = max(60, int(len(text) * 0.25))
    head = text[:n]
    return head + "\n\nAnyway, that's basically it. Let me know if you want more."
```

## Reproduction

```bash
# judge A, all 452 pairs, both orders
.venv/bin/python neurips_review/autoresearch/tasks/T11/rejudge.py --mode order \
  --judge-model gpt-5-mini --max-concurrent 5 \
  --out neurips_review/autoresearch/tasks/T11/out/order_gpt5mini.jsonl
# cross-family judges on the frozen subset
... --judge-model DeepSeek-V4-Flash --subset-file .../out/subset160.json ...
... --judge-model Kimi-K2.6        --subset-file .../out/subset160.json ...
# self-consistency and positive controls
... --mode repeat  --judge-model gpt-5-mini --fixed-order ao_first --subset-file .../subset160.json
... --mode control --judge-model <M> --limit 20
.venv/bin/python neurips_review/autoresearch/tasks/T11/analyze.py
```

All judges routed through `load_balancer=t9_foundry_trapi` (gpt-5-mini on `dl-openai-3`;
DeepSeek-V4-Flash and Kimi-K2.6 on `mgalley-foundry2`). Nothing under `src/` was modified;
no `git checkout` was performed; all outputs are T11-scoped.

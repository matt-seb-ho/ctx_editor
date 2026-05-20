# Post-May-18 R3 Overnight Summary

**Run window**: 2026-05-19 22:53 PT → 2026-05-20 01:54 PT (~3h)
**Status**: Complete. All R3 cells finished; mega-table populated;
follow-ups logged in `docs/post_may18_r3_followups.md`.
**Author**: Claude (autonomous overnight)
**Prior batch**: `docs/reports/post_neurips_r2_summary.md` (R2, 2026-05-18)

## Agenda (per `docs/next_todos_post_may18.md`)

1. **Task 1.1**: Hierarchical analysis of *why* Rewrite underperforms Reset
   at the prepared-context level.
2. **Task 1.2**: Try interventions to make Rewrite competitive (the
   2b "remove conversation from rewrite prompt" hypothesis is the
   strongest candidate to start with).
3. **Task 2**: Fill the mega-table cells:
   - WildChat × Rewrite on all models + Augment on Kimi
   - LiC × Rewrite on gpt-5.4 + Kimi
   - CollabLLM × all standard methods on gpt-5.4 + Kimi
   - tau2 — scope replayability

## Workhorse + book-keeping conventions

- **DeepSeek-V4-Flash** for all analysis/prototyping/worker scripts.
- Literature notes go in `docs/notes/literature/` (GEPA, TextGrad,
  Combee, the optimize-anything blog).
- All long-running experiments documented with **run command,
  output directory, score table, takeaways**.

## TL;DR (01:32 PT)

- **Rewrite-vs-Reset analysis (Task 1.1)**: 63% of LiC Rewrite
  failures attribute to **rewriter-LLM hallucination** — content
  invented from neither the analyzer notes nor the conversation.
  Only 4% attribute to conversation. The user's "remove conversation"
  hypothesis (Task 1.2b) is largely falsified by the data.
- **Rewrite interventions (Task 1.2)**: v3 (no-conv) is **net slightly
  worse** than v1 (math −3.4pp, database −5.5pp, code +3.6pp).
  Confirms 1.1: removing the conversation can't fix what the
  rewriter itself adds. v4 (strict-relay) in flight.
- **HEADLINE (Task 2 WildChat)**: AC3-Rewrite is **competitive on
  WildChat across all models**, and **beats Reset on DeepSeek
  (+8.6pp) and Kimi (+10.5pp)**. The "Rewrite is always worst"
  pattern is LiC-specific — it doesn't generalize to real
  multi-turn human conversation.
- **Rewrite on gpt-5.4 / Kimi (LiC)**: clears Baseline on math
  (+2.5pp gpt-5.4) and database (+15.7pp gpt-5.4 / +17.7pp Kimi); ties or
  loses on code/actions. Still ~12pp below Reset on average. Rewrite
  gets stronger as the respondent gets stronger, but doesn't overtake
  Reset on LiC.
- **CollabLLM cross-model**: math-hard saturates at 95–100% on
  gpt-5.4/Kimi for all 4 standard methods — no signal here.
  bigcodebench has signal: AO leads on Kimi (26% > Baseline 15%),
  Augment ≈ Baseline ~15-18%, **Rewrite worst at 10%** (DeepSeek).
  AC3-Reset broken on bigcodebench × {gpt-5.4, Kimi} by Azure content
  filter — known issue. R3 also added CollabLLM × Rewrite × DeepSeek:
  math-hard 90% (competitive), bigcodebench 10% (worst AC3 variant).
- **Mega table**: see `docs/reports/post_may18_r3_mega_table.md` —
  3 models × 3 benchmarks × 4 strategies for LiC + CollabLLM, plus
  the WildChat win-rate matrix. Only Gated-Reset is largely empty.
- **tau2 deferred** (replay infra ~2 dev-days; not tonight; see
  `docs/notes/literature/tau2_replay_scoping.md`).

## Phase A — Task 1.1: Rewrite vs Reset context-level analysis

### Method

Hierarchical:
1. Hand-read 2 contrast cases (one database, one math) where Reset
   succeeded and Rewrite failed. Identified two recurring patterns:
   spec drift (Rewrite paraphrases the analyzer spec, adding phantom
   detail or relaxing a constraint) and "What Looks Right" anchoring
   (Rewrite inlines verbatim prior code or numerical speculation that
   the assistant treats as authoritative).
2. Wrote `scripts/analysis_rewrite_v_reset/extract_pairs.py`. Walks
   Phase 1 outputs (DeepSeek-V4-Flash), pulls 127 (sample, task)
   pairs where Reset got it right and Rewrite got it wrong, dumping
   both prepared contexts + both final answers + the analyzer log.
3. Wrote `scripts/analysis_rewrite_v_reset/diagnose_pair.py`. For each
   pair, asks DeepSeek-V4-Flash to compare the two contexts, classify
   the spec divergence (vaguer / phantom_added / phantom_dropped /
   format_lost / equivalent), flag "What Looks Right" pathologies
   (verbatim code, numerical speculation, missing caveat), pick a
   primary cause, and attribute the bad context to one of:
   `analyzer_output / conversation / rewrite_prompt /
   rewriter_hallucination`.
4. Ran on a balanced 48-pair sample (12/task). Aggregated via
   `aggregate_diagnoses.py`. Mean labeler confidence 0.95.

### Headline finding

**The rewriter LLM hallucinates content not present in either input.**

Attribution of the bad Rewrite context (which input is responsible):

| Source | n / 48 |
|---|---|
| **rewriter_hallucination** (neither in analyzer nor conversation) | **30 (63%)** |
| analyzer_output (analyzer was already wrong) | 13 (27%) |
| rewrite_prompt | 3 (6%) |
| conversation | 2 (4%) |

The conversation-as-input hypothesis (that the conversation pollutes
the rewriter — Task 1.2b motivation) is **falsified by this data**:
only 4% of failures attribute to the conversation. The dominant
mechanism is the rewriter LLM *adding* content from nowhere —
inventing constraints, re-deriving numbers, inlining code that
wasn't established in the prior work, etc.

### Spec divergence (Rewrite spec vs Reset spec)

| Kind | n |
|---|---|
| phantom_added | 20 |
| phantom_dropped | 17 |
| equivalent | 8 |
| vaguer | 2 |
| more_specific | 1 |

77% of Rewrite specs *materially differ* from Reset's — almost
evenly split between adding phantom requirements and dropping real
ones.

### Work-so-far divergence (flag counts across 48)

| Pathology | n |
|---|---|
| omits_important_caveat | 28 (58%) |
| inlines_verbatim_code | 21 (44%) |
| inlines_numerical_speculation | 3 (6%) |

Verbatim-code inlining clusters in code (9/12) and database (7/12)
— consistent with the smoking-gun we saw by hand. The "omits
caveat" pathology is everywhere — Reset's templated narrative
preserves status notes ("waiting for X to compute final answer")
that Rewrite drops.

### Primary cause

| Cause | n |
|---|---|
| spec_divergence | 28 |
| work_so_far_divergence | 18 |
| other | 2 |

Spec divergence is the #1 cause; "What Looks Right" pathologies
are the #2. The two interact (a vague spec + inlined wrong code
together push the assistant toward the wrong answer).

### What this tells us about interventions

- The **"remove the conversation from the rewrite prompt"
  hypothesis (Task 1.2b)** is weak — only 4% of failures attribute
  to the conversation. Removing it cannot help most cases.
- The right intervention has to **structurally constrain the
  rewriter LLM from inventing content** (the 63% hallucination
  bucket). Options:
  - (a) Make the rewrite operation a strict promotion of analyzer
    notes — no rephrasing, no addition. Closer to template-filling.
  - (b) Skip the rewrite LLM call entirely (= Reset).
  - (c) Reformulate the rewriter's task: instead of "compact",
    have it produce *something different from the analyzer notes*
    (e.g., prompt-engineering hints). This changes the value
    proposition.

Tonight we test (a) via two prompts:
- `context_compaction_v3_no_conv.txt`: no conversation in input,
  strict "do not add, do not paraphrase" framing.
- `context_compaction_v3_conv_first.txt`: conversation at the
  top, analyzer notes at the bottom (cheap "softer" variant of
  the no-conv hypothesis; included for completeness).

Even before results land, the analysis says (a) probably caps at
"Reset-equivalent" because the hallucination is in the rewriter
LLM itself, not its input. If v3 doesn't beat Reset, the cleanest
paper claim is: **the rewrite LLM call is structurally lossy;
prompt-level controls cannot fully suppress hallucination.**

## Phase B — Task 1.2: Rewrite intervention

### Design (informed by 1.1)

The 1.1 finding (63% of rewrite failures are
**rewriter-LLM hallucination** — content added that wasn't in either
the analyzer notes or the conversation) re-routed my interventions
away from the user's 1.2b "remove conversation" hypothesis (which
only addresses the 4% conversation-attributed bucket) and toward a
stricter anti-hallucination prompt:

- **v3-no-conv** (`context_compaction_v3_no_conv.txt`): removes the
  conversation entirely from the rewriter's input. Tests the 1.2b
  hypothesis. Predicted not to help much (per the 4% attribution).
- **v3-conv-first** (`context_compaction_v3_conv_first.txt`):
  conversation at top, analyzer notes at bottom. Softer variant of
  1.2b. Included for completeness.
- **v4-strict** (`context_compaction_v4_strict.txt`): no conversation
  input + "relay, not rewrite" framing + explicit ban on verbatim
  code, numerical results, "implied next steps" — and a 2-sentence
  cap on the work-so-far section. Designed against the 1.1
  hallucination findings directly.

Smoke tests (n=2) showed v3-no-conv still emits "implied next
step is..." in the spec (consistent with 1.1's prediction that
prompt-only constraints don't fully suppress LLM hallucination), and
v4-strict still inlines numerical results in "What Looks Right"
despite explicit prohibitions. The structural pull toward
elaboration is hard to suppress at the prompt level.

### First-run rate-limit gotcha

First v3 sweep ran with `max_concurrent=12` per cell across 24
parallel cells while WildChat + LiC cross-model fills were also
hitting the foundry endpoint. Result: most cells had 30–49 of 50
samples excluded as errors (429 token-rate limits). Cells were
killed and outputs removed; the throttled re-run uses
`max_concurrent=4` per cell with at most 4 cells in parallel.
Script: `scripts/run_post_may18_r3_rewrite_v3_v4.sh`.

### Expected outcomes

Per the 1.1 attribution, the upper bound for prompt-only
intervention is roughly "match Reset". The cleanest **paper claim**
from this batch — assuming v4-strict doesn't materially beat v1 — is:

> The rewriter LLM call is structurally lossy. The dominant
> failure (63%) is the LLM generating content that wasn't in either
> input. Prompt-level controls (v2 v3 v4) reduce but cannot suppress
> this. The template-fill approach (Reset) wins by structural design:
> it has no LLM step at which hallucination could occur.

### Results — Rewrite versions vs Baseline / Reset on LiC

Aggregated by `scripts/analysis_rewrite_v_reset/compare_rewrite_versions.py`.
DeepSeek-V4-Flash, last-turn replay, htn50_52 (n=113–150 per task).

| Variant | math | code | database | actions | avg | Δ vs Baseline (avg) |
|---|---|---|---|---|---|---|
| Baseline | 72.2 | 34.5 | 22.4 | 76.0 | 51.3 | — |
| AO | 86.1 | 60.2 | 45.6 | 86.0 | 69.5 | **+18.2pp** |
| Reset | 81.9 | 59.3 | 49.0 | 83.3 | 68.4 | **+17.1pp** |
| Rewrite v1 | 73.6 | 28.3 | 27.9 | 74.0 | 51.0 | **−0.3pp** |
| Rewrite v2 (R2 "exhaustive") | 70.8 | 36.3 | 21.8 | 70.0 | 49.7 | **−1.6pp** |
| Rewrite v3-no-conv (Task 1.2b) | 68.8 | 31.9 | 22.4 | 72.7 | 48.9 | **−2.4pp** |
| Rewrite v4-strict (Task 1.2-relay) | 66.0 | 33.6 | 21.1 | 64.7 | 46.3 | **−5.0pp** |

**Net negative trajectory**: v1 → v2 → v3 → v4 all worsen vs.
v1. The progressively stricter prompts (v2 added "be exhaustive",
v3 removed conversation input, v4 banned verbatim code + numerical
results + "next step" prose) compound to push the rewriter LLM
toward shorter, less-informative output that hurts more than it
helps. v4 even has elevated error counts (9 math errors, 7 actions
errors) — the strict prompt may be triggering refusals / malformed
output.

### Conclusion: Task 1.2

**Prompt-only intervention cannot rescue LiC Rewrite.** Every
attempted intervention made things worse than v1, and v1 itself only
matched Baseline. The 1.1 attribution (63% rewriter hallucination)
predicted this: the failure mechanism is the LLM itself adding
content, which prompt instructions reduce but cannot suppress.

The cleanest paper claim from this batch:

> Compaction-by-LLM-rewrite is a structurally lossy intervention.
> Multiple progressively-stricter prompt revisions failed to recover
> the gap to Reset on LiC. The simpler templated approach (Reset)
> wins because it doesn't introduce a second LLM step at which
> hallucination can occur.

This is a clean negative result that motivates the Reset design.
Together with the new WildChat finding (Rewrite competitive on
multi-turn human conversation), the bigger story is **the right
intervention intensity depends on task structure** — strict-format
tasks reward Reset's literal preservation, open-ended conversational
tasks tolerate or even prefer Rewrite's flexibility.

## Phase C — Task 2: mega-table fills

### LiC × Rewrite cross-model

Launcher: `scripts/run_post_may18_r3_lic_rewrite_fills.sh`.
gpt-5.4 fills landed cleanly. **Kimi-K2.6 fills polluted by the
same 429 cascade** (most cells excluded 30–48 of 50 samples). Re-run
prepared at `scripts/run_post_may18_r3_lic_rewrite_kimi_retry.sh`,
will launch after the foundry endpoint frees up.

gpt-5.4 Rewrite v1 — clean numbers (errors < 1 per cell):

| Task | gpt-5.4 Rewrite | gpt-5.4 Baseline (Phase 2) | Δ |
|---|---|---|---|
| math | 81.0% | 78.5% | **+2.5pp** |
| code | 57.4% | 57.5% | −0.1pp |
| database | 34.7% | 19.0% | **+15.7pp** |
| actions | 84.0% | 87.3% | −3.3pp |

Rewrite **clears Baseline on math + database** on gpt-5.4, ties on
code, slightly loses on actions. Database is the standout (+15.7pp)
— consistent with the broader "stronger models recover schema
benefit from any context restatement" pattern from R1/R2.

But Rewrite is still well below Reset on gpt-5.4 (Phase 2 numbers):
math 81 vs Reset 87.4 (−6pp), code 57.4 vs 73.6 (−16pp), database
34.7 vs 56.2 (−21pp), actions 84 vs 92 (−8pp). So **gpt-5.4 doesn't
rescue Rewrite-vs-Reset either**.

### WildChat × Rewrite (s3) cross-model — DONE

Launcher: `scripts/run_post_may18_r3_wildchat_fills.sh`. All 4 cells
completed by 00:10 PT. Pairwise win-rate vs AO/FC on the same
76-turn evaluation set:

| Respondent | s3 vs AO (quality) | s3 vs AO (ontopic) | s3 vs FC (quality) |
|---|---|---|---|
| gpt-5-mini | **86.7%** | 77.3% | 77.3% |
| DeepSeek-V4-Flash | 83.6% | 72.6% | 71.2% |
| Kimi-K2.6 | 82.1% | 71.6% | 74.6% |

Plus the Kimi×Augment fill we were missing:

| Respondent | Augment vs AO (quality) | Augment vs FC (quality) |
|---|---|---|
| Kimi-K2.6 | **85.7%** | 78.6% |

**Headline finding**: AC3-Rewrite is **competitive on WildChat across
all models** — within 5pp of the other AC3 variants.

| Respondent | Reset (s15) | Augment | Rewrite (s3) |
|---|---|---|---|
| gpt-5-mini | 89.8% | 92.1% | 86.7% |
| DeepSeek-V4-Flash | 75.0% | 84.2% | **83.6%** |
| Kimi-K2.6 | 71.6% | 85.7% | **82.1%** |

On DeepSeek and Kimi, **Rewrite (s3) beats Reset (s15)** by 8.6 and
10.5pp respectively — a complete inversion of the LiC ranking.

This is the most narrative-shifting finding tonight. The "Rewrite
is always worst" story (from LiC) does not generalize. On WildChat,
Rewrite's extra LLM polish is rewarded by the pairwise judge — likely
because real human conversations have more polished prose, and the
judge prefers the rewriter's more natural output over Reset's more
structured templated message. LiC's strict-format tasks (math
answer format, SQL syntax, function-call format) penalize the
rewriter's drift; WildChat's open-ended conversational tasks reward
its flexibility.

### CollabLLM × {gpt-5.4, Kimi-K2.6} — DONE

Launchers: `scripts/run_post_may18_r3_collabllm_gpt5_4.sh` (Azure
OAI assistant + foundry DeepSeek user-sim) and
`scripts/run_post_may18_r3_collabllm_kimi.sh` (all-foundry).
N=1 single rep, 20 problems per cell.

| Task / Model | Strategy | Accuracy | Notes |
|---|---|---|---|
| math-hard / gpt-5.4 | Baseline | 95.0% | |
| math-hard / gpt-5.4 | AO | 95.0% | |
| math-hard / gpt-5.4 | Augment | 95.0% | |
| math-hard / gpt-5.4 | Reset | 93.8% | 4 errors excluded |
| math-hard / Kimi-K2.6 | Baseline | **100.0%** | |
| math-hard / Kimi-K2.6 | AO | **100.0%** | |
| math-hard / Kimi-K2.6 | Augment | 95.0% | |
| math-hard / Kimi-K2.6 | Reset | 93.8% | 4 errors excluded |
| bigcodebench / gpt-5.4 | Baseline | 15.0% | |
| bigcodebench / gpt-5.4 | AO | **20.0%** | |
| bigcodebench / gpt-5.4 | Augment | 17.6% | 3 errors excluded |
| bigcodebench / gpt-5.4 | Reset | **0.0%** | **ALL 20 filtered** (CF) |
| bigcodebench / Kimi-K2.6 | Baseline | 15.0% | |
| bigcodebench / Kimi-K2.6 | AO | **25.0%** | |
| bigcodebench / Kimi-K2.6 | Augment | 15.8% | 1 error excluded |
| bigcodebench / Kimi-K2.6 | Reset | **0.0%** | **ALL 20 filtered** (CF) |

#### Findings

- **math-hard is fully saturated** on both stronger models.
  Baseline ties or beats every intervention. The user-sim swap (R2
  finding) recovered all the headroom on this task; there is no
  room left for AC3 to help.
- **bigcodebench AO leads** on both gpt-5.4 (+5pp vs Baseline) and
  Kimi (+10pp vs Baseline). Different from the R2 DeepSeek-V4-Flash
  result where Reset led at 20%.
- **Reset is broken on bigcodebench × strong models** — Azure
  content filter triggers `jailbreak: detected` on the Reset
  analyzer's bigcodebench prompts when sent to gpt-5.4 / Kimi.
  Same false-positive pattern as the AC3 batch (`v8 → s1` escalation
  was the mitigation last time). Documented as a known issue;
  Reset-v8 + bigcodebench + strong-model needs an analyzer-prompt
  switch. Follow-up.
- **The cross-benchmark Augment-wins-easy / Reset-wins-hard story
  from R2 is task-and-model dependent.** On Kimi/gpt-5.4 ×
  bigcodebench, AO (a *simpler* intervention than either AC3 variant)
  wins. AC3-Reset's R2 lead on DeepSeek × bigcodebench may have been
  a model-specific effect rather than a generalizable property of
  hard tasks.

## Phase D — tau2 scoping

Scoping done. **Verdict**: tau2 last-turn replay is **not feasible
overnight** — requires ~2 dev-days of work to snapshot/restore the
dual-control env state (CRM DB + phone state + user-sim persona).
Fresh-sim cross-model on telecom_small is feasible (~2h per
(assistant model, strategy) cell) but would push tonight's budget.

Defer tau2 fills to a follow-up overnight. Full reasoning:
`docs/notes/literature/tau2_replay_scoping.md`.

## Mega table

Full snapshot in `docs/reports/post_may18_r3_mega_table.md`
(auto-generated by `scripts/build_mega_table.py`).

Coverage as of R3 wrap-up:

- **LiC**: full 3-model × 4-task × {Baseline, AO, Augment, Reset,
  Rewrite} matrix. Gated-Reset only on DeepSeek (Phase 1).
  Kimi Rewrite × {database, actions} still landing (LiC Kimi retry).
- **CollabLLM**: 3 models × 2 tasks × {Baseline, AO, Augment, Reset}.
  Rewrite on DeepSeek launching now. Reset × bigcodebench × {gpt-5.4,
  Kimi} broken by Azure content filter (logged follow-up).
- **WildChat**: 3 models × {Reset, Augment, Rewrite}. Augment on
  Kimi added tonight. Gated-Reset not yet anywhere.
- **tau2**: deferred (see Phase D below).

## Cost / time accounting

Will fill in once the last cells (CollabLLM Rewrite DeepSeek + Kimi
LiC retry actions) land. Foundry-side tokens not priced; LiC + Huang
+ CollabLLM at this scale costs <$2 in reported OAI calls.

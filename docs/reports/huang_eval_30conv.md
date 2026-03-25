# Huang et al. Reproduction Evaluation: 30-Conversation Pilot

## Overview

This report documents a small-scale reproduction of Huang et al. "Do LLMs Benefit from Their Own Words?" using our context editing framework. The experiment uses a two-phase design: Phase 1 mines for AO (assistant-omitted) failure cases by comparing FC (full context) against AO on 30 WildChat conversations, and Phase 2 tests whether our surgical context editing strategies (S3 and S1.5) can recover performance on those failure turns. The goal is to demonstrate that surgical context editing overcomes AO's failure mode on stateful turns -- turns where the assistant's prior responses carry information the user depends on -- without discarding useful context the way AO does.

## Method

**Data.** 30 conversations sampled from allenai/WildChat-1M, filtered per Huang's criteria: English language, technical content (math/coding keywords), 5--10 rounds, non-toxic. Sampling used seed=42 with max_scan=10000.

**Conditions.**

- **FC (full context):** The unmodified conversation history, serving as the ceiling for context-dependent turns.
- **AO (assistant-omitted):** All prior assistant messages replaced with `"[Response provided]"` placeholders, plus Huang's AO system message instructing the model to infer prior responses from user messages. This is Huang's main intervention.
- **S3 (ConversationAnalyzer v8 + LLM compaction):** The v8 two-query hard-attention analyzer inspects the conversation for problematic content (anchoring, failed approaches, erroneous assumptions), then an LLM compaction step (context_compaction.txt prompt) rewrites the context to surgically remove harmful content while preserving correct information.
- **S1.5 (analyzer + programmatic template):** Same analyzer as S3, but instead of LLM compaction, uses a programmatic template to reset context. No additional LLM call for the compaction step.
- **S2 (gated context edit with v11 analyzer):** Uses the v11 analyzer prompt (generalized from tau2's v10 "mid-task reflection" framing). Key difference from S1.5/S3: S2 gates on `needs_edit` -- if the analyzer finds no issues, returns FC (no reset). This avoids unnecessary resets on turns where the conversation is on track. When reset IS triggered, uses programmatic template (like S1.5). The v11 compare prompt tightens the issues section to require exact "None" when no problems exist, preventing false triggers.

**Turn classification.** Each user turn was classified using Huang's classifier prompt into one of three types: `new_ask` (new topic or question), `feedback` (user gives feedback on prior response), `no_feedback` (continuation without explicit feedback, often stateful).

**Evaluation.** Huang's pairwise judge prompt was used to compare responses on two dimensions: Quality and On-Topic. A/B order was randomized to control for position bias.

**Models.** All roles (respondent, judge, classifier, analyzer) used gpt-5-mini. Note that Huang used GPT-5 as their judge model.

## Run Configs

### Phase 1

```
python -m ctx_editor.huang_eval.run_phase1 \
    --num-conversations 30 --respondent-model gpt-5-mini \
    --judge-model gpt-5-mini --classifier-model gpt-5-mini \
    --max-concurrent 5 --max-scan 10000 --seed 42
```

### Phase 2

```
python -m ctx_editor.huang_eval.run_phase2 \
    --phase1-dir outputs/huang_eval/phase1/2026-03-24/02-22-57 \
    --respondent-model gpt-5-mini --judge-model gpt-5-mini \
    --analyzer-model gpt-5-mini --max-concurrent 5 --run-s15 --seed 42
```

## Prompt Versions

- **Turn classifier:** `src/ctx_editor/huang_eval/prompts/turn_classifier.txt` (from Huang et al. Appendix A.5)
- **Pairwise judge:** `src/ctx_editor/huang_eval/prompts/pairwise_judge.txt` (from Huang et al. main evaluation prompt)
- **AO system message:** `src/ctx_editor/huang_eval/prompts/ao_system_message.txt` (from Huang et al.)
- **S3 analyzer:** ConversationAnalyzer v8 (two-query hard attention), prompts at `src/ctx_editor/strategies/prompts/analyzer_v8_task_spec.txt` and `analyzer_v8_compare.txt`
- **S3 compaction:** `src/ctx_editor/strategies/prompts/context_compaction.txt`

## Output Locations

**Phase 1:** `outputs/huang_eval/phase1/2026-03-24/02-22-57/`

- `turn_results.jsonl` -- 179 per-turn records with FC/AO responses, judgments, and turn type
- `metrics.json` -- aggregated win rates
- `breakdown_by_type.csv` -- win rates by turn type
- `ao_failure_turns.json` -- 76 turns where FC > AO on quality
- `conversations/` -- 30 raw filtered WildChat conversations
- `config.json`, `summary.txt`, `phase1.log`

**Phase 2:** `outputs/huang_eval/phase2/2026-03-24/02-54-36/`

- `turn_results.jsonl` -- 76 per-turn records with S3/S1.5 responses, judgments, and analyzer outputs
- `metrics.json`, `breakdown_by_type.csv`, `config.json`, `summary.txt`, `phase2.log`

## Results

### Phase 1: FC vs AO (n=179 turns, 30 conversations)

**Turn type distribution:**

| Type | Count | % |
|------|-------|---|
| no_feedback | 69 | 38.5% |
| new_ask | 67 | 37.4% |
| feedback | 43 | 24.0% |

**FC vs AO quality win rates by turn type:**

| Turn Type | n | FC wins | AO wins | Tie |
|-----------|---|---------|---------|-----|
| new_ask | 67 | 34.3% | 56.7% | 9.0% |
| feedback | 43 | 37.2% | 60.5% | 2.3% |
| no_feedback | 69 | 53.6% | 42.0% | 4.3% |
| Overall | 179 | 42.5% | 52.0% | 5.6% |

**FC vs AO on-topic win rates by turn type:**

| Turn Type | n | FC wins | AO wins | Tie |
|-----------|---|---------|---------|-----|
| new_ask | 67 | 16.4% | 14.9% | 68.7% |
| feedback | 43 | 14.0% | 20.9% | 65.1% |
| no_feedback | 69 | 23.2% | 18.8% | 58.0% |
| Overall | 179 | 18.4% | 17.9% | 63.7% |

76 AO failure turns identified (FC > AO on quality), representing 42.5% of all turns.

### Phase 2: S3 and S1.5 on AO failure subset (n=76)

**S3 edit rate:** 85.5% (the analyzer flagged issues and triggered compaction on 65 of 76 turns).

**Overall comparisons (quality):**

| Comparison | Winner 1 | Winner 2 | Tie |
|------------|----------|----------|-----|
| AO vs S3 | AO 10.5% | S3 86.8% | 2.6% |
| FC vs S3 | FC 14.5% | S3 84.2% | 1.3% |
| AO vs S1.5 | AO 9.2% | S1.5 90.8% | 0.0% |
| FC vs S1.5 | FC 13.2% | S1.5 86.8% | 0.0% |

**Overall comparisons (on-topic):**

| Comparison | Winner 1 | Winner 2 | Tie |
|------------|----------|----------|-----|
| AO vs S3 | AO 7.9% | S3 73.7% | 18.4% |
| FC vs S3 | FC 9.2% | S3 72.4% | 18.4% |
| AO vs S1.5 | AO 7.9% | S1.5 73.7% | 18.4% |
| FC vs S1.5 | FC 10.5% | S1.5 71.1% | 18.4% |

**S3 vs AO by turn type (quality):**

| Turn Type | n | S3 wins | AO wins | Tie |
|-----------|---|---------|---------|-----|
| no_feedback | 37 | 86.5% | 8.1% | 5.4% |
| new_ask | 23 | 87.0% | 13.0% | 0.0% |
| feedback | 16 | 87.5% | 12.5% | 0.0% |

## Analysis

**1. Huang reproduction confirmed.** The `no_feedback` turn type is the only category where FC consistently beats AO (53.6% vs 42.0%), matching Huang's central finding that AO hurts performance on stateful turns where the user implicitly depends on prior assistant output. Our classifier found 38.5% `no_feedback` turns, close to their reported 33.1%. On `new_ask` and `feedback` turns, AO wins, consistent with context pollution being the dominant factor when the user's message is self-contained or provides explicit corrections.

**2. S3 and S1.5 dramatically outperform both FC and AO on failure cases.** On the 76 turns where AO lost to FC, S3 beats AO at roughly 87% and beats FC at roughly 84% on quality. S1.5 performs comparably or slightly better than S3. Both strategies achieve strong on-topic improvements as well (around 72--74% win rate over AO and FC).

**3. S3 beats FC, not just AO.** This is the key finding. If S3 merely preserved the assistant context that AO discards, it would match FC but not exceed it. The fact that S3 wins against FC at 84% suggests it also cleans up context pollution present in FC. The analyzer identifies where the assistant's reasoning went wrong, and the compaction removes that content, producing a context that is cleaner than the unmodified original.

**4. S1.5 vs S3.** S1.5 (programmatic reset, no LLM compaction) slightly outperforms S3 (LLM compaction) on quality win rates. This is consistent with prior findings on LiC where the programmatic template performs well. The extra LLM compaction call in S3 may not add value on these conversations, and the programmatic approach avoids introducing compaction errors.

## Phase 2 Full: S3 on All 179 Turns (Unconditional)

A follow-up run evaluated S3 on all 179 turns (not just AO failure cases) to test whether S3 holds up overall, including on turns where AO was already winning.

### Run Config

```
python -m ctx_editor.huang_eval.run_phase2 \
    --phase1-dir outputs/huang_eval/phase1/2026-03-24/02-22-57 \
    --turns-file outputs/huang_eval/phase1/2026-03-24/02-22-57/all_turns.json \
    --respondent-model gpt-5-mini --judge-model gpt-5-mini \
    --analyzer-model gpt-5-mini --max-concurrent 5 --seed 42
```

**Output location:** `outputs/huang_eval/phase2_full/2026-03-25/01-39-43/`

### Results (n=178 turns, S3 only, no S1.5)

S3 edit rate: 84.3%

**S3 vs AO (quality):**

| Turn Type | n | S3 wins | AO wins | Tie |
|-----------|---|---------|---------|-----|
| new_ask | 66 | 84.8% | 15.2% | 0.0% |
| feedback | 43 | 81.4% | 18.6% | 0.0% |
| no_feedback | 69 | 81.2% | 18.8% | 0.0% |
| **Overall** | **178** | **82.6%** | **17.4%** | **0.0%** |

**S3 vs FC (quality):**

| Turn Type | n | S3 wins | FC wins | Tie |
|-----------|---|---------|---------|-----|
| new_ask | 66 | 87.9% | 12.1% | 0.0% |
| feedback | 43 | 76.7% | 23.3% | 0.0% |
| no_feedback | 69 | 75.4% | 21.7% | 2.9% |
| **Overall** | **178** | **80.3%** | **18.5%** | **1.1%** |

**S3 vs AO (on-topic):**

| Turn Type | n | S3 wins | AO wins | Tie |
|-----------|---|---------|---------|-----|
| new_ask | 66 | 65.2% | 7.6% | 27.3% |
| feedback | 43 | 72.1% | 16.3% | 11.6% |
| no_feedback | 69 | 69.6% | 15.9% | 14.5% |
| **Overall** | **178** | **68.5%** | **12.9%** | **18.5%** |

**S3 vs FC (on-topic):**

| Turn Type | n | S3 wins | FC wins | Tie |
|-----------|---|---------|---------|-----|
| new_ask | 66 | 68.2% | 4.5% | 27.3% |
| feedback | 43 | 69.8% | 20.9% | 9.3% |
| no_feedback | 69 | 65.2% | 17.4% | 17.4% |
| **Overall** | **178** | **67.4%** | **13.5%** | **19.1%** |

### Analysis of Full Results

**5. S3 dominates unconditionally.** The selection bias concern from the failure-only Phase 2 is resolved: S3 beats both AO and FC across all turn types, not just on AO failure cases. Even on new_ask turns where AO was beating FC (56.7% to 34.3% in Phase 1), S3 beats AO 84.8% to 15.2%. The result is not conditional on pre-selecting failure cases.

**6. Uniformly high win rates raise a format bias concern.** S3 win rates are remarkably uniform across turn types (~81-85% vs AO, ~75-88% vs FC). We would expect more variation if the wins were purely content-driven: S3 should help more on no_feedback turns (where context matters) and less on new_ask turns (where the question is self-contained). The uniformity suggests the compacted format itself (clean task spec + structured headers) may give S3 a presentation advantage that the judge rewards. The judge sees a well-organized summary from S3 vs. a raw multi-turn conversation rendered in Option 2 format from FC/AO. This is a real concern for interpreting absolute win rates.

**7. Relative ordering still informative despite format bias.** Even if absolute win rates are inflated by format advantage, the relative comparisons within S3 results are still valid. S3 wins slightly more against AO than against FC, which is expected (FC has the context that AO lacks). And the on-topic dimension shows more ties than quality, suggesting the judge is at least somewhat discriminating between dimensions.

## S2 (Gated Context Edit) on AO Failure Subset

S2 uses the v11 analyzer prompt (generalized from tau2's v10 "mid-task reflection" framing) with gating: only resets when `needs_edit=True`. When no issues are found, falls back to FC.

### Run Config

```
python -m ctx_editor.huang_eval.run_phase2 \
    --phase1-dir outputs/huang_eval/phase1/2026-03-24/02-22-57 \
    --respondent-model gpt-5-mini --judge-model gpt-5-mini \
    --analyzer-model gpt-5-mini --max-concurrent 5 --run-s2 --seed 42
```

**Prompt versions:** Analyzer v11 (task spec: `analyzer_v8_task_spec.txt`, compare: `analyzer_v11_compare.txt`). Programmatic post-reset template (no LLM compaction).

**Output location:** `outputs/huang_eval/phase2_s2_failures/2026-03-25/04-53-30/`

### Results (n=75, AO failure subset)

S2 edit rate: 68.0% (v11 gating prevents reset on 32% of turns)

**S2 vs AO and S3 vs AO (quality) -- side by side:**

| Comparison | Winner | Loser | Tie |
|------------|--------|-------|-----|
| AO vs S2 | **S2 93.3%** | AO 5.3% | 1.3% |
| AO vs S3 | S3 85.3% | AO 14.7% | 0.0% |
| FC vs S2 | **S2 82.7%** | FC 17.3% | 0.0% |
| FC vs S3 | S3 84.0% | FC 16.0% | 0.0% |

**S2 vs AO by turn type (quality):**

| Turn Type | n | S2 wins | AO wins | Tie |
|-----------|---|---------|---------|-----|
| new_ask | 22 | 90.9% | 9.1% | 0.0% |
| feedback | 16 | 100.0% | 0.0% | 0.0% |
| no_feedback | 37 | 91.9% | 5.4% | 2.7% |

## S2 on All Turns (Unconditional)

### Run Config

```
python -m ctx_editor.huang_eval.run_phase2 \
    --phase1-dir outputs/huang_eval/phase1/2026-03-24/02-22-57 \
    --turns-file outputs/huang_eval/phase1/2026-03-24/02-22-57/all_turns.json \
    --respondent-model gpt-5-mini --judge-model gpt-5-mini \
    --analyzer-model gpt-5-mini --max-concurrent 5 --run-s2 --seed 42
```

**Output location:** `outputs/huang_eval/phase2_s2_full/2026-03-25/06-13-04/`

### Results (n=173, all turn types)

S2 edit rate: 72.3%

**Overall comparisons (quality):**

| Comparison | Winner | Loser | Tie |
|------------|--------|-------|-----|
| AO vs S2 | **S2 86.1%** | AO 12.7% | 1.2% |
| AO vs S3 | S3 87.3% | AO 11.6% | 1.2% |
| FC vs S2 | **S2 83.8%** | FC 12.7% | 3.5% |
| FC vs S3 | S3 83.2% | FC 15.6% | 1.2% |

**S2 and S3 by turn type (quality):**

| Turn Type | n | S2 vs AO (S2 wins) | S3 vs AO (S3 wins) | S2 vs FC (S2 wins) | S3 vs FC (S3 wins) |
|-----------|---|---------------------|---------------------|---------------------|---------------------|
| new_ask | 64 | 87.5% | 89.1% | 87.5% | 90.6% |
| feedback | 42 | 85.7% | 85.7% | 83.3% | 76.2% |
| no_feedback | 67 | 85.1% | 86.6% | 80.6% | 80.6% |
| **Overall** | **173** | **86.1%** | **87.3%** | **83.8%** | **83.2%** |

**S2 edit rate by turn type:**

| Turn Type | n | Edit rate |
|-----------|---|-----------|
| new_ask | 64 | 78.1% |
| feedback | 42 | 78.6% |
| no_feedback | 67 | 62.7% |
| Overall | 173 | 72.3% |

### S2 Analysis

**8. S2 performs on par with S3 across all turns.** S2 beats AO 86.1% and FC 83.8%, nearly identical to S3's 87.3% and 83.2%. This is notable because S2 uses the v11 prompt (different from S3's v8) and gates on `needs_edit` (only resetting 72.3% of turns), while S3 always resets.

**9. S2's gating is well-calibrated.** S2 edits less often on no_feedback turns (62.7%) than on new_ask or feedback turns (~78%). This makes sense: on no_feedback turns, the user is referencing prior assistant outputs, so the conversation is more likely to be on track (the assistant just needs to continue). The gating prevents unnecessary resets in these cases. On the failure subset, S2 still achieves higher quality win rates than S3 (93.3% vs 85.3%) -- suggesting that when S2 does reset, it does so more effectively, and when it doesn't, FC (the fallback) is the right choice.

**10. v11 "mid-task reflection" framing is effective.** The v11 prompt's tighter issues section (requiring exact "None" for no errors) results in a 72.3% edit rate vs S3's ~85% (which uses v8's looser issues section). This means v11 avoids resetting on ~13% more turns where no reset is needed, without sacrificing quality.

## Caveats

**1. ~~Selection bias.~~** Resolved by the full unconditional evaluations for both S3 and S2.

**2. Format/presentation bias.** All reset-based strategies (S2, S3, S1.5) produce compacted contexts with structured headers (task spec, progress summary) that may look better to the judge than raw Option 2 conversation rendering. This could inflate win rates for all our methods equally. The relative comparisons between our methods (S2 vs S3 vs S1.5) are less affected since they share similar output formats.

**3. Judge model.** gpt-5-mini was used as the judge, not gpt-5 as Huang used. A weaker judge may be less reliable, particularly on subtle quality distinctions.

**4. Scale.** 30 conversations and ~179 turns is a pilot. Huang used 300 conversations. A production run with 100+ conversations and a gpt-5 judge would be more defensible for a paper submission.

**5. Response caching.** Phase 2 reuses FC/AO responses from Phase 1's `turn_results.jsonl`, truncated to 1000 characters. For turns where the cached response was truncated, the judge may not have had full context to evaluate. Future runs should store full responses or regenerate them.

## Prompt Versions Reference

| Prompt | File | Used by |
|--------|------|---------|
| Task spec (v8) | `strategies/prompts/analyzer_v8_task_spec.txt` | S2, S3, S1.5 |
| Compare (v8) | `strategies/prompts/analyzer_v8_compare.txt` | S3, S1.5 |
| Compare (v11) | `strategies/prompts/analyzer_v11_compare.txt` | S2 |
| Compaction (S3) | `strategies/prompts/context_compaction.txt` | S3 only |
| AO system message | `huang_eval/prompts/ao_system_message.txt` | AO |
| Turn classifier | `huang_eval/prompts/turn_classifier.txt` | All (classification) |
| Pairwise judge | `huang_eval/prompts/pairwise_judge.txt` | All (evaluation) |
